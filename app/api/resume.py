# filepath: AI_Screen/app/api/resume.py
# (YOUR file, kept intact; only additions & hardening)
"""
Resume parsing API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import os, json
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from app.services.resume_service import ResumeService
from app.core.database import get_connection
from app.schemas.resume import (
    ExtractKeysRequest,
    GenerateQuestionsRequest,
    ParseResumeResponse,
    ExtractKeysResponse,
    GenerateQuestionsResponse,
    FullPipelineResponse,
    # ✅ added for new endpoints
    ParsedResume,
    ResumeRecord,
)

router = APIRouter(tags=["Resume"])
resume_service = ResumeService()

UPLOAD_DIR = "C:/Users/moham/OneDrive/Desktop/Ai resume/Backend M/New folder/AI_Backend/AI_Screen/app/uploads"

# ---------- helpers (added; safe) ----------
def _iso(dt_val) -> str:
    try:
        if isinstance(dt_val, datetime):
            return dt_val.replace(microsecond=0).isoformat() + "Z"
        return str(dt_val)
    except Exception:
        return str(dt_val or "")

def _as_list(x) -> List[str]:
    if not x:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if str(i).strip()]
    if isinstance(x, str):
        try:
            j = json.loads(x)
            if isinstance(j, list):
                return [str(i) for i in j if str(i).strip()]
        except Exception:
            return [s.strip() for s in x.split(",") if s.strip()]
    return []

def _edu_to_level(edu) -> int:
    # simple ordinal mapping for matching
    if isinstance(edu, int):
        return edu
    if isinstance(edu, str):
        e = edu.lower()
        if "phd" in e or "doctor" in e: return 5
        if "master" in e or "ms" in e:  return 4
        if "bachelor" in e or "btech" in e or "b.e" in e: return 3
        if "associate" in e: return 2
        if "high" in e: return 1
    if isinstance(edu, list) and edu:
        return _edu_to_level(edu[0])
    return 0

def _json_dump_safe(obj) -> str:
    """WHY: MySQL JSON column needs valid JSON. Try best-effort conversion."""
    try:
        return json.dumps(obj)
    except TypeError:
        return json.dumps(str(obj) if obj is not None else "")

def _sp_or_upsert_parsed_resume(cur, resume_id: str, payload: Dict[str, Any]) -> None:
    """
    WHY: Prefer stored procedure; if it fails/missing, do a direct upsert.
    payload keys expected: name, email, skills_json, education_json, projects_json, internships_json, text_len
    """
    try:
        cur.callproc("InsertOrUpdateParsedResume", [
            resume_id,
            payload.get("name"),
            payload.get("email"),
            payload.get("github"),
            payload.get("linkedin"),
            payload.get("skills_json"),
            payload.get("education_json"),
            payload.get("projects_json"),
            payload.get("internships_json"),
            payload.get("text_len", 0),
        ])
        return
    except Exception:
        # Fallback: direct upsert into parsed_resumes
        cur.execute(
            """
            INSERT INTO parsed_resumes (
                resume_id, full_name, email_id, github_portfolio, linkedin_id,
                skills, education, key_projects, internships, parsed_text_length
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                email_id = VALUES(email_id),
                github_portfolio = VALUES(github_portfolio),
                linkedin_id = VALUES(linkedin_id),
                skills = VALUES(skills),
                education = VALUES(education),
                key_projects = VALUES(key_projects),
                internships = VALUES(internships),
                parsed_text_length = VALUES(parsed_text_length),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                resume_id,
                payload.get("name"),
                payload.get("email"),
                payload.get("github"),
                payload.get("linkedin"),
                payload.get("skills_json"),
                payload.get("education_json"),
                payload.get("projects_json"),
                payload.get("internships_json"),
                payload.get("text_len", 0),
            ),
        )

# ---------- existing endpoints (unchanged) ----------
@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_id = str(uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO resumes (id, file_name, file_path) VALUES (%s, %s, %s)",
            (file_id, file.filename, file_path)
        )
        conn.commit(); cursor.close(); conn.close()
        return {"message": "Resume uploaded successfully", "file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/all", response_model=Dict[str, Any])
