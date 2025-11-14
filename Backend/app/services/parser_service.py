"""
Service for interacting with Parser/resume_parser.py functions
"""
import sys
import os
from pathlib import Path
from app.core.config import PARSER_DIR

# Add Parser directory to path
sys.path.insert(0, str(PARSER_DIR))

# Import parser functions
from Parser.resume_parser import (
    extract_text_from_pdf,
    extract_text_from_image,
    extract_text_from_file,
    ats_extractor,
    key_extraction,
    topicwise_questions,
    compare_resume_to_job
)


class ParserService:
    """Service wrapper for resume parser functions."""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from PDF or image file.
        Automatically detects file type and uses appropriate extraction method.
        
        Args:
            file_path: Path to PDF or image file
            
        Returns:
            Extracted text content
        """
        return extract_text_from_file(file_path)
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        return extract_text_from_pdf(pdf_path)
    
    @staticmethod
    def extract_text_from_image(image_path: str) -> str:
        """
        Extract text from image file using Google Vision API OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text content
        """
        return extract_text_from_image(image_path)
    
    @staticmethod
    def extract_resume_data(resume_text: str) -> str:
        """
        Extract structured data from resume text using Groq.
        
        Args:
            resume_text: Text content from resume
            
        Returns:
            JSON string with extracted resume data
        """
        return ats_extractor(resume_text)
    
    @staticmethod
    def extract_key_categories(extracted_data: str) -> str:
        """
        Extract key categories from parsed resume data.
        
        Args:
            extracted_data: JSON string from ats_extractor
            
        Returns:
            JSON string with key categories
        """
        return key_extraction(extracted_data)
    
    @staticmethod
    def generate_questions(key_categories: str) -> str:
        """
        Generate interview questions based on key categories.
        
        Args:
            key_categories: JSON string from key_extraction
            
        Returns:
            JSON string with interview questions
        """
        return topicwise_questions(key_categories)


    @staticmethod
    def compare_resume_to_job(job_description: str, resume_data: dict) -> dict:
        """
        Compare a resume's key categories against a job description using Groq AI.
        Returns match percentage, matching/missing skills, and a summary.
        """
        import json, re
        from groq import Groq

        # ✅ Load Groq API key (already set in resume_parser)
        from Parser.resume_parser import api_key  

        client = Groq(api_key=api_key)

        prompt = f"""
        You are an expert HR recruiter.
        Compare the following job description and resume data.

        Job Description:
        {job_description}

        Resume Data:
        {json.dumps(resume_data, indent=2)}

        Return valid JSON with this structure only:
        {{
          "match_percentage": <integer 0-100>,
          "matching_skills": ["skill1", "skill2", ...],
          "missing_skills": ["skillA", "skillB", ...],
          "summary": "Brief, professional summary of the match quality (2–3 lines)."
        }}
        """

        try:
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2,
                max_tokens=800
            )

            result = response.choices[0].message.content

            # ✅ Extract valid JSON only
            match = re.search(r"(\{[\s\S]*\})", result)
            if match:
                return json.loads(match.group(0))
            else:
                return {"error": "Could not parse AI response", "raw_output": result}

        except Exception as e:
            return {"error": f"AI comparison failed: {str(e)}"}
