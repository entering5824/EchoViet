"""Pipeline helper: normalize -> VAD -> segment -> Whisper transcription -> normalize text"""
import os
import tempfile
import soundfile as sf
from typing import List, Dict, Optional
import numpy as np
import torch
import streamlit as st

from core.audio.audio_processor import normalize_audio_to_wav
from core.audio import vad as vad_module
from core.asr.model_manager import get_asr_model
from core.asr.transcription_service import transcribe_audio
from core.nlp.post_processing import format_text, normalize_vietnamese


def transcribe_with_vad_pipeline(
    audio_path: str,
    model_size: str = "tiny",
    vad_threshold: float = 0.5,
    window_min: float = 20.0,
    window_max: float = 30.0,
    language: str = "vi",
    postprocess_options: Optional[dict] = None,
):
    """Run the full requested pipeline and return structured results.

    Returns Dict with keys: 'segments' (list), 'text' (full text), 'duration'
    """
    postprocess_options = postprocess_options or {}

    # 1) Normalize audio to 16k mono PCM
    norm_path, sr, y = normalize_audio_to_wav(audio_path, target_sr=16000)
    try:
        duration = len(y) / sr

        # 2) Load Silero VAD
        device = "cpu"
        model, utils = vad_module.load_silero_vad(device=device)

        # 3) Get speech timestamps
        timestamps = vad_module.get_speech_timestamps_from_array(y, sr, model, utils, threshold=vad_threshold)
        timestamps = vad_module.merge_close_timestamps(timestamps, max_gap=0.5)

        # 4) Group into 20-30s windows
        windows = vad_module.group_segments_into_windows(timestamps, min_dur=window_min, max_dur=window_max, audio_duration=duration)

        # If no windows (e.g., model failed or no speech detected), fallback to single window
        if not windows:
            windows = [{"start": 0.0, "end": duration}]

        # 5) Load Whisper model (force CPU, fp16=False inside transcribe)
        st.info(f"🔁 Loading Whisper model ({model_size}) — this may take a moment...")
        whisper_model, device = get_asr_model(model_size, backend='whisper')
        if whisper_model is None:
            st.error("❌ Không thể tải Whisper model")
            return None

        segments = []
        full_text_parts: List[str] = []

        for idx, w in enumerate(windows):
            wav_path, s_start, s_end = vad_module.extract_window_audio(y, sr, w)
            try:
                result = transcribe_audio(whisper_model, wav_path, sr=sr, language=language, task="transcribe", verbose=False)
                text = result.get("text", "") if result else ""
                # Post-process each segment
                if postprocess_options.get("apply_normalize", True):
                    text = normalize_vietnamese(text)
                text = format_text(text, postprocess_options)

                segments.append({"index": idx, "start": s_start, "end": s_end, "text": text})
                full_text_parts.append(text)
            finally:
                # Clean up temporary chunk
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass

        full_text = "\n".join(full_text_parts)

        return {
            "segments": segments,
            "text": full_text,
            "duration": duration,
            "windows": windows,
        }
    finally:
        try:
            if os.path.exists(norm_path):
                os.unlink(norm_path)
        except Exception:
            pass
