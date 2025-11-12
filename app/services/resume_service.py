"""
Business logic service for resume processing
"""
import os
import re
import json
import shutil
import tempfile
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import UploadFile, HTTPException

from app.services.parser_service import ParserService
from app.core.utils import parse_json_response, convert_to_string
from app.core.database import get_connection


def safe_json_extract(text):
    """Extract valid JSON object/array from possibly messy LLM output.

    Returns parsed Python object (dict or list) or raises ValueError.
    """
    if isinstance(text, (dict, list)):
        return text

    if text is None or (isinstance(text, str) and not text.strip()):
        raise ValueError("Empty or invalid response received from model")

    cleaned = str(text).strip()
    # Remove common triple-backtick fences and language tags
    cleaned = cleaned.replace("```json", "").replace("```", "")
    # Try to find a JSON object or array in the text
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if not match:
        # As a last resort try to parse the whole cleaned string
        try:
            return json.loads(cleaned)
        except Exception:
            raise ValueError("No valid JSON object or array found in model response.")
    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Helpful debug info
        raise ValueError(f"Failed to parse JSON from model response: {e}")


class ResumeService:
    """Service for resume processing operations."""

    def __init__(self):
        self.parser_service = ParserService()

    async def parse_resume(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Parse a saved resume file (PDF or image) from disk.

        Args:
            file_path: Absolute or relative path to the resume file.
            file_name: Original filename (for responses)

        Returns:
            Dictionary with parsed resume data.

        Raises:
            HTTPException: If file not found, unsupported type, or parsing fails.
        """
        # Validate file existence
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
        tmp_file_path = None

        try:
            # Copy to a temp file for processing (some libs expect a regular file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file_path = tmp_file.name
            shutil.copy2(file_path, tmp_file_path)

            # Extract text (PDF or image) using ParserService
            if not hasattr(self.parser_service, "extract_text"):
                raise RuntimeError("ParserService.extract_text not implemented")

            resume_text = self.parser_service.extract_text(tmp_file_path)
            if not resume_text or not str(resume_text).strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the file")

            # Extract structured data using parser_service; handle both dict and string responses
            if not hasattr(self.parser_service, "extract_resume_data"):
                raise RuntimeError("ParserService.extract_resume_data not implemented")

            extracted_info_raw = self.parser_service.extract_resume_data(resume_text)
            try:
                extracted_info = safe_json_extract(extracted_info_raw)
            except ValueError:
                # Fallback to parse_json_response if provided (maintain existing util)
                extracted_info = parse_json_response(extracted_info_raw)

            return {
                "status": "success",
                "filename": file_name,
                "resume_text_length": len(resume_text),
                "extracted_data": extracted_info,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
        finally:
            try:
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except Exception:
                pass

    def extract_keys(self, extracted_data: dict, resume_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract key categories (AI-based) from parsed resume data and optionally save to DB.

        Args:
            extracted_data: Parsed resume data (dict or JSON string)
            resume_id: Optional resume ID to update in DB. If not provided, DB update is skipped.

        Returns:
            dict with status and extracted key categories.
        """
        try:
            # Normalize input to string for the LLM
            if isinstance(extracted_data, (dict, list)):
                input_data = json.dumps(extracted_data, indent=2)
            else:
                input_data = str(extracted_data)

            if not hasattr(self.parser_service, "extract_key_categories"):
                raise RuntimeError("ParserService.extract_key_categories not implemented")

            key_data_raw = self.parser_service.extract_key_categories(input_data)

            # ✅ Handle both dict and string cases safely
            if isinstance(key_data_raw, (dict, list)):
                key_data = key_data_raw
            else:
                # Clean LLM response if it's a string
                cleaned = re.sub(r"<think>.*?</think>", "", key_data_raw, flags=re.DOTALL)
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

                # Extract only JSON portion (ignore text outside braces)
                match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
                if match:
                    cleaned_json = match.group(0)
                    key_data = json.loads(cleaned_json)
                else:
                    key_data = parse_json_response(cleaned)

            # ✅ Optionally save into DB
            if resume_id:
                conn = get_connection()
                if conn is None:
                    raise HTTPException(status_code=500, detail="Database connection not available")

                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        UPDATE parsed_resumes
                        SET extracted_keys = %s,
                            parsed_at = NOW()
                        WHERE resume_id = %s
                    """, (json.dumps(key_data, ensure_ascii=False, indent=2), resume_id))
                    conn.commit()
                finally:
                    cursor.close()
                    conn.close()

            # ✅ Return clean JSON response
            return {
                "status": "success",
                "key_categories": key_data,
                "message": "Key categories extracted" + (" and saved to DB" if resume_id else "")
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting and saving key categories: {str(e)}")

    def generate_questions(self, file_id: str) -> Dict[str, Any]:
        """
        Generate interview questions based on extracted key categories stored in DB.
        
        Args:
            file_id: Resume ID (UUID) referencing parsed_resumes table.

        Returns:
            Dict[str, Any]: Clean, structured JSON of generated interview questions.
        """
        try:
            # ✅ Connect to database and fetch extracted_keys
            conn = get_connection()
            if conn is None:
                raise HTTPException(status_code=500, detail="Database connection not available")

            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT extracted_keys 
                FROM parsed_resumes 
                WHERE resume_id = %s
            """, (file_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row or not row.get("extracted_keys"):
                raise HTTPException(status_code=404, detail="No extracted key categories found for this file")

            key_categories = row["extracted_keys"]

            # ✅ If fetched as string, parse it
            if isinstance(key_categories, str):
                try:
                    key_categories = json.loads(key_categories)
                except json.JSONDecodeError:
                    key_categories = parse_json_response(key_categories)

            # ✅ Prepare input for LLM
            inp = json.dumps(key_categories, indent=2)

            if not hasattr(self, "parser_service") or not hasattr(self.parser_service, "generate_questions"):
                raise RuntimeError("ParserService.generate_questions not available")

            result = self.parser_service.generate_questions(inp)

            # ✅ If LLM returned dict, return directly
            if isinstance(result, (dict, list)):
                parsed = result
            else:
                cleaned = re.sub(r"<think>.*?</think>", "", str(result), flags=re.DOTALL)
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

                match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    parsed = parse_json_response(cleaned)

            # ✅ Return structured JSON
            return {
                "status": "success",
                "questions": parsed,
                "message": "Interview questions generated successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

    
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
        # Validate extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
            )

        suffix = file_ext if file_ext == '.pdf' else '.jpg'
        tmp_file_path = None
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file_path = tmp_file.name
                content = await file.read()
                tmp_file.write(content)

            # Step 1: parse resume
            parsed = await self.parse_resume(tmp_file_path, file.filename)

            # Step 2: extract keys (do not save to DB during full pipeline)
            extracted_data = parsed.get("extracted_data")
            keys_result = self.extract_keys(extracted_data, resume_id=None)

            # Step 3: generate questions
            key_categories = keys_result.get("key_categories")
            questions_parsed = generate_questions(self, key_categories)

            # Return shape matches response model that expects 'message' and 'pipeline_results'
            return {
                "status": "success",
                "filename": parsed.get("filename"),
                "message": "Pipeline completed successfully",
                "pipeline_results": {
                    "resume_text_length": parsed.get("resume_text_length"),
                    "extracted_data": parsed.get("extracted_data"),
                    "key_categories": keys_result.get("key_categories"),
                    "interview_questions": questions_parsed
                }
            }


        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in pipeline: {str(e)}")
        finally:
            try:
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except Exception:
                pass


