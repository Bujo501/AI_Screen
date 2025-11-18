# app/api/tts.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.tts_service import generate_tts_audio  # if you have service

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])

class TTSRequest(BaseModel):
    text: str

@router.post("/speak")
async def tts_speak(request: TTSRequest):
    audio_bytes = generate_tts_audio(request.text)
    return {"message": "TTS generated", "size": len(audio_bytes)}
