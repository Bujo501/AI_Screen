from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection

# 🔧 Make sure the filename is exactly services/gmail_services.py
#     and the class inside is GmailService
try:
    from app.services.gmail_services import GmailService  # correct module name
except Exception as e:
    GmailService = None  # allow app to start; we’ll error clearly later
    _gmail_import_error = e

# ✅ IMPORTANT: no '/api' here; global '/api/v1' is added in main.py
router = APIRouter(prefix="/interview", tags=["Interview"])


class InterviewRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(req: InterviewRequest):
    return {"answer": f"You asked: {req.question}"}


class InterviewDetails(BaseModel):
    interview_date: str
    interview_time: str
    interview_link: str


@router.post("/send-interview-mail/{resume_id}")
async def send_interview_mail(resume_id: str, data: InterviewDetails):
    # --- fetch candidate
    conn = get_connection()
    if conn is None:
        raise HTTPException(500, "Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT full_name, email_id
            FROM parsed_resumes
            WHERE resume_id = %s
            """,
            (resume_id,),
        )
        row = cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        raise HTTPException(404, "Candidate not found")

    candidate_name = row["full_name"] or "Candidate"
    candidate_email = row["email_id"]
    if not candidate_email:
        raise HTTPException(400, "Candidate email not available")

    # --- build email
    body = f"""
Dear {candidate_name},

You have been shortlisted for an interview at S2Integrators.

Date: {data.interview_date}
Time: {data.interview_time}

Join using this link:
{data.interview_link}

Regards,
S2Integrators HR Team
""".strip()

    # --- send email
    if GmailService is None:
        # Give a clear actionable error if the module/class wasn’t importable
        raise HTTPException(
            500,
            f"Gmail service not available: {_gmail_import_error}"
            if '_gmail_import_error' in globals()
            else "Unknown Gmail import error",
        )

    try:
        gmail = GmailService()
        gmail.send_email(
            to_email=candidate_email,
            subject="Interview Scheduled – S2Integrators",
            message_text=body,
        )
    except Exception as e:
        # Don’t crash the whole app; return a helpful error
        raise HTTPException(500, f"Error sending email: {str(e)}")

    return {
        "message": "Interview email sent successfully",
        "email_sent_to": candidate_email,
    }
