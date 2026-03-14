"""Text normalization and formatting utilities (Vietnamese-friendly)."""
import re
import unicodedata
from typing import Dict


def correct_punctuation(text: str) -> str:
    """Basic punctuation fixes: spacing, trailing period."""
    if not text:
        return ""
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])\s*([,.!?;:])", r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def capitalize_sentences(text: str) -> str:
    """Capitalize first letter of each sentence."""
    if not text:
        return ""
    sentences = re.split(r"([.!?]\s+)", text)
    result = ""
    for part in sentences:
        if part.strip() and len(part) > 1:
            result += part[0].upper() + part[1:]
        else:
            result += part
    return result


def clean_garbage_characters(text: str) -> str:
    """Remove garbage characters and redundant punctuation."""
    if not text:
        return ""
    txt = re.sub(r"([.;:,!?])\1{2,}", "", text)
    txt = re.sub(r"\.\s+\.", "", txt)
    txt = re.sub(r"\.\s*\.\s*\.", "", txt)
    txt = re.sub(r"\s+[.;:,!?]\s+", " ", txt)
    txt = re.sub(r"^[.;:,!?]+\s+", "", txt, flags=re.MULTILINE)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def normalize_vietnamese(text: str) -> str:
    """Unicode NFC, remove bracketed tokens, normalize spacing and punctuation for Vietnamese."""
    if not text:
        return ""
    txt = unicodedata.normalize("NFC", text)
    txt = re.sub(r"\[.*?\]", "", txt)
    for pattern in [r"\bà\s+", r"\bừ\s+", r"\bờ\s+"]:
        txt = re.sub(pattern, " ", txt)
    txt = clean_garbage_characters(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = re.sub(r"\s+([,.!?;:])", r"\1", txt)
    txt = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", txt)
    txt = re.sub(r'"\s+', '"', txt)
    txt = re.sub(r'\s+"', '"', txt)
    return txt


def improve_vietnamese_punctuation(text: str) -> str:
    """Improve punctuation for Vietnamese: cleanup, trailing period, capitalize sentences."""
    if not text:
        return ""
    text = text.strip()
    text = clean_garbage_characters(text)
    text = re.sub(r"([.!?;:,])\1+", r"\1", text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r";\s*;", ";", text)
    if text and text[-1] not in ".!?…":
        text += "."
    text = re.sub(r"([.!?])([^\s])", r"\1 \2", text)
    sentences = re.split(r"([.!?]\s+)", text)
    result = ""
    for sentence in sentences:
        if sentence.strip() and len(sentence) > 0:
            first = sentence[0]
            if first.islower() and (
                first.isalpha()
                or first
                in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
            ):
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
        result += sentence
    return result.strip()


def format_text(
    text: str,
    options: Dict,
    *,
    fix_semantic_fn=None,
    fix_broken_fn=None,
) -> str:
    """Format text with given options. Optionally use fix_semantic_fn/fix_broken_fn (e.g. from core.nlp)."""
    formatted = text
    formatted = clean_garbage_characters(formatted)
    if fix_broken_fn:
        formatted = fix_broken_fn(formatted)
    if options.get("fix_semantic_errors", True) and fix_semantic_fn:
        formatted = fix_semantic_fn(formatted)
    if options.get("improve_vietnamese", True):
        formatted = normalize_vietnamese(formatted)
    if options.get("punctuation", True):
        formatted = improve_vietnamese_punctuation(formatted)
    if options.get("capitalize", True):
        formatted = capitalize_sentences(formatted)
    if options.get("remove_extra_spaces", True):
        formatted = re.sub(r"\s+", " ", formatted).strip()
    formatted = clean_garbage_characters(formatted)
    return formatted
