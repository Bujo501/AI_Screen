from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection
from app.services.gmail_service import GmailService

router = APIRouter(tags=["Interview Email"])

class InterviewDetails(BaseModel):
    interview_date: str
    interview_time: str
    interview_link: str


@router.post("/send-interview-mail/{resume_id}")
async def send_interview_mail(resume_id: str, data: InterviewDetails):

    # Fetch candidate details from DB
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT full_name, email_id
        FROM parsed_resumes
        WHERE resume_id = %s
    """, (resume_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(404, "Candidate not found")

    candidate_name = row["full_name"]
    candidate_email = row["email_id"]

    # Email body
    body = f"""
Dear {candidate_name},

You have been shortlisted for an interview at S2Integrators.

Date: {data.interview_date}
Time: {data.interview_time}

Join using this link:
{data.interview_link}

Regards,
S2Integrators HR Team
"""

    # Send email
    try:
        gmail = GmailService()
        gmail.send_email(
            to_email=candidate_email,
            subject="Interview Scheduled – S2Integrators",
            message_text=body  
        )
    except Exception as e:
        raise HTTPException(500, f"Error sending email: {str(e)}")

    return {"message": "Interview email sent successfully", "email_sent_to": candidate_email}
