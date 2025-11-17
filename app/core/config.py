"""
Application configuration
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Parser directory path
PARSER_DIR = BASE_DIR / "Parser"
CONFIG_PATH = PARSER_DIR / "config.yaml"

# API Configuration
API_V1_PREFIX = "/api/v1"
APP_TITLE = "Resume Parser API"
APP_DESCRIPTION = "API for parsing PDF resumes using Groq AI and generating interview questions."
APP_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS = ["*"]  # In production, specify actual origins


