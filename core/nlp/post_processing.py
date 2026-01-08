"""
Post-processing: Grammar correction, punctuation
"""
import re
from typing import Dict, Optional

# Import semantic correction
try:
    from core.nlp.semantic_correction import apply_semantic_corrections, fix_broken_sentences
except ImportError:
    # Fallback if module not available
    def apply_semantic_corrections(text: str) -> str:
        return text
    def fix_broken_sentences(text: str) -> str:
        return text

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

def clean_garbage_characters(text: str) -> str:
    """
    Loại bỏ ký tự rác và dấu câu thừa
    
    Args:
        text: Input text
    
    Returns:
        Text đã được làm sạch
    """
    if not text:
        return ""
    
    # Remove multiple consecutive punctuation marks (;;;, ..., ,,,, etc.)
    txt = re.sub(r'([.;:,!?])\1{2,}', '', text)  # Remove 3+ consecutive same punctuation
    
    # Remove patterns like "vì. .", "em chỉ. ." (dấu chấm + space + dấu chấm)
    txt = re.sub(r'\.\s+\.', '', txt)
    txt = re.sub(r'\.\s*\.\s*\.', '', txt)  # Remove "..."
    
    # Remove standalone punctuation with spaces around
    txt = re.sub(r'\s+[.;:,!?]\s+', ' ', txt)
    
    # Remove punctuation at start of line (except if it's part of quoted text)
    txt = re.sub(r'^[.;:,!?]+\s+', '', txt, flags=re.MULTILINE)
    
    # Clean up multiple spaces
    txt = re.sub(r'\s+', ' ', txt).strip()
    
    return txt

def normalize_vietnamese(text: str) -> str:
    """Apply Vietnamese text normalization với cải thiện cho mixed language.

    - Unicode NFC normalization
    - Remove common bracketed noise tokens (e.g., [laughter])
    - Normalize spacing and punctuation
    - Fix common Vietnamese transcription errors
    - Preserve English words in mixed language scenarios
    - Clean garbage characters
    """
    if not text:
        return ""

    import unicodedata
    txt = unicodedata.normalize('NFC', text)

    # Remove bracketed tokens like [laughter], [noise], [inaudible], [music]
    txt = re.sub(r"\[.*?\]", "", txt)
    
    # Remove common filler words/phrases that Whisper might add
    filler_phrases = [
        r"\bà\s+",  # "à" standalone
        r"\bừ\s+",  # "ừ" standalone
        r"\bờ\s+",  # "ờ" standalone
    ]
    for pattern in filler_phrases:
        txt = re.sub(pattern, " ", txt)
    
    # Clean garbage characters first
    txt = clean_garbage_characters(txt)

    # Normalize whitespace (preserve space between Vietnamese and English words)
    txt = re.sub(r"\s+", " ", txt).strip()

    # Fix spacing around punctuation (Vietnamese style)
    # Dấu câu không có space trước, có space sau (trừ dấu cuối câu)
    txt = re.sub(r"\s+([,.!?;:])", r"\1", txt)
    txt = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", txt)  # Add space after punctuation if missing
    
    # Fix spacing around Vietnamese quotation marks
    txt = re.sub(r'"\s+', '"', txt)  # Remove space after opening quote
    txt = re.sub(r'\s+"', '"', txt)  # Remove space before closing quote
    
    # Fix common spacing issues with Vietnamese words
    # Vietnamese words typically don't have spaces between syllables
    # But we'll be conservative here to avoid breaking valid text

    return txt


def improve_vietnamese_punctuation(text: str) -> str:
    """
    Cải thiện dấu câu cho tiếng Việt
    
    - Thêm dấu chấm cuối câu nếu thiếu
    - Chuẩn hóa dấu câu
    - Xử lý các trường hợp đặc biệt của tiếng Việt
    - Loại bỏ dấu câu thừa
    """
    if not text:
        return ""
    
    text = text.strip()
    
    # Clean garbage characters first
    text = clean_garbage_characters(text)
    
    # Remove multiple consecutive punctuation marks
    text = re.sub(r'([.!?;:,])\1+', r'\1', text)  # Remove duplicates
    
    # Fix patterns like ". ." or ".." 
    text = re.sub(r'\.\s*\.', '.', text)
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r';\s*;', ';', text)
    
    # Thêm dấu chấm cuối nếu thiếu và text không kết thúc bằng dấu câu
    if text and text[-1] not in ".!?…":
        text += "."
    
    # Fix spacing after punctuation (Vietnamese style)
    text = re.sub(r'([.!?])([^\s])', r'\1 \2', text)
    
    # Capitalize first letter of sentences
    sentences = re.split(r'([.!?]\s+)', text)
    result = ""
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            # Capitalize first letter if it's Vietnamese or English
            if len(sentence) > 0:
                first_char = sentence[0]
                if first_char.islower() and (first_char.isalpha() or first_char in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"):
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            result += sentence
        else:
            result += sentence
    
    return result.strip()


def format_text(text: str, options: Dict) -> str:
    """
    Format text với các options, tối ưu cho tiếng Việt
    
    Args:
        text: Input text
        options: Dict với các formatting options
            - punctuation: bool - Cải thiện dấu câu
            - capitalize: bool - Viết hoa đầu câu
            - remove_extra_spaces: bool - Xóa khoảng trắng thừa
            - improve_vietnamese: bool - Áp dụng cải thiện tiếng Việt
            - fix_semantic_errors: bool - Sửa lỗi semantic (default: True)
    
    Returns:
        Formatted text
    """
    formatted = text
    
    # Clean garbage characters first (always apply)
    formatted = clean_garbage_characters(formatted)
    
    # Fix broken sentences (câu bị gãy)
    formatted = fix_broken_sentences(formatted)
    
    # Apply semantic corrections if enabled (default: True)
    if options.get("fix_semantic_errors", True):
        formatted = apply_semantic_corrections(formatted)
    
    # Áp dụng normalize Vietnamese trước
    if options.get("improve_vietnamese", True):
        formatted = normalize_vietnamese(formatted)
    
    if options.get("punctuation", True):
        formatted = improve_vietnamese_punctuation(formatted)
    
    if options.get("capitalize", True):
        formatted = capitalize_sentences(formatted)
    
    if options.get("remove_extra_spaces", True):
        formatted = re.sub(r'\s+', ' ', formatted).strip()
    
    # Final cleanup of garbage characters
    formatted = clean_garbage_characters(formatted)
    
    return formatted

