
# ============================
# backend/hrmatching/schemas.py
# ============================
from __future__ import annotations
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class SkillIn(BaseModel):
    name: str
    weight: int = Field(ge=1, le=5, default=3)
    must_have: bool = False

class CompanyIn(BaseModel):
    name: str
    description: Optional[str] = None

class CompanyOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class RoleIn(BaseModel):
    title: str
    min_years: int = 0
    max_years: int = 50
    description: Optional[str] = None

class RoleOut(BaseModel):
    id: int
    company_id: int
    title: str
    min_years: int
    max_years: int
    description: Optional[str]
    skills: List[SkillIn] = []

class CandidateIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = None

class CandidateOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    current_title: Optional[str]
    years_of_experience: Optional[int]
    skills: List[str] = []
    resume_text: Optional[str]

class ScoreItem(BaseModel):
    role_id: int
    role_title: str
    score: int
    top_matches: List[str]
    missing_must_haves: List[str]
    missing_nice_to_haves: List[str]
    components: Dict[str, float]

