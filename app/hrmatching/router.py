
# ============================
# backend/hrmatching/router.py
# ============================
from __future__ import annotations
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, Session
from .database import get_session, init_db
from .models import (
    HRCompany, HRRole, HRSkill, HRRoleSkill,
    HRCandidate, HRCandidateScore
)
from .schemas import (
    CompanyIn, CompanyOut, RoleIn, RoleOut, SkillIn,
    CandidateIn, CandidateOut, ScoreItem
)
from .scoring import extract_skills, extract_years, score_candidate_against_role, normalize

router = APIRouter(prefix="/matching", tags=["matching"])

@router.on_event("startup")
def _startup():
    init_db()

# ----- Company / Role Admin -----
@router.post("/companies", response_model=CompanyOut)
def create_company(data: CompanyIn, session: Session = Depends(get_session)):
    company = HRCompany(name=data.name, description=data.description)
    session.add(company); session.commit(); session.refresh(company)
    return CompanyOut(id=company.id, name=company.name, description=company.description)

@router.post("/companies/{company_id}/roles", response_model=RoleOut)
def create_role(company_id: int, data: RoleIn, session: Session = Depends(get_session)):
    if not session.get(HRCompany, company_id):
        raise HTTPException(404, "Company not found")
    role = HRRole(company_id=company_id, title=data.title, min_years=data.min_years,
                  max_years=data.max_years, description=data.description)
    session.add(role); session.commit(); session.refresh(role)
    return RoleOut(id=role.id, company_id=company_id, title=role.title,
                   min_years=role.min_years, max_years=role.max_years,
                   description=role.description, skills=[])

@router.post("/roles/{role_id}/requirements", response_model=RoleOut)
def set_role_requirements(role_id: int, skills: List[SkillIn], session: Session = Depends(get_session)):
    role = session.get(HRRole, role_id)
    if not role:
        raise HTTPException(404, "Role not found")

    for rs in list(role.role_skills):
        session.delete(rs)
    session.flush()

    for sk in skills:
        name = normalize(sk.name)
        skill = session.exec(select(HRSkill).where(HRSkill.name == name)).first()
        if not skill:
            skill = HRSkill(name=name)
            session.add(skill); session.flush()
        session.add(HRRoleSkill(role_id=role_id, skill_id=skill.id, weight=sk.weight, must_have=sk.must_have))
    session.commit(); session.refresh(role)

    out_skills = [SkillIn(name=rs.skill.name, weight=rs.weight, must_have=rs.must_have) for rs in role.role_skills]
    return RoleOut(id=role.id, company_id=role.company_id, title=role.title,
                   min_years=role.min_years, max_years=role.max_years,
                   description=role.description, skills=out_skills)

@router.get("/companies/{company_id}/roles", response_model=List[RoleOut])
def list_roles(company_id: int, session: Session = Depends(get_session)):
    roles = session.exec(select(HRRole).where(HRRole.company_id == company_id)).all()
    out: List[RoleOut] = []
    for r in roles:
        skills = [SkillIn(name=rs.skill.name, weight=rs.weight, must_have=rs.must_have) for rs in r.role_skills]
        out.append(RoleOut(id=r.id, company_id=r.company_id, title=r.title,
                           min_years=r.min_years, max_years=r.max_years,
                           description=r.description, skills=skills))
    return out

# ----- Candidates -----
@router.post("/candidates", response_model=CandidateOut)
def create_candidate(data: CandidateIn, session: Session = Depends(get_session)):
    resume_text = (data.resume_text or "").strip()
    skills = set([s.lower() for s in (data.skills or [])]) or set(extract_skills(resume_text))
    years = data.years_of_experience if data.years_of_experience is not None else extract_years(resume_text)
    c = HRCandidate(
        name=data.name, email=data.email, phone=data.phone,
        current_title=data.current_title, years_of_experience=years,
        resume_text=resume_text or None, skills_json={"skills": sorted(skills)},
    )
    session.add(c); session.commit(); session.refresh(c)
    return CandidateOut(
        id=c.id, name=c.name, email=c.email, phone=c.phone,
        current_title=c.current_title, years_of_experience=c.years_of_experience,
        skills=list(c.skills_json.get("skills", [])), resume_text=c.resume_text
    )

