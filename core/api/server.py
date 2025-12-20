"""
FastAPI endpoint cho upload audio -> transcript JSON.
Optional diarization flag (stub/simple segmentation nếu cần).
Chạy: uvicorn core.api.server:app --host 0.0.0.0 --port 8000
"""
import tempfile
import os
import logging
from typing import Optional
from pathlib import Path

# Setup FFmpeg từ imageio-ffmpeg TRƯỚC KHI import các module khác
from core.audio.ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=True)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

# Try to import config, fallback to defaults if not available
try:
    from config import config
    API_HOST = config.API_HOST
    API_PORT = config.API_PORT
    ALLOWED_ORIGINS = config.ALLOWED_ORIGINS.split(",") if config.ALLOWED_ORIGINS != "*" else ["*"]
    MAX_UPLOAD_SIZE = config.MAX_UPLOAD_SIZE * 1024 * 1024  # Convert MB to bytes
    IS_PRODUCTION = config.is_production()
except ImportError:
    # Fallback defaults
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS", "*") != "*" else ["*"]
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "200")) * 1024 * 1024
    IS_PRODUCTION = os.getenv("APP_ENV", "development").lower() == "production"

# Configure logging
logging.basicConfig(
    level=logging.INFO if not IS_PRODUCTION else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from core.asr.transcription_service import load_whisper_model, transcribe_audio
from core.audio.audio_processor import normalize_audio_to_wav

# Initialize FastAPI app
app = FastAPI(
    title="Vietnamese STT API",
    version="0.1.0",
    description="API for Vietnamese Speech-to-Text transcription",
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted Host Middleware (production only)
if IS_PRODUCTION:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual domain in production
    )

# Lazy-load model once
_whisper_model = None
_whisper_device = None
_model_loading = False

def get_model():
    """Get or load Whisper model (thread-safe lazy loading)"""
    global _whisper_model, _whisper_device, _model_loading
    
    if _whisper_model is not None:
        return _whisper_model
    
    if _model_loading:
        # Model is being loaded, wait a bit
        import time
        time.sleep(1)
        return get_model()
    
    try:
        _model_loading = True
        logger.info("Loading Whisper model...")
        # Use config default if available
        model_size = os.getenv("DEFAULT_WHISPER_MODEL", "base")
        _whisper_model, _whisper_device = load_whisper_model(model_size)
        logger.info(f"Whisper model loaded on device: {_whisper_device}")
        return _whisper_model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise
    finally:
        _model_loading = False


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Vietnamese STT API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if not IS_PRODUCTION else "disabled"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        model = get_model()
        model_status = "loaded" if model is not None else "not_loaded"
        return {
            "status": "ok",
            "model": model_status,
            "device": _whisper_device
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    diarization: bool = Form(False),
    language: Optional[str] = Form("vi"),
    model_size: Optional[str] = Form(None)
):
    """
    Transcribe audio file to text
    
    Args:
        file: Audio file (WAV, MP3, FLAC, etc.)
        diarization: Enable speaker diarization (stub implementation)
        language: Language code (default: vi)
        model_size: Whisper model size (default: from config)
    
    Returns:
        JSON with transcription results
    """
    temp_files = []
    
    try:
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Get model
        model = get_model()
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")

        # Save uploaded file
        suffix = os.path.splitext(file.filename or "")[-1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(file_content)
            tmp_in.flush()
            raw_path = tmp_in.name
            temp_files.append(raw_path)

        # Normalize to WAV 16kHz mono
        try:
            norm_path, sr, y = normalize_audio_to_wav(raw_path)
            temp_files.append(norm_path)
        except Exception as e:
            logger.error(f"Audio normalization failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")

        # Transcribe
        try:
            result = transcribe_audio(
                model, 
                norm_path, 
                sr=sr, 
                language=language, 
                task="transcribe"
            )
            text = result.get("text", "") if result else ""
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {str(e)}")

        return {
            "text": text,
            "language": result.get("language") if result else language,
            "segments": result.get("segments") if isinstance(result, dict) else None,
            "diarization": None  # diarization stub; có thể tích hợp pyannote nếu có model
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        # Cleanup temp files on error
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": str(e) if not IS_PRODUCTION else "An error occurred"}
        )


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Vietnamese STT API...")
    logger.info(f"Environment: {'Production' if IS_PRODUCTION else 'Development'}")
    logger.info(f"Max upload size: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB")
    
    # Pre-load model if in production
    if IS_PRODUCTION:
        try:
            get_model()
            logger.info("Model pre-loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to pre-load model: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Vietnamese STT API...")


if __name__ == "__main__":
    uvicorn.run(
        "core.api.server:app",
        host=API_HOST,
        port=API_PORT,
        reload=not IS_PRODUCTION,
        log_level="info" if not IS_PRODUCTION else "warning"
    )
