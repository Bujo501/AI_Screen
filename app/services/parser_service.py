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
from resume_parser import (
    extract_text_from_pdf,
    extract_text_from_image,
    extract_text_from_file,
    ats_extractor,
    key_extraction,
    topicwise_questions
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