@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, session: Session = Depends(get_session)):
    c = session.get(HRCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return CandidateOut(
        id=c.id, name=c.name, email=c.email, phone=c.phone,
        current_title=c.current_title, years_of_experience=c.years_of_experience,
        skills=list((c.skills_json or {}).get("skills", [])), resume_text=c.resume_text
    )

@router.post("/candidates/{candidate_id}/score", response_model=List[ScoreItem])
def score_candidate(candidate_id: int, company_id: int, session: Session = Depends(get_session)):
    c = session.get(HRCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    company = session.get(HRCompany, company_id)
    if not company:
        raise HTTPException(404, "Company not found")

    candidate_skills = set([s.lower() for s in (c.skills_json or {}).get("skills", [])])
    roles = session.exec(select(HRRole).where(HRRole.company_id == company_id)).all()
    results: List[ScoreItem] = []

    for r in roles:
        job_skills = [(rs.skill.name, rs.weight, rs.must_have) for rs in r.role_skills]
        percent, details = score_candidate_against_role(
            candidate_skills=candidate_skills,
            candidate_years=c.years_of_experience,
            candidate_title=c.current_title,
            role_title=r.title,
            job_skills=job_skills,
            min_years=r.min_years, max_years=r.max_years,
        )

        cs = HRCandidateScore(candidate_id=c.id, role_id=r.id, score=percent, details_json=details)
        session.add(cs); session.commit()

        results.append(ScoreItem(
            role_id=r.id, role_title=r.title, score=percent,
            top_matches=details["matched_skills"],
            missing_must_haves=details["missing_must_haves"],
            missing_nice_to_haves=details["missing_nice_to_haves"],
            components={
                "skills": details["skill_score"],
                "experience": details["experience_score"],
                "title": details["title_score"],
            },
        ))
    # sort high → low for dashboard “top matches”
    results.sort(key=lambda x: x.score, reverse=True)
    return results

# ----- Leaderboards -----
@router.get("/roles/{role_id}/top-candidates", response_model=List[CandidateOut])
def top_candidates(role_id: int, limit: int = 50, session: Session = Depends(get_session)):
    scores = session.exec(
        select(HRCandidateScore).where(HRCandidateScore.role_id == role_id).order_by(HRCandidateScore.score.desc())
    ).all()[:limit]
    out: List[CandidateOut] = []
    for sc in scores:
        c = sc.candidate
        out.append(CandidateOut(
            id=c.id, name=c.name, email=c.email, phone=c.phone,
            current_title=c.current_title, years_of_experience=c.years_of_experience,
            skills=list((c.skills_json or {}).get("skills", [])), resume_text=c.resume_text
        ))
    return out

@router.get("/roles/{role_id}/candidates-by-experience", response_model=List[CandidateOut])
def candidates_by_experience(role_id: int, order: str = Query("desc", pattern="^(asc|desc)$"), session: Session = Depends(get_session)):
    # why: decouple from matches to let recruiter view pure experience ordering
    cand_ids = [s.candidate_id for s in session.exec(select(HRCandidateScore).where(HRCandidateScore.role_id == role_id)).all()]
    q = select(HRCandidate).where(HRCandidate.id.in_(cand_ids))
    if order == "asc":
        q = q.order_by(HRCandidate.years_of_experience)
    else:
        q = q.order_by(HRCandidate.years_of_experience.desc())
    cs = session.exec(q).all()
    out: List[CandidateOut] = []
    for c in cs:
        out.append(CandidateOut(
            id=c.id, name=c.name, email=c.email, phone=c.phone,
            current_title=c.current_title, years_of_experience=c.years_of_experience,
            skills=list((c.skills_json or {}).get("skills", [])), resume_text=c.resume_text
        ))
    return out