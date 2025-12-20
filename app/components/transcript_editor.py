"""
Component editor transcript với formatting options
"""
import streamlit as st
import re

def format_transcript_text(text: str, options: dict) -> str:
    """
    Format transcript text với các options
    
    Args:
        text: Raw transcript text
        options: Dict với các formatting options
            - auto_punctuation: bool
            - capitalize_sentences: bool
            - remove_extra_spaces: bool
    """
    if not text:
        return ""
    
    formatted = text
    
    # Auto punctuation
    if options.get("auto_punctuation", False):
        # Thêm dấu chấm cuối câu nếu thiếu
        if formatted and formatted[-1] not in ".!?":
            formatted += "."
        # Fix spacing around punctuation
        formatted = re.sub(r'\s+([,.!?;:])', r'\1', formatted)
        formatted = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1\2', formatted)
        formatted = re.sub(r'\s+', ' ', formatted)
    
    # Capitalize sentences
    if options.get("capitalize_sentences", False):
        sentences = re.split(r'([.!?]\s+)', formatted)
        formatted = ""
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                formatted += sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            else:
                formatted += sentence
    
    # Remove extra spaces
    if options.get("remove_extra_spaces", False):
        formatted = re.sub(r'\s+', ' ', formatted).strip()
    
    return formatted

def render_transcript_editor(transcript_text: str, key_prefix: str = "editor"):
    """
    Render transcript editor với formatting options
    
    Returns:
        Tuple (edited_text: str, formatting_options: dict)
    """
    st.subheader("✏️ Chỉnh sửa Transcript")
    
    # Formatting options
    with st.expander("🔧 Formatting Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            auto_punct = st.checkbox("Tự động chèn dấu câu", value=False, key=f"{key_prefix}_punct")
            capitalize = st.checkbox("Viết hoa đầu câu", value=False, key=f"{key_prefix}_capitalize")
        
        with col2:
            remove_spaces = st.checkbox("Loại bỏ khoảng trắng thừa", value=True, key=f"{key_prefix}_spaces")
            show_timestamps = st.checkbox("Hiển thị timestamps", value=False, key=f"{key_prefix}_timestamps")
    
    # Apply formatting
    formatting_options = {
        "auto_punctuation": auto_punct,
        "capitalize_sentences": capitalize,
        "remove_extra_spaces": remove_spaces
    }
    
    formatted_text = format_transcript_text(transcript_text, formatting_options)
    
    # Editor
    edited_text = st.text_area(
        "Chỉnh sửa transcript:",
        formatted_text,
        height=400,
        key=f"{key_prefix}_textarea"
    )
    
    return edited_text, formatting_options

