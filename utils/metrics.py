"""Evaluation metrics: WER (transcription), BLEU (translation)."""
from typing import List, Tuple, Union


def compute_wer(reference: str, hypothesis: str) -> float:
    """
    Word Error Rate: reference vs hypothesis (for transcription evaluation).
    Returns WER in [0, +inf); lower is better.
    """
    try:
        import jiwer
        return jiwer.wer(reference, hypothesis)
    except ImportError:
        raise ImportError("Install jiwer: pip install jiwer")


def compute_wer_batch(
    pairs: List[Tuple[str, str]],
) -> float:
    """Average WER over list of (reference, hypothesis) pairs."""
    if not pairs:
        return 0.0
    wers = [compute_wer(ref, hyp) for ref, hyp in pairs]
    return sum(wers) / len(wers)


def compute_bleu(reference: str, hypothesis: str) -> float:
    """
    BLEU score: reference vs hypothesis (for translation evaluation).
    Returns BLEU in [0, 100] (sacrebleu convention); higher is better.
    """
    try:
        import sacrebleu
        bleu = sacrebleu.sentence_bleu(hypothesis, [reference])
        return bleu.score
    except ImportError:
        try:
            from nltk.translate.bleu_score import sentence_bleu
            from nltk.tokenize import word_tokenize
            ref_tok = word_tokenize(reference.lower())
            hyp_tok = word_tokenize(hypothesis.lower())
            return sentence_bleu([ref_tok], hyp_tok) * 100.0
        except ImportError:
            raise ImportError("Install sacrebleu or nltk: pip install sacrebleu")


def compute_bleu_batch(
    pairs: List[Tuple[str, str]],
) -> float:
    """Corpus BLEU over list of (reference, hypothesis) pairs. Returns 0-100."""
    if not pairs:
        return 0.0
    try:
        import sacrebleu
        refs = [[p[0]] for p in pairs]
        hyps = [p[1] for p in pairs]
        bleu = sacrebleu.corpus_bleu(hyps, refs)
        return bleu.score
    except ImportError:
        scores = [compute_bleu(ref, hyp) for ref, hyp in pairs]
        return sum(scores) / len(scores)
