# ============================
# backend/hrmatching/models.py
# ============================
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column, String

class HRCompany(SQLModel, table=True):
    __tablename__ = "hr_company"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    roles: List["HRRole"] = Relationship(back_populates="company")

class HRRole(SQLModel, table=True):
    __tablename__ = "hr_role"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="hr_company.id", index=True)
    title: str = Field(index=True)
    min_years: int = Field(default=0, ge=0)
    max_years: int = Field(default=50, ge=0)
    description: Optional[str] = None

    company: HRCompany = Relationship(back_populates="roles")
    role_skills: List["HRRoleSkill"] = Relationship(back_populates="role")

class HRSkill(SQLModel, table=True):
    __tablename__ = "hr_skill"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True), index=True)

class HRRoleSkill(SQLModel, table=True):
    __tablename__ = "hr_role_skill"
    id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="hr_role.id", index=True)
    skill_id: int = Field(foreign_key="hr_skill.id", index=True)
    weight: int = Field(default=3, ge=1, le=5)
    must_have: bool = Field(default=False)

    role: HRRole = Relationship(back_populates="role_skills")
    skill: HRSkill = Relationship()

class HRCandidate(SQLModel, table=True):
    __tablename__ = "hr_candidate"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    resume_text: Optional[str] = None
    skills_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    scores: List["HRCandidateScore"] = Relationship(back_populates="candidate")

class HRCandidateScore(SQLModel, table=True):
    __tablename__ = "hr_candidate_score"
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="hr_candidate.id", index=True)
    role_id: int = Field(foreign_key="hr_role.id", index=True)
    score: int = Field(ge=0, le=100)
    details_json: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    candidate: HRCandidate = Relationship(back_populates="scores")
    role: HRRole = Relationship()
