"""
FastAPI Resume Parser Application
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import (
    API_V1_PREFIX,
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    CORS_ORIGINS
)
from app.api.routes import api_router

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Resume Parser API",
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "parse_resume": f"{API_V1_PREFIX}/resume/parse",
            "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
            "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
            "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": APP_TITLE}
