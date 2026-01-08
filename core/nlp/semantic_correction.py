"""
Semantic Correction for Vietnamese ASR Errors
Sửa các lỗi semantic phổ biến từ ASR (speech-to-text)
"""
import re
from typing import Dict, List, Tuple

# Common ASR error corrections (phát âm sai → từ đúng)
COMMON_ASR_CORRECTIONS: Dict[str, str] = {
    # Common pronunciation errors
    "chứng cấp 3": "trường cấp 3",
    "nối tiếng": "nổi tiếng",
    "dạy với một trường": "học ở một trường",  # Context-dependent, but common pattern
    "chia. Sẻ": "chia sẻ",
    "chia. sẻ": "chia sẻ",
    "chia sẻ": "chia sẻ",  # Keep correct ones
    # Add more common errors as needed
}

# Pattern-based corrections (regex patterns)
PATTERN_CORRECTIONS: List[Tuple[str, str, str]] = [
    # (pattern, replacement, description)
    (r'\bchia\.\s*[Ss]ẻ\b', 'chia sẻ', 'Fix "chia. Sẻ" → "chia sẻ"'),
    (r'\bchứng\s+cấp\s+3\b', 'trường cấp 3', 'Fix "chứng cấp 3" → "trường cấp 3"'),
    (r'\bnối\s+tiếng\b', 'nổi tiếng', 'Fix "nối tiếng" → "nổi tiếng"'),
    (r'\bdạy\s+với\s+một\s+trường\b', 'học ở một trường', 'Fix "dạy với một trường" → "học ở một trường"'),
]

def apply_semantic_corrections(text: str) -> str:
    """
    Áp dụng các sửa lỗi semantic phổ biến cho văn bản tiếng Việt
    
    Args:
        text: Input text
    
    Returns:
        Text đã được sửa lỗi semantic
    """
    if not text:
        return ""
    
    corrected = text
    
    # Apply dictionary-based corrections
    for wrong, correct in COMMON_ASR_CORRECTIONS.items():
        # Case-insensitive replacement
        corrected = re.sub(re.escape(wrong), correct, corrected, flags=re.IGNORECASE)
    
    # Apply pattern-based corrections
    for pattern, replacement, _ in PATTERN_CORRECTIONS:
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
    
    return corrected

def fix_broken_sentences(text: str) -> str:
    """
    Sửa các câu bị gãy do dấu chấm sai chỗ
    
    Args:
        text: Input text
    
    Returns:
        Text với câu đã được nối lại
    """
    if not text:
        return ""
    
    # Fix patterns like "chia. Sẻ" → "chia sẻ"
    # Remove period before capitalized word if it's part of a compound word
    corrected = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ])\.\s+([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+)', r'\1 \2', corrected)
    
    return corrected
