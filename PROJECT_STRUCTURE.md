# Project Structure

## Overview
The FastAPI application has been refactored into a clean, modular structure following best practices.

## Directory Structure

```
app/
├── main.py                 # FastAPI app initialization and configuration
├── core/                   # Core utilities and configuration
│   ├── __init__.py
│   ├── config.py          # Application configuration (paths, constants)
│   └── utils.py           # Utility functions (JSON parsing, conversions)
├── schemas/                # Pydantic models for request/response validation
│   ├── __init__.py
│   └── resume.py          # Resume-related schemas
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── parser_service.py  # Wrapper for Parser/resume_parser.py functions
│   └── resume_service.py  # Resume processing business logic
└── api/                    # API routes
    ├── __init__.py
    ├── routes.py          # Main router aggregator
    └── resume.py          # Resume API endpoints
```

## File Responsibilities

### `app/main.py`
- FastAPI application initialization
- CORS middleware configuration
- Route registration
- Root and health check endpoints

### `app/core/config.py`
- Application constants (API prefix, title, version)
- Path configurations (Parser directory, config file)
- CORS settings

### `app/core/utils.py`
- `parse_json_response()` - Parses JSON from Groq API responses
- `convert_to_string()` - Converts dict to JSON string

### `app/schemas/resume.py`
- Pydantic models for request/response validation:
  - `ExtractKeysRequest`
  - `GenerateQuestionsRequest`
  - `ParseResumeResponse`
  - `ExtractKeysResponse`
  - `GenerateQuestionsResponse`
  - `FullPipelineResponse`
  - `PipelineResults`

### `app/services/parser_service.py`
- Wrapper service for `Parser/resume_parser.py` functions
- Methods:
  - `extract_text()` - Extract text from PDF
  - `extract_resume_data()` - Extract structured data using Groq
  - `extract_key_categories()` - Extract key categories
  - `generate_questions()` - Generate interview questions

### `app/services/resume_service.py`
- Business logic for resume processing
- Methods:
  - `parse_resume()` - Parse uploaded PDF
  - `extract_keys()` - Extract key categories
  - `generate_questions()` - Generate questions
  - `full_pipeline()` - Complete workflow

### `app/api/routes.py`
- Aggregates all API route modules
- Includes resume router with prefix

### `app/api/resume.py`
- Resume API endpoints:
  - `POST /api/v1/resume/parse`
  - `POST /api/v1/resume/extract-keys`
  - `POST /api/v1/resume/generate-questions`
  - `POST /api/v1/resume/full-pipeline`

## Benefits of This Structure

1. **Separation of Concerns**: Each layer has a clear responsibility
2. **Maintainability**: Easy to find and modify specific functionality
3. **Testability**: Services can be tested independently
4. **Scalability**: Easy to add new features and endpoints
5. **Reusability**: Services can be reused across different endpoints
6. **Type Safety**: Pydantic schemas provide validation and documentation

## API Endpoints

All endpoints are prefixed with `/api/v1`:

- `POST /api/v1/resume/parse` - Parse PDF resume
- `POST /api/v1/resume/extract-keys` - Extract key categories
- `POST /api/v1/resume/generate-questions` - Generate questions
- `POST /api/v1/resume/full-pipeline` - Complete pipeline

## Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc





