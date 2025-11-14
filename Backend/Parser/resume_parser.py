from groq import Groq
import yaml
from PyPDF2 import PdfReader
from google.cloud import vision
from google.api_core import exceptions as google_exceptions
import os
import io
from app.core.utils import parse_json_response, convert_to_string

api_key = None
google_vision_api_key = None
CONFIG_PATH = "D:/S2_REC/Backend/Parser/config.yaml"

with open(CONFIG_PATH) as file:
    data = yaml.load(file, Loader=yaml.FullLoader)
    api_key = data.get("GROQ_API_KEY") 
    google_vision_api_key = data.get("GOOGLE_VISION_API_KEY")


def extract_text_from_pdf(pdf_path):
    """Extracts and returns all text from a PDF file"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_image(image_path):
    """
    Extracts text from an image file using Google Vision API OCR.
    
    Args:
        image_path: Path to the image file (jpg, png, etc.)
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If API key is not configured
        Exception: If Vision API call fails
    """
    if not google_vision_api_key:
        raise ValueError("GOOGLE_VISION_API_KEY not found in config.yaml. Please set it to the path of your Google Cloud service account JSON file.")
    
    # Set the API key as environment variable for Google Cloud Vision
    # This should be the path to your service account JSON file
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_vision_api_key
    
    # Initialize the Vision API client
    client = vision.ImageAnnotatorClient()
    
    # Read the image file
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    # Create image object
    image = vision.Image(content=content)
    
    # Perform text detection
    try:
        response = client.text_detection(image=image)
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error and response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        texts = response.text_annotations
        
        if texts:
            # The first annotation contains the entire detected text
            extracted_text = texts[0].description
            return extracted_text.strip()
        else:
            return ""
    except google_exceptions.PermissionDenied as e:
        error_msg = str(e)
        if "BILLING_DISABLED" in error_msg or "billing" in error_msg.lower():
            raise Exception(
                "Google Vision API requires billing to be enabled on your Google Cloud project. "
                "Please enable billing at: https://console.cloud.google.com/billing "
                "or visit the link provided in the error details. "
                f"Original error: {error_msg}"
            )
        else:
            raise Exception(f"Google Vision API permission denied: {error_msg}")
    except google_exceptions.GoogleAPIError as e:
        error_msg = str(e)
        if "BILLING_DISABLED" in error_msg or "billing" in error_msg.lower():
            raise Exception(
                "Google Vision API requires billing to be enabled on your Google Cloud project. "
                "Please enable billing at: https://console.cloud.google.com/billing. "
                f"Original error: {error_msg}"
            )
        raise Exception(f"Google Vision API error: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        # Check if it's a billing-related error even if not caught by specific exception
        if "BILLING_DISABLED" in error_msg or ("billing" in error_msg.lower() and "403" in error_msg):
            raise Exception(
                "Google Vision API requires billing to be enabled on your Google Cloud project. "
                "Please enable billing at: https://console.cloud.google.com/billing. "
                f"Original error: {error_msg}"
            )
        raise


def extract_text_from_file(file_path):
    """
    Automatically detects file type and extracts text from PDF or image.
    
    Args:
        file_path: Path to the file (PDF or image)
        
    Returns:
        Extracted text as a string
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Supported: PDF, JPG, PNG, GIF, BMP, WEBP")


def ats_extractor(resume_data):
    prompt = '''
    You are an AI bot designed to act as a professional for parsing resumes. 
    You are given the resume and your job is to extract the following information:
    1. full name
    2. email id
    3. github portfolio
    4. linkedin id
    5. Education
    6. Skills
    7. Key Projects
    8. Internships
    Give the extracted information in JSON format.
    '''

    # ✅ Create Groq client
    client = Groq(api_key=api_key)

    # ✅ Construct messages
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": resume_data}
    ]

    # ✅ Use a valid Groq model (gpt-3.5-turbo is NOT supported on Groq)
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=messages,
        temperature=0.0,
        max_tokens=2500
    )

    # ✅ Typo fix: should be response.choices (plural)
    data = response.choices[0].message.content

    # print(data)
    return data


