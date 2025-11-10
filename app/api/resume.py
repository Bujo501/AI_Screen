"""
Resume parsing API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.resume_service import ResumeService
from app.schemas.resume import (
    ExtractKeysRequest,
    GenerateQuestionsRequest,
    ParseResumeResponse,
    ExtractKeysResponse,
    GenerateQuestionsResponse,
    FullPipelineResponse
)

router = APIRouter(tags=["Resume"])
resume_service = ResumeService()


@router.post("/parse", response_model=ParseResumeResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Upload and parse a PDF or image resume.
    Extracts: name, email, github, linkedin, education, skills, projects, internships.
    
    - **file**: PDF or image file (JPG, PNG, etc.) containing the resume
    """
    try:
        return await resume_service.parse_resume(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@router.post("/extract-keys", response_model=ExtractKeysResponse)
async def extract_keys(request: ExtractKeysRequest):
    """
    Extract key categories from parsed resume data.
    Returns: technical_skills, frameworks_libraries, projects_topics, etc.
    
    - **extracted_data**: JSON string or dict from the parse_resume endpoint
    """
    try:
        return resume_service.extract_keys(request.extracted_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting keys: {str(e)}")


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate topic-wise interview questions based on key categories.
    
    - **key_categories**: JSON string or dict from the extract_keys endpoint
    """
    try:
        return resume_service.generate_questions(request.key_categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline(file: UploadFile = File(...)):
    """
    Complete pipeline: Upload PDF/Image → Parse → Extract Keys → Generate Questions.
    Returns all results in one response.
    
    - **file**: PDF or image file (JPG, PNG, etc.) containing the resume
    """
    try:
        return await resume_service.full_pipeline(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in pipeline: {str(e)}")

