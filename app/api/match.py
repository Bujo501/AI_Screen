# =========================================
# filepath: AI_Screen/app/api/match.py
# =========================================
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from app.core.database import get_connection
from ..schemas.match import (
    MatchRequest, BatchMatchRequest, MatchResponse, MatchBreakdown
)
from ..core.match import (
    skill_score, experience_score, education_score, keywords_score, overall_score
)

router = APIRouter(prefix="/match", tags=["match"])

# ---------- JSON jobs fallback ----------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

def _load_jobs() -> List[Dict[str, Any]]:
    if not JOBS_FILE.exists():
        return []
    try:
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

# ---------- DB roles loader (SAFE) ----------
def _load_db_roles() -> List[Dict[str, Any]]:
    """
    Pull JobRequirements from MySQL hr_* tables.
    IMPORTANT: Returns [] on any error (missing tables, etc.) so the API never 500s.
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        if not conn:
            return []
        cur = conn.cursor(dictionary=True)

        # If tables don't exist yet, this SELECT will raise – we catch and return []
        cur.execute("""
            SELECT id, title, min_years_experience, required_education, description
            FROM hr_role
            ORDER BY updated_at DESC
        """)
        roles = cur.fetchall()

        out: List[Dict[str, Any]] = []
        for r in roles:
            # fetch skills for the role
            cur.execute("""
                SELECT s.name, rs.must_have
                FROM hr_role_skill rs
                JOIN hr_skill s ON s.id = rs.skill_id
                WHERE rs.role_id = %s
            """, (r["id"],))
            must, nice = [], []
            for name, must_have in cur.fetchall():
                (must if must_have else nice).append(name)

            out.append({
                "id": str(r["id"]),
                "title": r.get("title", ""),
                "description": r.get("description") or "",
                "min_years_experience": int(r.get("min_years_experience") or 0),
                "required_education": int(r.get("required_education") or 0),
                "must_have_skills": must,
                "nice_to_have_skills": nice,
            })
        return out
    except Exception:
        return []
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass

def _find_job_any(job_id: str) -> Dict[str, Any]:
    """
    Best-effort job lookup:
      1) Try numeric id in hr_role (+ skills) from DB
      2) Fallback to jobs.json 'id' string match
    """
    # Try as integer for DB roles
    iid: Optional[int] = None
    try:
        iid = int(job_id)
    except Exception:
        iid = None

    if iid is not None:
        conn = None
        cur = None
        try:
            conn = get_connection()
            if conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("""
                    SELECT id, title, min_years_experience, required_education, description
                    FROM hr_role WHERE id = %s
                """, (iid,))
                r = cur.fetchone()
                if r:
                    cur.execute("""
                        SELECT s.name, rs.must_have
                        FROM hr_role_skill rs
                        JOIN hr_skill s ON s.id = rs.skill_id
                        WHERE rs.role_id = %s
                    """, (iid,))
                    must, nice = [], []
                    for name, must_have in cur.fetchall():
                        (must if must_have else nice).append(name)
                    return {
                        "id": str(r["id"]),
                        "title": r.get("title", ""),
                        "description": r.get("description") or "",
                        "min_years_experience": int(r.get("min_years_experience") or 0),
                        "required_education": int(r.get("required_education") or 0),
                        "must_have_skills": must,
                        "nice_to_have_skills": nice,
                    }
        except Exception:
            pass
        finally:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except Exception:
                pass

    # Fallback to JSON
    for j in _load_jobs():
        if j.get("id") == job_id:
            return j
    raise HTTPException(404, "Job not found")

# ---------- Your existing scoring endpoints ----------
@router.post("/score", response_model=MatchResponse)
def score(req: MatchRequest):
    w = req.weights
    s_score, must_hit, nice_hit = skill_score(
        req.resume.skills, req.job.must_have_skills, req.job.nice_to_have_skills
    )
    e_score = experience_score(req.resume.years_experience, req.job.min_years_experience)
    d_score = education_score(int(req.resume.education), int(req.job.required_education))
    k_source = f"{req.job.title}\n{req.job.description}\n{' '.join(req.job.must_have_skills + req.job.nice_to_have_skills)}"
    k_score = keywords_score(req.resume.raw_text or "", k_source)

    final = overall_score(w, s_score, e_score, d_score, k_score)
    return MatchResponse(
        score=final,
        breakdown=MatchBreakdown(
            skills=round(s_score * 100, 1),
            experience=round(e_score * 100, 1),
            education=round(d_score * 100, 1),
            keywords=round(k_score * 100, 1),
        ),
        details={
            "matched_must_have": float(must_hit),
            "matched_nice_to_have": float(nice_hit),
        },
    )

@router.post("/score/batch")
def score_batch(req: BatchMatchRequest):
    return [
        score(type("X", (), {"resume": r, "job": req.job, "weights": req.weights}))
        for r in req.resumes
    ]

# ---------- NEW: role-wise scoring for one resume ----------
class ResumeIn(BaseModel):
    skills: List[str] = []
    years_experience: float | int = 0
    education: int = 0
    raw_text: Optional[str] = None

class WeightsIn(BaseModel):
    skills: Optional[float] = None
    experience: Optional[float] = None
    education: Optional[float] = None
    keywords: Optional[float] = None

class RoleMatchItem(BaseModel):
    job_id: str
    title: str
    score: float
    breakdown: MatchBreakdown
    details: Dict[str, float]

class ScoreAgainstAllJobsRequest(BaseModel):
    resume: ResumeIn
    weights: Optional[WeightsIn] = None

@router.post("/score/roles", response_model=List[RoleMatchItem])
def score_against_all_jobs(req: ScoreAgainstAllJobsRequest):
    """
    Score one resume against ALL roles.
    Loads from hr_* tables when available; otherwise falls back to data/jobs.json
    """
    jobs = _load_db_roles() or _load_jobs()
    if not jobs:
        return []

    out: List[RoleMatchItem] = []
    for j in jobs:
        s_score, must_hit, nice_hit = skill_score(
            req.resume.skills,
            j.get("must_have_skills", []),
            j.get("nice_to_have_skills", []),
        )
        e_score = experience_score(
            req.resume.years_experience, j.get("min_years_experience", 0)
        )
        d_score = education_score(
            int(req.resume.education), int(j.get("required_education", 0))
        )
        k_source = (
            f"{j.get('title','')}\n"
            f"{j.get('description','')}\n"
            f"{' '.join(j.get('must_have_skills', []) + j.get('nice_to_have_skills', []))}"
        )
        k_score = keywords_score(req.resume.raw_text or "", k_source)

        final = overall_score(req.weights, s_score, e_score, d_score, k_score)
        out.append(
            RoleMatchItem(
                job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                score=final,
                breakdown=MatchBreakdown(
                    skills=round(s_score * 100, 1),
                    experience=round(e_score * 100, 1),
                    education=round(d_score * 100, 1),
                    keywords=round(k_score * 100, 1),
                ),
                details={
                    "matched_must_have": float(must_hit),
                    "matched_nice_to_have": float(nice_hit),
                },
            )
        )

    out.sort(key=lambda x: x.score, reverse=True)
    return out

# ---------- NEW: leaderboard for ONE role ----------
class CandidateWithScoreOut(BaseModel):
    index: int
    score: float
    years_experience: Optional[float | int] = None
    breakdown: MatchBreakdown

@router.post("/score/role/{job_id}/batch", response_model=List[CandidateWithScoreOut])
def score_batch_for_role(
    job_id: str,
    req: BatchMatchRequest,
    sort: str = Query("score", pattern="^(score|experience)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    job = _find_job_any(job_id)

    rows: List[CandidateWithScoreOut] = []
    for i, r in enumerate(req.resumes):
        s_score, _, _ = skill_score(
            r.skills, job.get("must_have_skills", []), job.get("nice_to_have_skills", [])
        )
        e_score = experience_score(
            r.years_experience, job.get("min_years_experience", 0)
        )
        d_score = education_score(
            int(r.education), int(job.get("required_education", 0))
        )
        k_source = (
            f"{job.get('title','')}\n"
            f"{job.get('description','')}\n"
            f"{' '.join(job.get('must_have_skills', []) + job.get('nice_to_have_skills', []))}"
        )
        k_score = keywords_score(r.raw_text or "", k_source)

        final = overall_score(req.weights, s_score, e_score, d_score, k_score)
        rows.append(
            CandidateWithScoreOut(
                index=i,
                score=final,
                years_experience=r.years_experience,
                breakdown=MatchBreakdown(
                    skills=round(s_score * 100, 1),
                    experience=round(e_score * 100, 1),
                    education=round(d_score * 100, 1),
                    keywords=round(k_score * 100, 1),
                ),
            )
        )

    reverse = (order == "desc")
    if sort == "experience":
        rows.sort(key=lambda x: (x.years_experience or 0), reverse=reverse)
    else:
        rows.sort(key=lambda x: x.score, reverse=reverse)

    return rows
