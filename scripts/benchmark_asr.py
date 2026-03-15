"""
ASR Benchmark: compare Whisper small, Whisper large-v3, and wav2vec2 Vietnamese
on the same eval set. Reports WER, CER, and latency.
Usage: from EchoViet root, python scripts/benchmark_asr.py [--test-dir test_audio] [--output results/benchmark.csv]
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from jiwer import wer, cer

try:
    import torch
    import whisper
except ImportError:
    print("Install: pip install torch openai-whisper")
    sys.exit(1)


def load_reference_texts(test_dir: str) -> dict:
    refs = {}
    test_path = Path(test_dir)
    if not test_path.exists():
        test_path.mkdir(parents=True, exist_ok=True)
        print(f"Created {test_dir}. Add .wav/.mp3 files and same-named .txt references.")
        return refs
    for ext in [".wav", ".mp3", ".flac"]:
        for f in test_path.glob(f"*{ext}"):
            txt = f.with_suffix(".txt")
            if txt.exists():
                refs[f.name] = txt.read_text(encoding="utf-8").strip()
    return refs


def transcribe_whisper(audio_path: str, model_size: str) -> str:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, language="vi", task="transcribe", fp16=False)
    return (result.get("text") or "").strip()


def transcribe_wav2vec2_vi(audio_path: str) -> str:
    """wav2vec2 Vietnamese (e.g. nguyenvulebinh/wav2vec2-base-vietnamese-250h)."""
    try:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        import librosa
        model_id = "nguyenvulebinh/wav2vec2-base-vietnamese-250h"
        processor = Wav2Vec2Processor.from_pretrained(model_id)
        model = Wav2Vec2ForCTC.from_pretrained(model_id)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        y, sr = librosa.load(audio_path, sr=16000)
        inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(inputs.input_values.to(device)).logits
        ids = torch.argmax(logits, dim=-1)[0]
        return processor.decode(ids).strip()
    except Exception as e:
        print(f"  wav2vec2 error: {e}")
        return ""


def run_benchmark(test_dir: str, output_path: str):
    refs = load_reference_texts(test_dir)
    if not refs:
        print("No references found. Exiting.")
        return
    test_path = Path(test_dir)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}, files: {len(refs)}")

    models = [
        ("whisper_small", lambda p: transcribe_whisper(p, "small")),
        ("whisper_large_v3", lambda p: transcribe_whisper(p, "large-v3")),
        ("wav2vec2_vi", transcribe_wav2vec2_vi),
    ]

    rows = []
    for name, ref in refs.items():
        audio_path = str(test_path / name)
        if not os.path.exists(audio_path):
            continue
        row = {"file": name, "reference": ref}
        for model_name, transcribe_fn in models:
            t0 = time.perf_counter()
            hyp = transcribe_fn(audio_path)
            elapsed = time.perf_counter() - t0
            row[f"{model_name}_text"] = hyp
            row[f"{model_name}_wer"] = wer(ref, hyp) if hyp else 1.0
            row[f"{model_name}_cer"] = cer(ref, hyp) if hyp else 1.0
            row[f"{model_name}_latency_s"] = round(elapsed, 2)
        rows.append(row)

    df = pd.DataFrame(rows)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Saved {out}")

    # Summary
    print("\n--- Summary ---")
    for model_name, _ in models:
        w = df[f"{model_name}_wer"].mean()
        c = df[f"{model_name}_cer"].mean()
        l = df[f"{model_name}_latency_s"].mean()
        print(f"  {model_name}: WER={w:.4f}, CER={c:.4f}, latency_avg_s={l:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", default="test_audio")
    ap.add_argument("--output", default="results/benchmark_asr.csv")
    args = ap.parse_args()
    run_benchmark(args.test_dir, args.output)
