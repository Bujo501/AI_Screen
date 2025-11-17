# filepath: AI_Screen/app/schemas/resume.py
"""
Pydantic schemas for resume parsing API
"""
from pydantic import BaseModel
from typing import Union, Dict, Any, Optional, List


class ExtractKeysRequest(BaseModel):
    """Request model for key extraction."""
    extracted_data: Union[str, dict]  # JSON string or dict from ats_extractor


class GenerateQuestionsRequest(BaseModel):
    """Request model for question generation."""
    key_categories: Union[str, dict]  # JSON string or dict from key_extraction


class ParseResumeResponse(BaseModel):
    """Response model for resume parsing."""
    status: str
    filename: str
    resume_text_length: int
    extracted_data: Dict[str, Any]
    # message: str


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation."""
    status: str
    questions: Dict[str, Any]
    message: str


class ExtractKeysResponse(BaseModel):
    """Response model for key extraction."""
    status: str
    key_categories: Dict[str, Any]
    message: str


class PipelineResults(BaseModel):
    """Results from full pipeline."""
    resume_text_length: int
    extracted_data: Dict[str, Any]
    key_categories: Dict[str, Any]
    interview_questions: Dict[str, Any]


class FullPipelineResponse(BaseModel):
    """Response model for full pipeline."""
    status: str
    filename: str
    pipeline_results: PipelineResults
    message: str


# -----------------------------
# ✅ Added (non-breaking)
# Used by dashboard list/score
# -----------------------------

class ParsedResume(BaseModel):
    """Normalized resume slice consumed by matching UI/API."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    years_experience: float = 0.0
    education: int = 0  # 0-none, 3-bachelor, 4-master, 5-phd (simple ordinal)
    raw_text: str = ""   # for keyword similarity


class ResumeRecord(ParsedResume):
    """Stored resume with identifiers/timestamps."""
    id: str
    created_at: str  # ISO
    updated_at: str  # ISO
from datetime import datetime
from typing import List, Optional



class JobDescriptionCreate(BaseModel):
    """Request model for adding a job description."""
    title: str
    comapny_branch: Optional[str] = None
    description: str
    required_skills: Optional[Dict[str, Any]] = None

class JobDescriptionResponse(BaseModel):
    """Response model for a job description."""
    job_id: str
    title: str
    description: str
    required_skills: Optional[Dict[str, Any]] = None
    created_at: datetime


# ===========================
# ⚖️ RESUME–JOB COMPARISON SCHEMAS
# ===========================

class ComparisonResult(BaseModel):
    """AI comparison result structure."""
    match_percentage: int
    matching_skills: List[str]
    missing_skills: List[str]
    summary: str


class ResumeJobComparisonResponse(BaseModel):
    """Response model for /resume/compare endpoint."""
    status: str
    file_id: str
    job_id: str
    comparison_result: ComparisonResult


class ResumeJobComparisonDB(BaseModel):
    """Database record model for stored comparison results."""
    comparison_id: str
    resume_id: str
    job_id: str
    match_percentage: int
    matching_skills: List[str]
    missing_skills: List[str]
    summary: str
    compared_at: datetime
