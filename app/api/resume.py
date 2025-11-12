"""
Resume parsing API routes
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
import os,json
from typing import List, Dict, Any
from app.services.resume_service import ResumeService
from uuid import uuid4
from app.core.database import get_connection
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


# @router.post("/parse", response_model=ParseResumeResponse)
# async def parse_resume(file: UploadFile = File(...)):
#     """
#     Upload and parse a PDF or image resume.
#     Extracts: name, email, github, linkedin, education, skills, projects, internships.
    
#     - **file**: PDF or image file (JPG, PNG, etc.) containing the resume
#     """
#     try:
#         return await resume_service.parse_resume(file)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

UPLOAD_DIR = "D:/ai_screen/app/uploads"


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    # 1. Save file to disk
    file_id = str(uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 2. Insert metadata into database
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO resumes (id, file_name, file_path) VALUES (%s, %s, %s)",
            (file_id, file.filename, file_path)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # 3. Return success
        return {"message": "Resume uploaded successfully", "file_id": file_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/all", response_model=Dict[str, Any])
async def get_all_resumes():
    """
    Fetch all uploaded resumes and total count.
    """
    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")

        cursor = conn.cursor()

        # Fetch all resumes
        cursor.execute("""
            SELECT id, file_name, file_path, uploaded_at
            FROM resumes
            ORDER BY uploaded_at DESC
        """)
        rows = cursor.fetchall()

        # Fetch total count
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        resumes = [
            {
                "id": str(row[0]),
                "file_name": row[1],
                "file_path": row[2],
                "uploaded_at": row[3]
            }
            for row in rows
        ]

        return {
            "total_resumes": total_count,
            "resumes": resumes
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resumes: {str(e)}")

@router.post("/parse/{file_id}", response_model=ParseResumeResponse)
async def parse_resume(file_id: str):
    """
    Parse a previously uploaded resume using its file_id.
    - **file_id**: UUID of the uploaded file (returned by /upload)
    """
    try:
        # 1️⃣ Fetch file path from database
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")

        cursor = conn.cursor()
        cursor.execute("SELECT file_name, file_path FROM testing1.resumes WHERE id = %s", (file_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="File not found")

        file_name, file_path = result
        print("Parsing file:", file_name, file_path)

        # 2️⃣ Parse the file using your Parser service
        parsed_data = await resume_service.parse_resume(file_path, file_name)
        extracted = parsed_data.get("extracted_data", {})

        import json

        # 3️⃣ Call stored procedure to insert/update parsed data
        cursor.callproc("InsertOrUpdateParsedResume", [
            file_id,
            extracted.get("full_name"),
            extracted.get("email_id"),
            extracted.get("github_portfolio"),
            extracted.get("linkedin_id"),
            json.dumps(extracted.get("skills")),
            json.dumps(extracted.get("education")),
            json.dumps(extracted.get("key_projects")),
            json.dumps(extracted.get("internships")),
            parsed_data.get("resume_text_length", 0)
        ])

        conn.commit()  # ✅ Commit the transaction
        cursor.close()
        conn.close()

        # 4️⃣ Return structured response
        return {
            "status": parsed_data.get("status", "success"),
            "filename": file_name,
            "resume_text_length": parsed_data.get("resume_text_length", 0),
            "extracted_data": extracted,
            "message": "Resume parsed and saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")




@router.post("/extract-keys/{file_id}", response_model=ExtractKeysResponse)
async def extract_keys(file_id: str):
    """
    Extract key interview categories (technical_skills, frameworks_libraries, etc.)
    from the parsed resume stored in the database.
    """

    try:
        conn = get_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        cursor = conn.cursor(dictionary=True)

        # 1️⃣ Fetch parsed resume data
        cursor.execute("""
            SELECT 
                resume_id,
                full_name,
                email_id,
                github_portfolio,
                linkedin_id,
                skills,
                education,
                key_projects,
                internships,
                parsed_text_length
            FROM parsed_resumes
            WHERE resume_id = %s
        """, (file_id,))

        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Parsed resume not found")

        # 2️⃣ Convert JSON fields into Python objects
        json_fields = ["skills", "education", "key_projects", "internships"]
        for field in json_fields:
            if row.get(field):
                try:
                    row[field] = json.loads(row[field])
                except (TypeError, json.JSONDecodeError):
                    pass

        cursor.close()
        conn.close()
        print("Row:", row)

        # 3️⃣ Call resume service to extract AI-based key categories
        result = resume_service.extract_keys(row, file_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting keys: {str(e)}")



@router.post("/generate-questions/{file_id}", response_model=GenerateQuestionsResponse)
async def generate_questions(file_id: str):
    """
    Generate topic-wise interview questions based on stored key categories
    from the parsed_resumes table.
    """
    try:
        return resume_service.generate_questions(file_id=file_id)
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

