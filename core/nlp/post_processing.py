"""
Post-processing: Grammar correction, punctuation
"""
import re
from typing import Dict, Optional

def correct_punctuation(text: str) -> str:
    """
    Sửa dấu câu cơ bản
    
    Args:
        text: Raw text
    
    Returns:
        Text với punctuation đã được sửa
    """
    if not text:
        return ""
    
    # Thêm dấu chấm cuối câu nếu thiếu
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1\2', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def capitalize_sentences(text: str) -> str:
    """
    Viết hoa đầu câu
    
    Args:
        text: Input text
    
    Returns:
        Text với đầu câu đã viết hoa
    """
    if not text:
        return ""
    
    sentences = re.split(r'([.!?]\s+)', text)
    result = ""
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            if len(sentence) > 1:
                result += sentence[0].upper() + sentence[1:]
            else:
                result += sentence.upper()
        else:
            result += sentence
    
    return result

def normalize_vietnamese(text: str) -> str:
    """Apply basic Vietnamese text normalization.

    - Unicode NFC normalization
    - Remove common bracketed noise tokens (e.g., [laughter])
    - Normalize spacing and punctuation
    """
    if not text:
        return ""

    import unicodedata
    txt = unicodedata.normalize('NFC', text)

    # Remove bracketed tokens like [laughter], [noise], [inaudible]
    txt = re.sub(r"\[.*?\]", "", txt)

    # Normalize whitespace
    txt = re.sub(r"\s+", " ", txt).strip()

    # Fix spacing around punctuation
    txt = re.sub(r"\s+([,.!?;:])", r"\1", txt)

    return txt


def format_text(text: str, options: Dict) -> str:
    """
    Format text với các options
    
    Args:
        text: Input text
        options: Dict với các formatting options
    
    Returns:
        Formatted text
    """
    formatted = text
    
    if options.get("punctuation", False):
        formatted = correct_punctuation(formatted)
    
    if options.get("capitalize", False):
        formatted = capitalize_sentences(formatted)
    
    if options.get("remove_extra_spaces", True):
        formatted = re.sub(r'\s+', ' ', formatted).strip()
    
    return formatted

