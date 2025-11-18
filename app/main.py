# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.core.config import API_V1_PREFIX, APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS
# from app.api.routes import api_router

# app = FastAPI(
#     title=APP_TITLE,
#     description=APP_DESCRIPTION,
#     version=APP_VERSION,
#     docs_url="/docs",
#     redoc_url="/redoc",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ single mount (routes.py already includes resume/jobs/match)
# app.include_router(api_router, prefix=API_V1_PREFIX)

# @app.get("/")
# async def root():
#     return {
#         "message": "Resume Parser API",
#         "version": APP_VERSION,
#         "docs": "/docs",
#         "endpoints": {
#             "parse_resume": f"{API_V1_PREFIX}/resume/parse",
#             "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
#             "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
#             "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline",
#         },
#     }

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": APP_TITLE}
# File: AI_Screen/app/main.py
# """
# FastAPI Resume Parser Application
# Main application entry point
# """
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.core.config import (
#     API_V1_PREFIX,
#     APP_TITLE,
#     APP_DESCRIPTION,
#     APP_VERSION,
#     CORS_ORIGINS,
# )

# from app.api.routes import api_router

# # ✅ Existing imports
# from app.api.jobs import router as jobs_router
# from app.api.match import router as match_router

# # ✅ Optional feature imports (guarded)
# tts_router = None
# interview_router = None
# try:
#     from app.api.tts import router as _tts_router  # noqa
#     tts_router = _tts_router
# except Exception:
#     # WHY: Avoid startup crash if feature not present
#     tts_router = None

# try:
#     from app.api.interview import router as _interview_router  # noqa
#     interview_router = _interview_router
# except Exception:
#     interview_router = None


# # ---------------------------------------------------------
# # Create FastAPI app
# # ---------------------------------------------------------
# app = FastAPI(
#     title=APP_TITLE,
#     description=APP_DESCRIPTION,
#     version=APP_VERSION,
#     docs_url="/docs",
#     redoc_url="/redoc",
# )


# # ---------------------------------------------------------
# # CORS Middleware
# # ---------------------------------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CORS_ORIGINS + [
#         "http://localhost:5173",
#         "http://127.0.0.1:5173",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ---------------------------------------------------------
# # Include API Routers
# # ---------------------------------------------------------
# # Grouped v1 router
# app.include_router(api_router, prefix=API_V1_PREFIX)

# # Jobs + Match routers (v1)
# app.include_router(jobs_router, prefix=API_V1_PREFIX)
# app.include_router(match_router, prefix=API_V1_PREFIX)

# # New feature routers (mount only if present)
# if tts_router is not None:
#     app.include_router(tts_router)
# if interview_router is not None:
#     app.include_router(interview_router)


# # ---------------------------------------------------------
# # Root Endpoints
# # ---------------------------------------------------------
# @app.get("/")
# async def root():
#     return {
#         "message": "Resume Parser API",
#         "version": APP_VERSION,
#         "docs": "/docs",
#         "endpoints": {
#             "parse_resume": f"{API_V1_PREFIX}/resume/parse",
#             "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
#             "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
#             "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline",
#         },
#     }


# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": APP_TITLE}

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
    CORS_ORIGINS,
)

from app.api.routes import api_router

# ✅ Existing imports
from app.api.jobs import router as jobs_router
from app.api.match import router as match_router

# ✅ Optional feature imports (guarded)
tts_router = None
interview_router = None
# 🔶 ADD: hr router guard
hr_router = None

try:
    from app.api.tts import router as _tts_router  # noqa
    tts_router = _tts_router
except Exception:
    # WHY: Avoid startup crash if feature not present
    tts_router = None

try:
    from app.api.interview import router as _interview_router  # noqa
    interview_router = _interview_router
except Exception:
    interview_router = None

# 🔶 ADD: hr import guard
try:
    from app.api.hr import router as _hr_router  # noqa
    hr_router = _hr_router
except Exception:
    hr_router = None


# ---------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Include API Routers
# ---------------------------------------------------------
# Grouped v1 router
app.include_router(api_router, prefix=API_V1_PREFIX)

# Jobs + Match routers (v1)
app.include_router(jobs_router, prefix=API_V1_PREFIX)
app.include_router(match_router, prefix=API_V1_PREFIX)

# New feature routers (mount only if present)  ➜ mount UNDER /api/v1
if tts_router is not None:
    app.include_router(tts_router, prefix=API_V1_PREFIX)

if interview_router is not None:
    app.include_router(interview_router, prefix=API_V1_PREFIX)

# 🔶 ADD: mount HR router under /api/v1  ➜ fixes 404 on /api/v1/hr/roles
if hr_router is not None:
    app.include_router(hr_router, prefix=API_V1_PREFIX)


# ---------------------------------------------------------
# Root Endpoints
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Resume Parser API",
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "parse_resume": f"{API_V1_PREFIX}/resume/parse",
            "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
            "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
            "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": APP_TITLE}
