"""
Keyword extraction và summarization
"""
import re
from typing import List, Dict
from collections import Counter

def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """
    Extract keywords từ text (simple word frequency)
    
    Args:
        text: Input text
        top_k: Số lượng keywords cần extract
    
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Remove punctuation và lowercase
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Remove common Vietnamese stopwords (simple list)
    stopwords = {'và', 'của', 'cho', 'với', 'là', 'có', 'được', 'trong', 'từ', 'về',
                 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
                 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    # Filter stopwords và short words
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    
    # Count frequency
    word_freq = Counter(keywords)
    
    # Get top k
    top_keywords = [word for word, _ in word_freq.most_common(top_k)]
    
    return top_keywords

def simple_summarize(text: str, max_sentences: int = 3) -> str:
    """
    Simple summarization (extract first N sentences)
    
    Args:
        text: Input text
        max_sentences: Số câu tối đa trong summary
    
    Returns:
        Summary text
    """
    if not text:
        return ""
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first N sentences
    summary_sentences = sentences[:max_sentences]
    
    return '. '.join(summary_sentences) + '.' if summary_sentences else ""

