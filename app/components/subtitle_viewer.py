"""Dual subtitle viewer: show source and/or translation per segment with optional confidence."""
import streamlit as st
from typing import List, Dict, Any


def render_subtitle_viewer(
    segments: List[Dict[str, Any]],
    mode: str = "dual",
    show_confidence: bool = False,
    key_prefix: str = "sub",
) -> None:
    """
    Render segments as subtitle view. mode: 'source' | 'translation' | 'dual'.
    If dual, show both source and translation per segment. show_confidence: show confidence_asr if present.
    """
    if not segments:
        st.caption("Chưa có segment.")
        return
    for i, seg in enumerate(segments):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = (seg.get("text") or "").strip()
        trans = (seg.get("translated_text") or "").strip()
        conf = seg.get("confidence_asr")
        time_str = f"[{start:.1f}s - {end:.1f}s]"
        if mode == "source":
            line = f"{time_str} {text}"
        elif mode == "translation":
            line = f"{time_str} {trans or text}"
        else:
            line = f"{time_str} {text}"
            if trans:
                line += "\n  → " + trans
        if show_confidence and conf is not None:
            line += f" (conf: {conf:.2f})"
        st.text(line)
