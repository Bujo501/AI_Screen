"""
Business logic service for resume processing
"""
import os,json
import tempfile
from typing import Dict, Any
from fastapi import UploadFile, HTTPException

from app.services.parser_service import ParserService
from app.core.utils import parse_json_response, convert_to_string
import re
from app.core.database import get_connection


@staticmethod
def safe_json_extract(text):
    """Extract valid JSON object from possibly messy LLM output."""
    if isinstance(text, dict):
        # Already parsed JSON
        return text

    if not text or not str(text).strip():
        raise ValueError("Empty or invalid response received from model")

    cleaned = str(text).strip().replace("```json", "").replace("```", "")
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("No valid JSON object found in model response.")

    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ JSON Decode Error:", e)
        print("🧾 Raw JSON Segment:", json_str)
        raise ValueError("Failed to parse JSON from LLM response.")
    

def generate_questions(self, key_categories) -> str:
        """
        Generate interview questions based on the key values (skills) provided.
        Absolutely safe for Groq API – always sends plain strings.
        """
        try:
            # 1️⃣ Always stringify the input early
            try:
                key_categories_str = json.dumps(key_categories, indent=2)
            except Exception:
                key_categories_str = str(key_categories)

            # 2️⃣ Build a very simple text prompt
            prompt_text = (
                "You are an AI interviewer.\n"
                "Generate exactly 10 interview questions directly based on these skills.\n"
                "Return valid JSON ONLY in this format:\n"
                "{\n"
                '  "questions": [\n'
                '    {"skill": "<skill name>", "type": "<conceptual|technical|scenario>", '
                '"difficulty": "<easy|medium|hard>", "question": "<text>"}\n'
                "  ]\n"
                "}\n\n"
                f"Skills input:\n{key_categories_str}"
            )

            # 3️⃣ Final guarantee: cast prompt to string
            prompt_text = str(prompt_text)

            # 4️⃣ Call Groq safely
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system",
                     "content": "You generate skill-based interview questions and respond only with valid JSON."},
                    {"role": "user", "content": prompt_text},
                ],
                temperature=0.4,
                max_tokens=2000,
            )

            # 5️⃣ Extract message text safely
            content = response.choices[0].message.content
            return str(content)

        except Exception as e:
            raise Exception(f"Error generating questions: {e}")

