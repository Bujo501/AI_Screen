# =========================================
# filepath: AI_Screen/app/api/routes.py
# =========================================
"""
Main API routes aggregator
"""
from fastapi import APIRouter

# import router objects
from app.api.resume import router as resume_router   # resume router has no prefix
from app.api.jobs import router as jobs_router       # has prefix="/jobs"
from app.api.match import router as match_router     # has prefix="/match"

api_router = APIRouter()

# Final paths mounted under /api/v1/...
api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
# IMPORTANT: don't add an extra prefix here; routers already have one
api_router.include_router(jobs_router,   tags=["jobs"])
api_router.include_router(match_router,  tags=["match"])
