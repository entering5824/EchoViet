"""Speaker diarization: segment transcript by speaker (energy/silence-based)."""
import re
from typing import List, Dict, Any

import numpy as np
import librosa


def simple_speaker_segmentation(
    audio_array: np.ndarray,
    sr: int,
    segments: List[Any],
    min_silence_duration: float = 0.5,
    max_speakers: int = 4,
) -> List[Dict]:
    """
    Phân đoạn đơn giản dựa trên energy và silence, gán speaker dựa trên transcript segments.
    Returns list of dicts with keys: speaker, start, end, text.
    """
    try:
        if segments and isinstance(segments[0], str):
            parsed_segments = []
            for line in segments:
                line = line.strip()
                if not line:
                    continue
                ts_match = re.match(r"\[([\d.]+)\s*-\s*([\d.]+)\]\s*(.+)", line)
                if ts_match:
                    start, end, text = float(ts_match.group(1)), float(ts_match.group(2)), ts_match.group(3)
                    parsed_segments.append({"start": start, "end": end, "text": text.strip()})
                else:
                    prev_end = parsed_segments[-1]["end"] if parsed_segments else 0
                    estimated_dur = len(line.split()) * 0.5
                    parsed_segments.append({"start": prev_end, "end": prev_end + estimated_dur, "text": line})
            segments = parsed_segments

        if not segments or len(segments) == 0:
            return []
        if not isinstance(segments[0], dict) or "start" not in segments[0]:
            return []

        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        energy = librosa.feature.rms(y=audio_array, frame_length=frame_length, hop_length=hop_length)[0]
        energy_threshold = np.percentile(energy, 25)

        speaker_segments = []
        current_speaker = 1
        last_seg_end = 0.0

        for i, seg in enumerate(segments):
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_text = (seg.get("text") or "").strip()
            if not seg_text:
                continue
            gap = seg_start - last_seg_end if i > 0 else 0
            start_frame = int(seg_start * sr / hop_length)
            end_frame = int(seg_end * sr / hop_length)
            seg_energy = (
                np.mean(energy[start_frame:end_frame])
                if start_frame < len(energy) and end_frame <= len(energy)
                else energy_threshold
            )
            should_switch = False
            if gap > min_silence_duration * 1.5:
                should_switch = True
            elif i > 0 and speaker_segments:
                prev_seg = speaker_segments[-1]
                prev_start = int(prev_seg["start"] * sr / hop_length)
                prev_end_f = int(prev_seg["end"] * sr / hop_length)
                if prev_start < len(energy) and prev_end_f <= len(energy):
                    prev_energy = np.mean(energy[prev_start:prev_end_f])
                    energy_diff = abs(seg_energy - prev_energy) / (prev_energy + 1e-6)
                    if energy_diff > 0.3:
                        should_switch = True
            if should_switch:
                current_speaker = (current_speaker % max_speakers) + 1
            speaker_segments.append({
                "speaker": f"Speaker {current_speaker}",
                "start": seg_start,
                "end": seg_end,
                "text": seg_text,
            })
            last_seg_end = seg_end
        return speaker_segments
    except Exception as e:
        try:
            import streamlit as st
            st.warning(f"Không thể thực hiện speaker diarization: {str(e)}")
        except Exception:
            pass
        return []


def format_with_speakers(segments: List[Dict]) -> str:
    """Format transcript với thông tin speaker."""
    if not segments:
        return ""
    lines = []
    for seg in segments:
        speaker = seg.get("speaker", "Unknown")
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = (seg.get("text") or "").strip()
        if text:
            lines.append(f"[{format_time(start)} - {format_time(end)}] {speaker}: {text}")
    return "\n".join(lines)


def format_time(seconds: float) -> str:
    """Format thời gian."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    return f"{minutes:02d}:{secs:02d}.{millis:03d}"
