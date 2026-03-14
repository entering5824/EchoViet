"""Timestamp alignment: normalize and align segment timestamps for transcript/player."""
from typing import List, Dict, Any


def align_segments(
    segments: List[Dict[str, Any]],
    *,
    ensure_start_end: bool = True,
    merge_gap_seconds: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Normalize segment list: ensure each has 'start', 'end', 'text';
    optionally merge segments separated by less than merge_gap_seconds.
    """
    if not segments:
        return []
    out = []
    for seg in segments:
        s = dict(seg)
        if ensure_start_end:
            s.setdefault("start", 0.0)
            s.setdefault("end", 0.0)
            s.setdefault("text", "")
        out.append(s)

    if merge_gap_seconds <= 0:
        return out

    merged = [out[0]]
    for seg in out[1:]:
        prev = merged[-1]
        gap = seg["start"] - prev["end"]
        if gap <= merge_gap_seconds and prev.get("text") and seg.get("text"):
            prev["end"] = seg["end"]
            prev["text"] = (prev.get("text", "") + " " + seg.get("text", "")).strip()
        else:
            merged.append(seg)
    return merged


def segments_to_timed_text(segments: List[Dict], sep: str = "\n") -> str:
    """Format segments as '[start - end] text' lines."""
    lines = []
    for s in segments:
        start = s.get("start", 0)
        end = s.get("end", 0)
        text = (s.get("text") or "").strip()
        if text:
            lines.append(f"[{start:.2f} - {end:.2f}] {text}")
    return sep.join(lines)
