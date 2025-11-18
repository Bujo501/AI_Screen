
from io import BytesIO

def synthesize_wav(text: str) -> bytes:
    """
    Return WAV bytes for `text`.
    Why: single entry so the route stays engine-agnostic.
    Replace stub with your actual engine (e.g., pyttsx3, Azure, ElevenLabs).
    """
    text = (text or "").strip()
    if not text:
        return b""

    # --- Example offline engine (uncomment to use) ---
    # import pyttsx3, tempfile, os
    # engine = pyttsx3.init()
    # with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    #     path = tmp.name
    # engine.save_to_file(text, path)
    # engine.runAndWait()
    # data = open(path, "rb").read()
    # os.remove(path)
    # return data

    # Fallback: short silent WAV so endpoint remains testable.
    import wave, struct
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        frames = int(0.25 * 16000)
        for _ in range(frames):
            wf.writeframesraw(struct.pack("<h", 0))
    return buffer.getvalue()

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.tts_service import synthesize_wav

router = APIRouter(prefix="/api/v1/tts", tags=["tts"])

class SpeakIn(BaseModel):
    text: str

@router.post("/speak", response_class=StreamingResponse)
def speak(body: SpeakIn):
    """
    Stream WAV bytes for the given text.
    Why: correct content-type & low latency.
    """
    txt = (body.text or "").strip()
    if not txt:
        raise HTTPException(status_code=400, detail="Empty text")
    wav = synthesize_wav(txt)
    if not wav:
        raise HTTPException(status_code=500, detail="TTS failed")
    return StreamingResponse(iter([wav]), media_type="audio/wav")


def generate_tts_audio(text: str) -> bytes:
    """
    Simple placeholder TTS function.
    Replace with real audio generation later.
    """
    return b"FAKE_AUDIO_DATA_" + text.encode()
