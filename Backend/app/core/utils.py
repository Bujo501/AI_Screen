"""
Utility functions
"""
import json
import re
from typing import Dict, Union


def parse_json_response(response_str: str) -> dict:
    """
    Parse JSON from Groq response string.
    Handles cases where response might have extra text or markdown code blocks.
    
    Args:
        response_str: JSON string response from Groq API
        
    Returns:
        Parsed JSON as dictionary
    """
    try:
        # Remove markdown code blocks if present
        response_str = re.sub(r'```json\s*', '', response_str)
        response_str = re.sub(r'```\s*', '', response_str)
        response_str = response_str.strip()
        
        # Try to find JSON object in the string
        # Look for first { and last }
        start = response_str.find('{')
        end = response_str.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = response_str[start:end]
            return json.loads(json_str)
        else:
            # If no JSON found, try parsing the whole string
            return json.loads(response_str)
    except json.JSONDecodeError as e:
        # If parsing fails, return the original string wrapped in an object
        return {"raw_response": response_str, "parse_error": str(e)}


def convert_to_string(data: Union[str, dict]) -> str:
    """
    Convert data to JSON string if it's a dict, otherwise return as is.
    
    Args:
        data: String or dictionary to convert
        
    Returns:
        JSON string representation
    """
    if isinstance(data, dict):
        return json.dumps(data)
    return data


