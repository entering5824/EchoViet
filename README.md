# EchoViet

**Vietnamese Speech-to-Text and Automatic Meeting Transcription** — End-to-end ASR pipeline with Whisper, Streamlit UI, FastAPI serving, speaker diarization, and export (TXT, DOCX, PDF).

---

## Problem Statement

- **Real-world problem**: Converting Vietnamese speech (meetings, interviews, presentations) into accurate, editable text is time-consuming and error-prone when done manually. Organizations need searchable transcripts and structured exports for compliance and knowledge reuse.
- **Why it matters**: Enables faster meeting summaries, accessible content, and analytics on spoken data. Vietnamese is low-resource for ASR compared to English, so using a strong multilingual model (Whisper) with a dedicated workflow is important.
- **Constraints**: Long-form audio increases latency and memory (Whisper-large ~10GB RAM); CPU-only environments are slower; first run requires internet to download models; user type ranges from end-users (upload/export) to technical users (evaluation, WER/CER).

---

## System Architecture

```
User → Streamlit UI (app/) → core/ (ASR, audio, diarization, export)
         ↓                           ↓
    FastAPI (optional)          Whisper / PhoWhisper
         ↓                           ↓
    POST /transcribe            FFmpeg (imageio-ffmpeg), Librosa
         ↓
    JSON: text, segments, language
```

- **Streamlit**: Web UI — upload, preprocessing, model choice (tiny→large), transcription, diarization, export, analytics.
- **FastAPI** (`core/api/server.py`): REST API for programmatic transcription (`POST /transcribe`), health check.
- **Whisper**: Transformer-based ASR; model sizes (tiny, base, small, medium, large) trade off speed vs accuracy.
- **FFmpeg**: Handled via `imageio-ffmpeg` for portability (no system FFmpeg required on Streamlit Cloud).
- **No separate DB/vector store**: Session state and file-based export only.

---

## Key Features

### AI Features

- **Model**: Whisper (OpenAI) for Vietnamese ASR; optional PhoWhisper comparison in evaluation.
- **Inference**: Batch and single-file transcription with segment timestamps.
- **Evaluation**: WER/CER via `jiwer` when reference transcripts exist; report to `docs/model_comparison.md`.
- **Speaker diarization**: Optional simple diarization (env `DIARIZATION_ENABLED`).

### Application Features

- **Upload**: WAV, MP3, FLAC, M4A, OGG.
- **Preprocessing**: Normalize, noise reduction, VAD-related options.
- **Dashboard**: Waveform/spectrogram, statistics (word count, WPM, duration).
- **Export**: TXT, DOCX, PDF.
- **Real-time**: Optional streaming demo (audio-recorder-streamlit).

### Engineering Features

- **Config**: Env-based (e.g. `USE_GPU`, `DIARIZATION_ENABLED`, `WER_CER_ENABLED`); settings export.
- **Docker**: Dockerfile and docker-compose for containerized run.
- **Logging**: Standard Python logging; error handling and user-facing messages.

---

## Model & Methodology

- **Algorithm**: Whisper (Transformer encoder–decoder, multilingual).
- **Training**: Pretrained; no custom training in this repo.
- **Evaluation metrics**: WER (Word Error Rate), CER (Character Error Rate) via `jiwer`; optional per-file and mean±std in evaluation script (`core/asr/evaluate_models.py`).
- **Sizes**: tiny, base, small, medium, large — recommend **base** for Vietnamese speed/accuracy balance.

---

## Results

- **Metrics**: WER and CER depend on dataset and model size. Run evaluation with reference transcripts in `test_audio/`; report is written to `docs/model_comparison.md`.
- **Latency**: Depends on length and model (e.g. base ~150MB; large needs ~10GB RAM). GPU recommended for long files.
- *(Run `core/asr/evaluate_models.py` with paired audio + `.txt` references to generate metrics.)*

---

## Project Structure

```
.
├── app/                    # UI: Streamlit
│   ├── main.py             # Entry point
│   ├── components/         # Sidebar, layout
│   └── pages/              # Home, Audio Input, Transcription, Diarization, Export, Settings, Analysis, API
├── core/
│   ├── api/                # FastAPI server
│   ├── asr/                # transcription_service, evaluate_models, model_manager
│   ├── audio/               # audio_processor, ffmpeg_setup
│   ├── diarization/        # speaker_diarization
│   ├── nlp/                # post_processing, keyword_extraction
│   └── utils/              # export, settings
├── export/                 # Export helpers
├── assets/
├── docs/                   # architecture, model_comparison (generated)
├── scripts/
├── requirements.txt
└── README.md
```

---

## Installation

### Backend / app (Python)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

- **Python**: 3.9–3.10 recommended (Streamlit Cloud). 3.11+ may have compatibility issues with Whisper.
- **FFmpeg**: Portable via `imageio-ffmpeg`; optional system FFmpeg (e.g. `choco install ffmpeg` on Windows).

---

## Usage

### Web UI

```bash
streamlit run app/main.py
```

Open `http://localhost:8501`. Use sidebar pages: Home → Audio Input → Transcription → (Diarization) → Export → Settings / Analysis / API.

### API

```bash
uvicorn core.api.server:app --host 0.0.0.0 --port 8000
```

- `GET /health` — Liveness.
- `POST /transcribe` — Form-data: `file`, optional `diarization`; response: `{ "text", "language", "segments" }`.

### Evaluation (WER/CER)

Run evaluation script with audio files and matching `.txt` reference files in `test_audio/`; output in `docs/model_comparison.md`.

---

## Deployment

- **Streamlit Cloud**: Main file path `app/main.py`; see `DEPLOYMENT.md`.
- **Docker**: `docker build -t vietnamese-stt:latest .` then `docker run -d -p 8501:8501 vietnamese-stt:latest` or `docker-compose up -d`.

---

## Future Improvements

- Quantization / smaller models for lower memory and latency.
- Caching of model loads and repeated segments.
- Stronger speaker diarization (e.g. pyannote).
- Optional LLM-based punctuation/grammar (e.g. Gemini) as a post-step.
