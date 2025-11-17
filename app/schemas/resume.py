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
