"""Speech-to-text pipeline: normalize -> VAD -> segment -> Whisper/Faster-Whisper -> post-process (no Streamlit)."""
import os
from typing import List, Dict, Optional, Any

from utils import audio_utils
from models import model_manager
from models.whisper_model import get_vietnamese_initial_prompt
from core import summarizer


def transcribe_with_vad_pipeline(
    audio_path: str,
    model_size: str = "base",
    vad_threshold: float = 0.5,
    window_min: float = 20.0,
    window_max: float = 30.0,
    language: str = "vi",
    postprocess_options: Optional[dict] = None,
    asr_backend: str = "whisper",
    compute_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Run full pipeline: normalize audio -> VAD -> windows -> Whisper per window -> post-process.
    Returns dict with keys: segments, text, duration, windows; or None on failure.
    """
    postprocess_options = postprocess_options or {}

    norm_path, sr, y = audio_utils.normalize_audio_to_wav(audio_path, target_sr=16000)
    try:
        duration = len(y) / sr
        model, utils = audio_utils.load_silero_vad(device="cpu")
        if model is None or utils is None:
            windows = [{"start": 0.0, "end": duration}]
        else:
            timestamps = audio_utils.get_speech_timestamps_from_array(y, sr, model, utils, threshold=vad_threshold)
            timestamps = audio_utils.merge_close_timestamps(timestamps, max_gap=0.5)
            windows = audio_utils.group_segments_into_windows(
                timestamps, min_dur=window_min, max_dur=window_max, audio_duration=duration
            )
            if not windows:
                windows = [{"start": 0.0, "end": duration}]

        asr_backend = (asr_backend or "whisper").lower()
        asr_model, _ = model_manager.get_asr_model(
            model_size=model_size,
            backend=asr_backend,
            compute_type=compute_type,
        )
        if asr_model is None:
            return None

        initial_prompt = get_vietnamese_initial_prompt(include_english=True) if language == "vi" else None
        segments = []
        full_text_parts: List[str] = []

        for idx, w in enumerate(windows):
            wav_path, s_start, s_end = audio_utils.extract_window_audio(y, sr, w)
            try:
                if asr_backend == "faster_whisper":
                    from models.faster_whisper_model import transcribe as fw_transcribe
                    result = fw_transcribe(
                        asr_model,
                        wav_path,
                        language=language or None,
                        initial_prompt=initial_prompt,
                    )
                    fw_segments = result.get("segments") or []
                    text = (result.get("text") or "").strip()
                    confidences = [seg.get("confidence_asr") for seg in fw_segments if seg.get("confidence_asr") is not None]
                    confidence_asr = sum(confidences) / len(confidences) if confidences else None
                else:
                    result = asr_model.transcribe(
                        wav_path,
                        language=language,
                        task="transcribe",
                        verbose=False,
                        fp16=False,
                        initial_prompt=initial_prompt,
                        beam_size=5,
                        temperature=0.0,
                        condition_on_previous_text=True,
                        best_of=5,
                    )
                    text = (result.get("text") or "").strip()
                    confidence_asr = None

                if postprocess_options.get("apply_normalize", True):
                    text = summarizer.normalize_vietnamese(text)
                text = summarizer.format_text(text, postprocess_options)
                seg_out = {"index": idx, "start": s_start, "end": s_end, "text": text}
                if confidence_asr is not None:
                    seg_out["confidence_asr"] = confidence_asr
                segments.append(seg_out)
                full_text_parts.append(text)
            finally:
                try:
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)
                except Exception:
                    pass

        return {
            "segments": segments,
            "text": "\n".join(full_text_parts),
            "duration": duration,
            "windows": windows,
        }
    finally:
        try:
            if os.path.exists(norm_path):
                os.unlink(norm_path)
        except Exception:
            pass