async def get_all_resumes():
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_name, file_path, uploaded_at
            FROM resumes
            ORDER BY uploaded_at DESC
        """)
        rows = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_count = cursor.fetchone()[0]
        cursor.close(); conn.close()
        resumes = [{
            "id": str(row[0]),
            "file_name": row[1],
            "file_path": row[2],
            "uploaded_at": _iso(row[3])
        } for row in rows]
        return {"total_resumes": total_count, "resumes": resumes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resumes: {str(e)}")

@router.post("/parse/{file_id}", response_model=ParseResumeResponse)
async def parse_resume(file_id: str):
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cursor = conn.cursor()
        # NOTE: You used testing1.resumes here originally; keeping as-is to avoid breaking.
        cursor.execute("SELECT file_name, file_path FROM testing1.resumes WHERE id = %s", (file_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close(); conn.close()
            raise HTTPException(status_code=404, detail="File not found")
        file_name, file_path = result

        parsed_data = await resume_service.parse_resume(file_path, file_name)
        extracted = parsed_data.get("extracted_data", {}) or {}

        # Build payloads safely
        skills_json = _json_dump_safe(extracted.get("skills") or [])
        education_json = _json_dump_safe(extracted.get("education") or [])
        projects_json = _json_dump_safe(extracted.get("key_projects") or [])
        internships_json = _json_dump_safe(extracted.get("internships") or [])
        text_len = int(parsed_data.get("resume_text_length", 0) or 0)

        _sp_or_upsert_parsed_resume(cursor, file_id, {
            "name": extracted.get("full_name"),
            "email": extracted.get("email_id"),
            "github": extracted.get("github_portfolio"),
            "linkedin": extracted.get("linkedin_id"),
            "skills_json": skills_json,
            "education_json": education_json,
            "projects_json": projects_json,
            "internships_json": internships_json,
            "text_len": text_len,
        })

        conn.commit(); cursor.close(); conn.close()

        return {
            "status": parsed_data.get("status", "success"),
            "filename": file_name,
            "resume_text_length": text_len,
            "extracted_data": extracted,
            "message": "Resume parsed and saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.post("/extract-keys/{file_id}", response_model=ExtractKeysResponse)
async def extract_keys(file_id: str):
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT resume_id, full_name, email_id, github_portfolio, linkedin_id,
                   skills, education, key_projects, internships, parsed_text_length
            FROM parsed_resumes WHERE resume_id = %s
        """, (file_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close(); conn.close()
            raise HTTPException(status_code=404, detail="Parsed resume not found")

        for field in ["skills","education","key_projects","internships"]:
            if row.get(field):
                try: row[field] = json.loads(row[field])
                except (TypeError, json.JSONDecodeError): pass

        cursor.close(); conn.close()
        return resume_service.extract_keys(row, file_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting keys: {str(e)}")

@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    try:
        return resume_service.generate_questions(request.key_categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@router.post("/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline(file: UploadFile = File(...)):
    try:
        return await resume_service.full_pipeline(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in pipeline: {str(e)}")

# ---------- ✅ NEW / hardened: endpoints your Dashboard needs ----------
@router.get("/resumes", response_model=List[ResumeRecord])
async def list_parsed_resumes(
    limit: int = Query(200, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Filter by name/email substring"),
) -> List[ResumeRecord]:
    """Join uploads with parsed_resumes and return normalized candidates."""
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cur = conn.cursor()

        # basic join; LIMIT sanitized by driver when passed as %s for mysql-connector
        base_sql = """
            SELECT r.id, r.uploaded_at,
                   COALESCE(p.full_name, '')        AS full_name,
                   COALESCE(p.email_id, '')         AS email_id,
                   COALESCE(p.skills, '[]')          AS skills_json,
                   COALESCE(p.education, '[]')       AS edu_json,
                   COALESCE(p.key_projects, '[]')    AS proj_json,
                   COALESCE(p.internships, '[]')     AS intern_json,
                   COALESCE(p.parsed_text_length, 0) AS text_len
            FROM resumes r
            LEFT JOIN parsed_resumes p ON p.resume_id = r.id
        """
        params: List[Any] = []
        if search:
            base_sql += " WHERE (p.full_name LIKE %s OR p.email_id LIKE %s) "
            like = f"%{search}%"
            params.extend([like, like])
        base_sql += " ORDER BY r.uploaded_at DESC LIMIT %s"
        params.append(int(limit))

        cur.execute(base_sql, tuple(params))
        rows = cur.fetchall()
        cur.close(); conn.close()

        out: List[ResumeRecord] = []
        for row in rows:
            rid, uploaded_at, name, email, skills_json, edu_json, _, _, _ = row
            skills = _as_list(skills_json)
            try:
                edu_val = json.loads(edu_json) if isinstance(edu_json, str) else (edu_json or [])
            except Exception:
                edu_val = edu_json
            education_level = _edu_to_level(edu_val)
            out.append(ResumeRecord(
                id=str(rid),
                created_at=_iso(uploaded_at),
                updated_at=_iso(uploaded_at),
                name=name or None,
                email=email or None,
                phone=None,
                skills=skills,
                years_experience=0.0,
                education=education_level,
                raw_text=" ".join(skills),
            ))
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing resumes: {str(e)}")

@router.post("/resumes", response_model=ResumeRecord)
async def create_parsed_resume(resume: ParsedResume) -> ResumeRecord:
    """
    Save a parsed resume directly (useful after /full-pipeline).
    """
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cur = conn.cursor()

        rid = str(uuid4())
        now = datetime.utcnow()

        # ensure a row in resumes
        cur.execute(
            "INSERT INTO resumes (id, file_name, file_path) VALUES (%s, %s, %s)",
            (rid, resume.name or "candidate", "")
        )

        # prepare JSON fields safely
        skills_json = _json_dump_safe(resume.skills or [])
        education_json = _json_dump_safe(resume.education)
        projects_json = _json_dump_safe([])      # extend when available
        internships_json = _json_dump_safe([])   # extend when available
        text_len = len((resume.raw_text or "").encode("utf-8"))

        _sp_or_upsert_parsed_resume(cur, rid, {
            "name": resume.name,
            "email": resume.email,
            "github": None,
            "linkedin": None,
            "skills_json": skills_json,
            "education_json": education_json,
            "projects_json": projects_json,
            "internships_json": internships_json,
            "text_len": text_len,
        })

        conn.commit()
        cur.close(); conn.close()

        return ResumeRecord(
            id=rid,
            created_at=_iso(now),
            updated_at=_iso(now),
            name=resume.name,
            email=resume.email,
            phone=resume.phone,
            skills=resume.skills or [],
            years_experience=resume.years_experience or 0.0,
            education=int(resume.education or 0),
            raw_text=resume.raw_text or "",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating resume: {str(e)}")
