"""
Vietnamese punctuation restoration for ASR output.
Whisper output: 'xin chào tôi là tú hôm nay tôi ...'
Restored: 'Xin chào, tôi là Tú. Hôm nay tôi...'
Uses rule-based by default; optional VFastPunct or similar model when available.
"""

import re
from typing import Optional

_restore_fn = None


def _rule_based_restore(text: str) -> str:
    """Simple rules: capitalize sentence start and after .!?; ensure period at end."""
    if not text or not text.strip():
        return text
    text = text.strip()
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    # Capitalize after . ! ?
    for sep in ".!?":
        parts = text.split(sep)
        out = []
        for i, p in enumerate(parts):
            p = p.strip()
            if p and i > 0:
                p = p[0].upper() + p[1:] if len(p) > 1 else p.upper()
            out.append(p)
        text = (sep + " ").join(out).replace(sep + " " + sep, sep + " ")
    # Ensure period at end if not ? !
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        text = text + "."
    return text


def _try_vfastpunct(text: str) -> Optional[str]:
    """Use VFastPunct if installed."""
    try:
        from vfastpunct import RestorePuncts
        rp = RestorePuncts()
        return rp.punctuate(text)
    except Exception:
        return None


def restore_punctuation(text: str, use_model: bool = True) -> str:
    """
    Restore punctuation and capitalization for Vietnamese ASR output.
    If use_model=True, tries VFastPunct when available; else rule-based.
    """
    if not text or not text.strip():
        return text
    if use_model:
        out = _try_vfastpunct(text)
        if out is not None:
            return out
    return _rule_based_restore(text)