class ResumeService:
    """Service for resume processing operations."""
    
    def __init__(self):
        self.parser_service = ParserService()
    
    # async def parse_resume(self, file: UploadFile) -> Dict[str, Any]:
    #     """
    #     Parse uploaded PDF or image resume.
        
    #     Args:
    #         file: Uploaded PDF or image file
            
    #     Returns:
    #         Dictionary with parsed resume data
            
    #     Raises:
    #         HTTPException: If file is not supported or processing fails
    #     """
    #     # Get file extension
    #     file_ext = os.path.splitext(file.filename)[1].lower()
    #     supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
    #     if file_ext not in supported_extensions:
    #         raise HTTPException(
    #             status_code=400, 
    #             detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
    #         )
        
    #     # Determine suffix based on file type
    #     suffix = file_ext if file_ext == '.pdf' else '.jpg'
        
    #     # Save uploaded file temporarily
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
    #         content = await file.read()
    #         tmp_file.write(content)
    #         tmp_file_path = tmp_file.name
        
    #     try:
    #         # Extract text from PDF or image
    #         resume_text = self.parser_service.extract_text(tmp_file_path)
            
    #         if not resume_text:
    #             raise HTTPException(status_code=400, detail="No text could be extracted from the file")
            
    #         # Extract structured data using Groq
    #         extracted_info_str = self.parser_service.extract_resume_data(resume_text)
    #         extracted_info = parse_json_response(extracted_info_str)
            
    #         return {
    #             "status": "success",
    #             "filename": file.filename,
    #             "resume_text_length": len(resume_text),
    #             "extracted_data": extracted_info,
    #             "message": "Resume parsed successfully"
    #         }
    #     finally:
    #         # Clean up temp file
    #         if os.path.exists(tmp_file_path):
    #             os.unlink(tmp_file_path)


    async def parse_resume(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Parse a saved resume file (PDF or image) from disk.

        Args:
            file_path: Absolute or relative path to the resume file.

        Returns:
            Dictionary with parsed resume data.

        Raises:
            HTTPException: If file not found, unsupported type, or parsing fails.
        """
        # 🔹 Validate file existence
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()
        supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
            )

        suffix = file_ext if file_ext == '.pdf' else '.jpg'

        try:
            # 🔹 Copy file to a temporary location for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                with open(file_path, "rb") as src:
                    tmp_file.write(src.read())
                tmp_file_path = tmp_file.name

            # 🔹 Extract text (PDF or image)
            resume_text = self.parser_service.extract_text(tmp_file_path)
            if not resume_text:
                raise HTTPException(status_code=400, detail="No text could be extracted from the file")

            # 🔹 Extract structured data using Groq (LLM)
            extracted_info_str = self.parser_service.extract_resume_data(resume_text)
            extracted_info = parse_json_response(extracted_info_str)

            return {
                "status": "success",
                "filename": file_name,
                "resume_text_length": len(resume_text),
                "extracted_data": extracted_info,
                # "message": "Resume parsed successfully"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

        finally:
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

        
    # def extract_keys(self, extracted_data: dict, resume_id: str) -> Dict[str, Any]:
    #     """
    #     Extract key categories (AI-based) from parsed resume data and save to DB.

    #     Args:
    #         extracted_data: Parsed resume data from DB
    #         resume_id: Resume ID to update

    #     Returns:
    #         dict: {
    #             "status": "success",
    #             "key_categories": {...},
    #             "message": "Key categories extracted and saved successfully"
    #         }
    #     """
    #     import json
    #     from fastapi import HTTPException

    #     try:
    #         # 1️⃣ Convert to JSON string
    #         input_data = json.dumps(extracted_data, indent=2)

    #         # 2️⃣ Call LLM through parser_service
    #         key_data_str = self.parser_service.extract_key_categories(input_data)

    #         # 3️⃣ Parse JSON safely
    #         try:
    #             key_data = json.loads(key_data_str)
    #         except json.JSONDecodeError:
    #             cleaned = key_data_str.replace("```json", "").replace("```", "").strip()
    #             key_data = json.loads(cleaned)

    #         # # 4️⃣ Save into parsed_resumes.extracted_keys
    #         # conn = get_connection()
    #         # cursor = conn.cursor()
    #         # cursor.execute("""
    #         #     UPDATE parsed_resumes
    #         #     SET extracted_keys = %s,
    #         #         parsed_at = NOW()
    #         #     WHERE resume_id = %s
    #         # """, (json.dumps(key_data), resume_id))

    #         # conn.commit()
    #         # cursor.close()
    #         # conn.close()

    #         # 5️⃣ Return the structured response
    #         return {
    #             "status": "success",
    #             "key_categories": key_data,
    #             "message": "Key categories extracted and saved successfully"
    #         }

    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Error extracting and saving key categories: {str(e)}")



    def extract_keys(self, extracted_data: dict, resume_id: str):
        """Extract key categories (AI-based) from parsed resume data and save to DB."""
        try:
            # 1️⃣ Convert parsed resume dict to a JSON string for the LLM
            input_data = json.dumps(extracted_data, indent=2)

            # 2️⃣ Call your LLM-based extractor
            key_data_str = self.parser_service.extract_key_categories(input_data)
            # print("🔍 Raw key_data_str:", key_data_str[:500])

            # 3️⃣ Cleanly extract JSON only
            key_data = safe_json_extract(key_data_str)
            print("✅ Extracted key_data dict:", key_data)

            # 4️⃣ Convert to string for DB save (only if it's still a dict)
            if isinstance(key_data, (dict, list)):
                key_data_str = json.dumps(key_data)
            else:
                key_data_str = str(key_data)

            # # 5️⃣ Save to DB
            # conn = get_connection()
            # cursor = conn.cursor()
            # cursor.execute("""
            #     UPDATE parsed_resumes
            #     SET parsed_at = NOW()
            #     WHERE resume_id = %s
            # """, (key_data_str, resume_id))
            # conn.commit()
            # cursor.close()
            # conn.close

            # 6️⃣ Return success

            return {
                "status": "success",
                "key_categories": key_data,
                "message": "Key categories extracted and saved successfully"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting and saving key categories: {str(e)}")

    
    async def full_pipeline(self, file: UploadFile) -> Dict[str, Any]:
        """
        Complete pipeline: Parse → Extract Keys → Generate Questions.
        
        Args:
            file: Uploaded PDF or image file
            
        Returns:
            Dictionary with all pipeline results
            
        Raises:
            HTTPException: If file is not supported or processing fails
        """
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
            )
        
        # Determine suffix based on file type
        suffix = file_ext if file_ext == '.pdf' else '.jpg'
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Extract text from PDF or image
            resume_text = self.parser_service.extract_text(tmp_file_path)
            
            if not resume_text:
                raise HTTPException(status_code=400, detail="No text could be extracted from the file")
            
            # Step 2: Extract structured data
            extracted_info_str = self.parser_service.extract_resume_data(resume_text)
            extracted_info = parse_json_response(extracted_info_str)
            
            # Step 3: Extract key categories
            key_categories_str = self.parser_service.extract_key_categories(extracted_info_str)
            key_categories = parse_json_response(key_categories_str)
            
            # Step 4: Generate questions
            questions_str = self.parser_service.generate_questions(key_categories_str)
            questions = parse_json_response(questions_str)
            
            return {
                "status": "success",
                "filename": file.filename,
                "pipeline_results": {
                    "resume_text_length": len(resume_text),
                    "extracted_data": extracted_info,
                    "key_categories": key_categories,
                    "interview_questions": questions
                },
                "message": "Full pipeline completed successfully"
            }
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)


