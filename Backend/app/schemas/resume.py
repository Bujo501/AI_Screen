"""
Pydantic schemas for resume parsing API
"""
from pydantic import BaseModel
from typing import Union, Dict, Any


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

# from pydantic import BaseModel
# from datetime import datetime

# class Resume(BaseModel):
#     id: str
#     file_name: str
#     file_path: str
#     uploaded_at: datetime

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
