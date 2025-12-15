"""
FastAPI endpoint cho upload audio -> transcript JSON.
Optional diarization flag (stub/simple segmentation nếu cần).
Chạy: uvicorn core.api.server:app --host 0.0.0.0 --port 8000
"""
import tempfile
import os

# Setup FFmpeg từ imageio-ffmpeg TRƯỚC KHI import các module khác
from core.audio.ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=True)

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.asr.transcription_service import load_whisper_model, transcribe_audio
from core.audio.audio_processor import normalize_audio_to_wav

app = FastAPI(title="Vietnamese STT API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load model once
_whisper_model = None
_whisper_device = None

def get_model():
    global _whisper_model, _whisper_device
    if _whisper_model is None:
        _whisper_model, _whisper_device = load_whisper_model("base")
    return _whisper_model


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), diarization: bool = Form(False)):
    try:
        model = get_model()
        if model is None:
            return JSONResponse(status_code=500, content={"error": "Model not loaded"})

        # Save uploaded file
        suffix = os.path.splitext(file.filename)[-1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(await file.read())
            tmp_in.flush()
            raw_path = tmp_in.name

        # Normalize to WAV 16kHz mono
        norm_path, sr, y = normalize_audio_to_wav(raw_path)

        result = transcribe_audio(model, norm_path, sr=sr, language="vi", task="transcribe")
        text = result.get("text", "") if result else ""

        # Cleanup temp files
        try:
            os.unlink(raw_path)
            os.unlink(norm_path)
        except Exception:
            pass

        return {
            "text": text,
            "language": result.get("language") if result else None,
            "segments": result.get("segments") if isinstance(result, dict) else None,
            "diarization": None  # diarization stub; có thể tích hợp pyannote nếu có model
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