def key_extraction(key_categories):
    prompt = '''
            You are an AI assistant that prepares personalized technical interviews based on a candidate’s resume.

    Below is a JSON object containing a candidate’s extracted resume data.

    Your task:
    1. Carefully analyze all sections (skills, frameworks, projects, internships, etc.).
    2. Identify and group interview-relevant topics into clear categories.
    3. Avoid duplicates and keep each topic concise and specific (e.g., “Python”, “TensorFlow”, “REST APIs”).
    4. Return the output in clean JSON format with the following structure:

    {
      "technical_skills": ["Python", "Java", "TensorFlow", "React", "Node.js", ...],
      "frameworks_libraries": ["Flask", "Django", "PyTorch", ...],
      "projects_topics": ["Diabetic Health Analyzer", "AgroVisionary", ...],
      "conceptual_topics": ["Machine Learning", "Deep Learning", "Full Stack Development", ...],
      "databases_cloud": ["MySQL", "MongoDB", "Docker", "Render", ...],
      "roles_experience": ["Backend Development", "Full Stack Development", "Data Science"]
    }

    Important notes:
    - Do not repeat the same topic in multiple lists.
    - Only include items that are relevant for interview question generation.
    - Keep the final JSON clean, without extra text or commentary.
    '''

    client = Groq(api_key=api_key)

    messages = [
        {"role": "system", "content" : prompt },
        {"role" : "user", "content": key_categories}
    ]

    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=messages,
        temperature=0.0,
        max_tokens=2500
    )

    key_data = response.choices[0].message.content


    print("-------------------------------------------:",parse_json_response(key_data))
    return parse_json_response(key_data)

def topicwise_questions(key_words):
    prompt = '''
            You are an intelligent AI interviewer. Your goal is to generate technical interview questions based on a candidate’s resume topics.

    Input:
    A JSON object containing categorized topics extracted from the candidate’s resume.

    Task:
    1. For each topic or skill, generate 2–3 concise and relevant interview questions.
    2. The questions should test both conceptual understanding and practical application.
    3. Keep them simple, specific, and directly related to the topic.
    4. Return the output strictly in the following JSON format:

    {
      "Python": [
        "What are decorators in Python and where are they useful?",
        "How does memory management work in Python?"
      ],
      "TensorFlow": [
        "Explain how you used TensorFlow in your projects.",
        "What is the difference between static and dynamic computation graphs in TensorFlow?"
      ],
      "React": [
        "What are React hooks and why are they used?",
        "How does React handle component re-rendering?"
      ]
    }

    Guidelines:
    - Do NOT include any extra explanations or commentary outside the JSON.
    - If a topic is a project title, frame project-specific questions like:
      “What was your role in the [project name] project?” or “Which technologies did you use in this project?”
    - Keep questions diverse — include both technical and real-world problem-based questions.'''

    client = Groq(api_key=api_key)

    messages = [
        {"role":"system","content" : prompt},
        {"role": "user", "content" : key_words}
    ]

    response = client.chat.completions.create(
        model = "qwen/qwen3-32b",
        messages=messages,
        temperature=0.9,
        max_tokens=2500)
    
    questions_ontopic = response.choices[0].message.content

    print(questions_ontopic)
    return questions_ontopic

@staticmethod
def compare_resume_to_job(job_description: str, resume_data: dict) -> dict:
    """
    Compare resume content against a job description using Groq AI.
    Returns match percentage, matching and missing skills, and a summary.
    """
    from groq import Groq
    import re, json

    client = Groq(api_key=api_key)

    prompt = f"""
    You are an expert HR recruiter.
    Compare the following job description and resume data.

    Job Description:
    {job_description}

    Resume Data:
    {json.dumps(resume_data, indent=2)}

    Return JSON only in the following format:
    {{
        "match_percentage": <integer 0-100>,
        "matching_skills": ["skill1", "skill2", ...],
        "missing_skills": ["skillA", "skillB", ...],
        "summary": "Brief 2–3 line explanation of match quality."
    }}
    """

    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    result = response.choices[0].message.content

    # ✅ Extract valid JSON from AI output
    match = re.search(r"(\{[\s\S]*\})", result)
    try:
        parsed_result = json.loads(match.group(0)) if match else parse_json_response(result)
    except Exception:
        parsed_result = {"error": "Failed to parse AI response", "raw_output": result}

    return parsed_result



