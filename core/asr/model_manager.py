"""ASR Model manager: unified wrapper and caching for ASR models.

Provides a small abstraction over available ASR backends (currently Whisper)
and exposes a cached loader suitable for Streamlit deployments.
"""
from typing import Tuple
import streamlit as st

from core.asr.transcription_service import load_whisper_model


@st.cache_resource
def get_asr_model(model_size: str = "tiny", backend: str = "whisper") -> Tuple[object, str]:
    """Return (model, device) for the requested ASR backend and model size.

    Currently supports backend='whisper'. This is intentionally small and
    delegates to `load_whisper_model` which already handles device selection
    and error handling.

    The resource is cached by Streamlit to avoid repeated downloads and loads.
    """
    backend = backend.lower()
    if backend == "whisper":
        model, device = load_whisper_model(model_size)
        return model, device
    else:
        st.error(f"Unsupported ASR backend: {backend}")
        return None, None
