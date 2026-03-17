"""
Meeting transcript analysis: summary, action items extraction.
"""
import re
from typing import List, Optional


def extract_action_items_rule_based(text: str) -> List[str]:
    """
    Extract action items from transcript using rule-based patterns.
    Looks for Vietnamese/English phrases indicating tasks or commitments.
    """
    if not (text and text.strip()):
        return []

    # Patterns that often precede action items (Vietnamese + English)
    action_patterns = [
        r"(?:cần|phải|sẽ|nên)\s+(?:chuẩn bị|gửi|gửi|hoàn thành|làm|làm xong|kiểm tra|báo cáo|trình bày|họp|họp lại)\s+[^.!?]+[.!?]",
        r"(?:sẽ|sắp)\s+[^.!?]*(?:chuẩn bị|gửi|gửi|hoàn thành|kiểm tra|báo cáo)[^.!?]*[.!?]",
        r"(?:nhớ|đừng quên)\s+[^.!?]+[.!?]",
        r"(?:được giao|được phân công)\s+[^.!?]+[.!?]",
        r"(?:todo|to-do|action item)\s*:\s*[^.!?\n]+",
        r"(?:minh|lan|anh|chị|em|tôi)\s+[^.!?]*(?:chuẩn bị|gửi|gửi|hoàn thành|kiểm tra|báo cáo|làm)[^.!?]*[.!?]",
    ]

    results = []
    seen = set()
    text_lower = text.lower()

    for pattern in action_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            item = m.group(0).strip()
            # Clean and normalize
            item = re.sub(r"\s+", " ", item)
            if len(item) > 10 and item.lower() not in seen:
                seen.add(item.lower())
                results.append(item)

    # Fallback: split by sentence and look for action keywords
    if not results:
        action_keywords = [
            "cần", "phải", "sẽ", "chuẩn bị", "gửi", "hoàn thành", "kiểm tra",
            "báo cáo", "deadline", "assign", "will", "need to", "have to"
        ]
        sentences = re.split(r"[.!?]+", text)
        for s in sentences:
            s = s.strip()
            if len(s) < 15:
                continue
            if any(kw in s.lower() for kw in action_keywords) and s.lower() not in seen:
                seen.add(s.lower())
                results.append(s)

    return results[:15]


def generate_meeting_summary_gemini(text: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Generate meeting summary using Gemini (bullet points).
    Returns None if Gemini unavailable.
    """
    try:
        import os
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        if not api_key:
            return None
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        prompt = f"""Tóm tắt cuộc họp sau bằng 5 bullet points ngắn gọn (tiếng Việt). Chỉ trả về nội dung, không giải thích.

Transcript:
{text[:8000]}

Tóm tắt:"""
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception:
        pass
    return None
