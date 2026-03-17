"""Orchestrate transcription: load model, run pipeline, format output."""
from typing import Dict, List, Optional, Any

from core.asr.transcription_service import load_whisper_model, get_vietnamese_initial_prompt
from core.transcriber import transcribe_with_vad_pipeline


def load_whisper_model_cached(model_size: str = "base"):
    """Load Whisper model (cached in core.asr.transcription_service). Returns (model, device)."""
    return load_whisper_model(model_size=model_size)


def transcribe_audio(
    model,
    audio_path_or_array,
    sr: int = 16000,
    language: str = "vi",
    task: str = "transcribe",
    verbose: bool = False,
    initial_prompt: Optional[str] = None,
    beam_size: int = 5,
    temperature: float = 0.0,
    condition_on_previous_text: bool = True,
    best_of: int = 5,
    use_vietnamese_optimization: bool = True,
) -> Optional[Dict]:
    """Transcribe with Whisper model. Returns Whisper result dict or None."""
    if model is None:
        return None
    effective_prompt = initial_prompt
    if use_vietnamese_optimization and language == "vi" and initial_prompt is None:
        effective_prompt = get_vietnamese_initial_prompt(include_english=True)
    try:
        kwargs = {
            "language": language,
            "task": task,
            "verbose": verbose,
            "fp16": False,
            "beam_size": beam_size,
            "temperature": temperature,
            "condition_on_previous_text": condition_on_previous_text,
            "best_of": best_of,
        }
        if effective_prompt:
            kwargs["initial_prompt"] = effective_prompt
        return model.transcribe(audio_path_or_array, **kwargs)
    except Exception:
        return None


def transcribe_with_pipeline(
    audio_path: str,
    model_size: str = "base",
    vad_threshold: float = 0.5,
    window_min: float = 20.0,
    window_max: float = 30.0,
    language: str = "vi",
    postprocess_options: Optional[dict] = None,
    asr_backend: Optional[str] = None,
    model_id: Optional[str] = None,
    compute_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run full VAD + ASR pipeline. model_id: whisper | faster_whisper | distil_whisper | whisper_large_v3_turbo | parakeet | moonshine."""
    return transcribe_with_vad_pipeline(
        audio_path,
        model_size=model_size,
        vad_threshold=vad_threshold,
        window_min=window_min,
        window_max=window_max,
        language=language,
        postprocess_options=postprocess_options,
        asr_backend=asr_backend,
        model_id=model_id or asr_backend,
        compute_type=compute_type,
    )


def format_time(seconds: float) -> str:
    """Format seconds for display."""
    return f"{seconds:.2f}"
