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
    message: str


class ExtractKeysResponse(BaseModel):
    """Response model for key extraction."""
    status: str
    key_categories: Dict[str, Any]
    message: str


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation."""
    status: str
    questions: Dict[str, Any]
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


