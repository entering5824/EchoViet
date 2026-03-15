"""
Speaker diarization using pyannote.audio.
Requires: pip install pyannote.audio, Hugging Face token for pyannote/speaker-diarization-3.1 or community model.
Merge diarization with Whisper segments to produce "Speaker 1: ... Speaker 2: ...".
"""

import os
from typing import List, Dict, Any, Optional

_pipeline = None


def _load_pipeline(hf_token: Optional[str] = None):
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        from pyannote.audio import Pipeline
        token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if not token:
            return None
        _pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )
        return _pipeline
    except Exception:
        try:
            from pyannote.audio import Pipeline
            token = hf_token or os.getenv("HF_TOKEN")
            if not token:
                return None
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1",
                use_auth_token=token,
            )
            return _pipeline
        except Exception:
            return None


def diarize(audio_path: str, hf_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run pyannote diarization on audio file.
    Returns list of {"speaker": "SPEAKER_00", "start": float, "end": float}.
    """
    pipeline = _load_pipeline(hf_token)
    if pipeline is None:
        return []
    try:
        diar = pipeline(audio_path)
        segments = []
        for turn, _, speaker in diar.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end,
            })
        return segments
    except Exception:
        return []


def merge_transcript_with_diarization(
    whisper_segments: List[Dict],
    diar_segments: List[Dict],
) -> List[Dict[str, Any]]:
    """
    Align Whisper segments with diarization by time overlap.
    whisper_segments: [{"start", "end", "text"}, ...]
    diar_segments: [{"speaker", "start", "end"}, ...]
    Returns [{"speaker": "Speaker 1", "start", "end", "text"}, ...].
    """
    if not whisper_segments or not diar_segments:
        return [{"speaker": "Speaker 1", "start": s.get("start", 0), "end": s.get("end", 0), "text": s.get("text", "")} for s in whisper_segments]
    out = []
    for ws in whisper_segments:
        start, end = ws.get("start", 0), ws.get("end", 0)
        text = (ws.get("text") or "").strip()
        if not text:
            continue
        best_speaker = "Speaker 1"
        max_overlap = 0
        for ds in diar_segments:
            o_start = max(start, ds["start"])
            o_end = min(end, ds["end"])
            if o_end > o_start:
                overlap = o_end - o_start
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = ds["speaker"].replace("SPEAKER_", "Speaker ")
        out.append({"speaker": best_speaker, "start": start, "end": end, "text": text})
    return out


def format_diarized_transcript(merged: List[Dict]) -> str:
    """Format as 'Speaker 1: ...\\nSpeaker 2: ...'."""
    lines = []
    for seg in merged:
        speaker = seg.get("speaker", "Speaker 1")
        text = (seg.get("text") or "").strip()
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)
