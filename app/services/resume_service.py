"""
Business logic service for resume processing
"""
import os
import tempfile
from typing import Dict, Any
from fastapi import UploadFile, HTTPException

from app.services.parser_service import ParserService
from app.core.utils import parse_json_response, convert_to_string


class ResumeService:
    """Service for resume processing operations."""
    
    def __init__(self):
        self.parser_service = ParserService()
    
    async def parse_resume(self, file: UploadFile) -> Dict[str, Any]:
        """
        Parse uploaded PDF or image resume.
        
        Args:
            file: Uploaded PDF or image file
            
        Returns:
            Dictionary with parsed resume data
            
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
            # Extract text from PDF or image
            resume_text = self.parser_service.extract_text(tmp_file_path)
            
            if not resume_text:
                raise HTTPException(status_code=400, detail="No text could be extracted from the file")
            
            # Extract structured data using Groq
            extracted_info_str = self.parser_service.extract_resume_data(resume_text)
            extracted_info = parse_json_response(extracted_info_str)
            
            return {
                "status": "success",
                "filename": file.filename,
                "resume_text_length": len(resume_text),
                "extracted_data": extracted_info,
                "message": "Resume parsed successfully"
            }
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def extract_keys(self, extracted_data: str | dict) -> Dict[str, Any]:
        """
        Extract key categories from parsed resume data.
        
        Args:
            extracted_data: JSON string or dict from parse_resume
            
        Returns:
            Dictionary with key categories
        """
        # Convert to string if needed
        input_data = convert_to_string(extracted_data)
        
        # Extract keys
        key_data_str = self.parser_service.extract_key_categories(input_data)
        key_data = parse_json_response(key_data_str)
        
        return {
            "status": "success",
            "key_categories": key_data,
            "message": "Key categories extracted successfully"
        }
    
    def generate_questions(self, key_categories: str | dict) -> Dict[str, Any]:
        """
        Generate interview questions based on key categories.
        
        Args:
            key_categories: JSON string or dict from extract_keys
            
        Returns:
            Dictionary with interview questions
        """
        # Convert to string if needed
        input_data = convert_to_string(key_categories)
        
        # Generate questions
        questions_str = self.parser_service.generate_questions(input_data)
        questions = parse_json_response(questions_str)
        
        return {
            "status": "success",
            "questions": questions,
            "message": "Interview questions generated successfully"
        }
    
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


