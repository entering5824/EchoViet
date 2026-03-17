"""ASR Model manager: unified loader for Whisper, Faster-Whisper, Distil-Whisper, Parakeet, Moonshine."""
from typing import Tuple, Optional
import streamlit as st

from core.asr.transcription_service import load_whisper_model


def _load_faster_whisper(model_size: str, compute_type: Optional[str] = None):
    """Load Faster-Whisper model (supports distil-large-v3, large-v3-turbo, etc.)."""
    import faster_whisper
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"
    model = faster_whisper.WhisperModel(model_size, device=device, compute_type=compute_type)
    return model, device


def _load_parakeet(model_size: str):
    """Load NVIDIA Parakeet via transformers pipeline."""
    from transformers import pipeline
    import torch
    model_map = {
        "parakeet-ctc-1.1b": "nvidia/parakeet-ctc-1.1b",
        "parakeet-rnnt-1.1b": "nvidia/parakeet-rnnt-1.1b",
    }
    hf_id = model_map.get(model_size, "nvidia/parakeet-ctc-1.1b")
    device = 0 if torch.cuda.is_available() else -1
    pipe = pipeline("automatic-speech-recognition", model=hf_id, device=device)
    return pipe, "cuda" if device >= 0 else "cpu"


def _load_moonshine(model_size: str):
    """Load Moonshine via transformers pipeline."""
    from transformers import pipeline
    import torch
    model_map = {
        "moonshine-tiny": "UsefulSensors/moonshine-tiny",
        "moonshine-base": "UsefulSensors/moonshine-base",
    }
    hf_id = model_map.get(model_size, "UsefulSensors/moonshine-base")
    device = 0 if torch.cuda.is_available() else -1
    pipe = pipeline("automatic-speech-recognition", model=hf_id, device=device)
    return pipe, "cuda" if device >= 0 else "cpu"


@st.cache_resource
def get_asr_model(
    model_id: str = "whisper",
    model_size: str = "base",
    compute_type: Optional[str] = None,
) -> Tuple[Optional[object], str]:
    """Return (model, device) for the requested ASR model.

    Supports: whisper, faster_whisper, distil_whisper, whisper_large_v3_turbo,
    parakeet, moonshine.
    """
    model_id = (model_id or "whisper").lower()

    if model_id == "whisper":
        return load_whisper_model(model_size)

    if model_id == "faster_whisper":
        return _load_faster_whisper(model_size, compute_type)

    if model_id == "distil_whisper":
        return _load_faster_whisper(model_size or "distil-large-v3", compute_type)

    if model_id == "whisper_large_v3_turbo":
        return _load_faster_whisper("large-v3-turbo", compute_type)

    if model_id == "parakeet":
        return _load_parakeet(model_size or "parakeet-ctc-1.1b")

    if model_id == "moonshine":
        return _load_moonshine(model_size or "moonshine-base")

    st.warning(f"Model '{model_id}' chưa hỗ trợ, dùng Whisper base.")
    return load_whisper_model("base")
