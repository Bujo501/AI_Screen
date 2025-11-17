"""
Job description API routes
"""
from fastapi import APIRouter, HTTPException
from app.services.job_service import JobService
from app.schemas.resume import JobDescriptionCreate
from typing import Dict, Any

router = APIRouter(tags=["Jobs"])
job_service = JobService()


@router.post("/add", response_model=Dict[str, Any])
async def add_job_description(request: JobDescriptionCreate):
    """
    Add a new job description to the database.
    """
    return job_service.add_job_description(request.title, request.description)


@router.get("/all", response_model=Dict[str, Any])
async def get_all_jobs():
    """
    Fetch all job descriptions stored in the database.
    """
    return job_service.get_all_jobs()


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_by_id(job_id: str):
    """
    Fetch a specific job by its ID.
    """
    return job_service.get_job_by_id(job_id)


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_job(job_id: str):
    """
    Delete a job by its ID.
    """
    return job_service.delete_job(job_id)
