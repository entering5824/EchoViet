"""Transcript viewer and editor with formatting options."""
import streamlit as st
import re


def format_transcript_text(text: str, options: dict) -> str:
    """Format transcript with options: punctuation, capitalize, remove extra spaces."""
    if not text:
        return ""
    formatted = text
    if options.get("auto_punctuation", False):
        if formatted and formatted[-1] not in ".!?":
            formatted += "."
        formatted = re.sub(r"\s+([,.!?;:])", r"\1", formatted)
        formatted = re.sub(r"([,.!?;:])\s*([,.!?;:])", r"\1\2", formatted)
        formatted = re.sub(r"\s+", " ", formatted)
    if options.get("capitalize_sentences", False):
        sentences = re.split(r"([.!?]\s+)", formatted)
        formatted = ""
        for part in sentences:
            if part.strip() and len(part) > 1:
                formatted += part[0].upper() + part[1:]
            else:
                formatted += part
    if options.get("remove_extra_spaces", True):
        formatted = re.sub(r"\s+", " ", formatted).strip()
    return formatted


def render_transcript_viewer(transcript_text: str, key_prefix: str = "viewer"):
    """Render transcript text area with formatting options. Returns (edited_text, options)."""
    st.subheader("✏️ Xem / Chỉnh sửa Transcript")
    with st.expander("🔧 Tùy chọn định dạng"):
        col1, col2 = st.columns(2)
        with col1:
            auto_punct = st.checkbox("Tự động chèn dấu câu", value=False, key=f"{key_prefix}_punct")
            capitalize = st.checkbox("Viết hoa đầu câu", value=False, key=f"{key_prefix}_cap")
        with col2:
            remove_spaces = st.checkbox("Loại bỏ khoảng trắng thừa", value=True, key=f"{key_prefix}_sp")
    options = {
        "auto_punctuation": auto_punct,
        "capitalize_sentences": capitalize,
        "remove_extra_spaces": remove_spaces,
    }
    formatted = format_transcript_text(transcript_text, options)
    edited = st.text_area("Transcript", value=formatted, height=300, key=f"{key_prefix}_area")
    return edited, options
