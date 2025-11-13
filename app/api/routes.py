"""
Main API routes aggregator
"""
from fastapi import APIRouter
from app.api import resume, jobs

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(resume.router, prefix="/resume")
api_router.include_router(jobs.router, prefix="/job")
