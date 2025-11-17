# ---------- File: AI_Screen/app/schemas/match.py
from __future__ import annotations
from enum import IntEnum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class EducationLevel(IntEnum):
    none = 0
    highschool = 1
    associate = 2
    bachelor = 3
    master = 4
    phd = 5


class ParsedResume(BaseModel):
    """Minimal resume shape consumed by the matcher."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_experience: float = 0.0
    education: EducationLevel = EducationLevel.none
    raw_text: str = ""  # used for keyword similarity


class JobRequirements(BaseModel):
    id: Optional[str] = None
    title: str
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_years_experience: float = 0.0
    required_education: EducationLevel = EducationLevel.none
    description: str = ""


class Weights(BaseModel):
    skills: float = 0.5
    experience: float = 0.3
    education: float = 0.1
    keywords: float = 0.1

    def normalized(self) -> "Weights":
        total = max(1e-9, self.skills + self.experience + self.education + self.keywords)
        # Avoid division by zero; preserves proportions.
        return Weights(
            skills=self.skills / total,
            experience=self.experience / total,
            education=self.education / total,
            keywords=self.keywords / total,
        )


class MatchBreakdown(BaseModel):
    skills: float
    experience: float
    education: float
    keywords: float


class MatchResponse(BaseModel):
    score: float  # 0..100
    breakdown: MatchBreakdown
    details: Dict[str, float] = Field(default_factory=dict)


class MatchRequest(BaseModel):
    resume: ParsedResume
    job: JobRequirements
    weights: Optional[Weights] = None


class BatchMatchRequest(BaseModel):
    resumes: List[ParsedResume]
    job: JobRequirements
    weights: Optional[Weights] = None