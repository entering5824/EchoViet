"""NLP summarization, keywords, and text enhancement (re-exports and thin wrapper)."""
from core.nlp import keyword_extraction
from core.nlp import gemini_enhancement
from core.nlp import post_processing

# Re-export
extract_keywords = keyword_extraction.extract_keywords
simple_summarize = keyword_extraction.simple_summarize
enhance_with_gemini = gemini_enhancement.enhance_with_gemini
is_gemini_available = gemini_enhancement.is_gemini_available
normalize_vietnamese = post_processing.normalize_vietnamese
format_text = post_processing.format_text

try:
    from core.nlp.semantic_correction import apply_semantic_corrections, fix_broken_sentences
except ImportError:
    def apply_semantic_corrections(text: str) -> str:
        return text
    def fix_broken_sentences(text: str) -> str:
        return text

__all__ = [
    "extract_keywords",
    "simple_summarize",
    "enhance_with_gemini",
    "is_gemini_available",
    "normalize_vietnamese",
    "format_text",
    "apply_semantic_corrections",
    "fix_broken_sentences",
]
