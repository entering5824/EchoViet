"""Orchestrate translation: receive segments from transcription, translate (batch/stream), return with translated_text."""
from typing import List, Dict, Optional, Any

from core.translation import (
    TranslationStreamBuffer,
    translate_segment,
    translate_batch,
    translate_segments_stream,
)


def translate_segments(
    segments: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    backend: str = "nllb",
    model_id: Optional[str] = None,
    batch_size: int = 4,
) -> List[Dict[str, Any]]:
    """
    Translate segments (from transcription pipeline). Returns same list with 'translated_text' on each.
    Uses batch translation for efficiency; batch_size controls chunk size for low-latency flow.
    """
    if not segments:
        return []
    return translate_segments_stream(
        segments,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        backend=backend,
        model_id=model_id,
        batch_size=batch_size,
    )


def run_translation_worker(
    buffer: TranslationStreamBuffer,
    output_list: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    backend: str = "nllb",
    model_id: Optional[str] = None,
    batch_size: int = 4,
) -> None:
    """
    Worker: pull from buffer, translate in batches, append to output_list in order.
    Call from a thread while transcriber pushes to buffer. output_list should be thread-safe (e.g. list with lock).
    """
    pending: List[Dict[str, Any]] = []
    while True:
        seg = buffer.pop(timeout=0.5)
        if seg is not None:
            pending.append(seg)
        if len(pending) >= batch_size or (seg is None and pending):
            if pending:
                translated = translate_segments_stream(
                    pending, src_lang, tgt_lang, backend=backend, model_id=model_id, batch_size=batch_size
                )
                output_list.extend(translated)
                pending = []
        if seg is None and buffer.empty():
            if pending:
                translated = translate_segments_stream(
                    pending, src_lang, tgt_lang, backend=backend, model_id=model_id, batch_size=batch_size
                )
                output_list.extend(translated)
            break
