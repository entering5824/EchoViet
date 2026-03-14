"""Translation pipeline: stream buffer, segment/batch translate (NLLB, SeamlessM4T, M2M100)."""
import queue
from typing import List, Dict, Optional, Any, Iterator

from models.translation_model import (
    translate_batch as model_translate_batch,
    load_nllb,
    load_m2m100,
    load_seamless_m4t,
    TRANSLATION_BACKENDS,
)


class TranslationStreamBuffer:
    """Thread-safe queue of segments for translation. Consumer can pop or iterate."""

    def __init__(self, maxsize: int = 0):
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._closed = False

    def push(self, segment: Dict[str, Any]) -> None:
        if self._closed:
            return
        self._queue.put(segment)

    def pop(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_nowait(self) -> Optional[Dict[str, Any]]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def empty(self) -> bool:
        return self._queue.empty()

    def qsize(self) -> int:
        return self._queue.qsize()

    def close(self) -> None:
        self._closed = True
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        while not self._closed:
            seg = self.pop(timeout=0.5)
            if seg is not None:
                yield seg


def translate_segment(
    segment: Dict[str, Any],
    src_lang: str,
    tgt_lang: str,
    backend: str = "nllb",
    model_id: Optional[str] = None,
    model_obj: Any = None,
) -> Dict[str, Any]:
    """Translate one segment; returns segment with 'translated_text' (and optional confidence_translation)."""
    text = (segment.get("text") or "").strip()
    if not text:
        return {**segment, "translated_text": ""}
    translated = model_translate_batch(
        [text], src_lang, tgt_lang, backend=backend, model_id=model_id, model_obj=model_obj
    )
    out = {**segment, "translated_text": (translated[0] or "").strip()}
    return out


def translate_batch(
    segments: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    backend: str = "nllb",
    model_id: Optional[str] = None,
    model_obj: Any = None,
) -> List[Dict[str, Any]]:
    """Translate list of segments in one batch. Returns segments with 'translated_text'."""
    if not segments:
        return []
    texts = [(s.get("text") or "").strip() for s in segments]
    translated = model_translate_batch(
        texts, src_lang, tgt_lang, backend=backend, model_id=model_id, model_obj=model_obj
    )
    return [
        {**seg, "translated_text": (translated[i] or "").strip()}
        for i, seg in enumerate(segments)
    ]


def translate_segments_stream(
    segments: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    backend: str = "nllb",
    model_id: Optional[str] = None,
    batch_size: int = 4,
) -> List[Dict[str, Any]]:
    """
    Translate segments in small batches (low latency: don't wait for full list).
    Returns list of segments with 'translated_text', in same order.
    """
    if not segments:
        return []
    model_obj = None
    if backend == "nllb":
        model_obj = load_nllb(model_id or TRANSLATION_BACKENDS["nllb"]["default_id"])
    elif backend == "m2m100":
        model_obj = load_m2m100(model_id or TRANSLATION_BACKENDS["m2m100"]["default_id"])
    elif backend == "seamless_m4t":
        model_obj = load_seamless_m4t(model_id or TRANSLATION_BACKENDS["seamless_m4t"]["default_id"])
    result = []
    for i in range(0, len(segments), batch_size):
        chunk = segments[i : i + batch_size]
        result.extend(translate_batch(chunk, src_lang, tgt_lang, backend=backend, model_id=model_id, model_obj=model_obj))
    return result
