# Resume Parser API

FastAPI application that integrates with `Parser/resume_parser.py` to parse PDF resumes using Groq AI and generate interview questions.

## Features

- **Parse Resume**: Extract structured data from PDF resumes (name, email, github, linkedin, education, skills, projects, internships)
- **Extract Keys**: Extract key categories (technical skills, frameworks, projects, etc.)
- **Generate Questions**: Generate topic-wise interview questions
- **Full Pipeline**: Complete workflow in one endpoint

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create `Parser/config.yaml`:

```yaml
OPENAI_API_KEY: "your-groq-api-key-here"
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Parse Resume
**POST** `/api/v1/resume/parse`

Upload and parse a PDF resume.

**Request:**
- Form data with `file` (PDF)

**Response:**
```json
{
  "status": "success",
  "filename": "resume.pdf",
  "resume_text_length": 1234,
  "extracted_data": "{...JSON from Groq...}",
  "message": "Resume parsed successfully"
}
```

### 2. Extract Keys
**POST** `/api/v1/resume/extract-keys`

Extract key categories from parsed resume data.

**Request:**
```json
{
  "extracted_data": "{...JSON from parse_resume...}"
}
```

**Response:**
```json
{
  "status": "success",
  "key_categories": "{...JSON with technical_skills, frameworks, etc...}",
  "message": "Key categories extracted successfully"
}
```

### 3. Generate Questions
**POST** `/api/v1/resume/generate-questions`

Generate interview questions based on key categories.

**Request:**
```json
{
  "key_categories": "{...JSON from extract_keys...}"
}
```

**Response:**
```json
{
  "status": "success",
  "questions": "{...JSON with topic-wise questions...}",
  "message": "Interview questions generated successfully"
}
```

### 4. Full Pipeline
**POST** `/api/v1/resume/full-pipeline`

Complete workflow: Parse → Extract Keys → Generate Questions.

**Request:**
- Form data with `file` (PDF)

**Response:**
```json
{
  "status": "success",
  "filename": "resume.pdf",
  "pipeline_results": {
    "resume_text_length": 1234,
    "extracted_data": "{...}",
    "key_categories": "{...}",
    "interview_questions": "{...}"
  },
  "message": "Full pipeline completed successfully"
}
```

## Example Usage

### Using cURL

**Parse Resume:**
```bash
curl -X POST "http://localhost:8000/api/v1/resume/parse" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf"
```

**Full Pipeline:**
```bash
curl -X POST "http://localhost:8000/api/v1/resume/full-pipeline" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf"
```

### Using Python

```python
import requests

# Parse resume
with open("resume.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/resume/parse",
        files={"file": f}
    )
    print(response.json())
    
    # Extract keys
    extracted_data = response.json()["extracted_data"]
    keys_response = requests.post(
        "http://localhost:8000/api/v1/resume/extract-keys",
        json={"extracted_data": extracted_data}
    )
    print(keys_response.json())
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **PyPDF2**: PDF parsing
- **python-multipart**: File upload support
- **pydantic**: Data validation
- **groq**: Groq AI client
- **pyyaml**: YAML configuration

## Project Structure

```
ai_screen/
├── app/
│   ├── main.py                    # FastAPI application
│   └── __init__.py
├── Parser/
│   ├── resume_parser.py           # Original parser functions
│   └── config.yaml                # Groq API key configuration
├── requirements.txt
└── README.md
```





