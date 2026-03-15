"""
Streaming ASR: real-time transcription via WebSocket.
Connect to API ws://host:8000/ws/transcribe; send PCM 16kHz 16-bit chunks, receive partial/final text.
"""

import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer

apply_custom_css()
st.set_page_config(page_title="Streaming ASR - EchoViet", page_icon="🔴", layout="wide")

render_page_header("Streaming ASR", "Real-time transcription via WebSocket + VAD", "🔴")

st.markdown("""
**Cách dùng:**
1. Chạy API: `uvicorn core.api.server:app --host 0.0.0.0 --port 8000`
2. Kết nối WebSocket: `ws://localhost:8000/ws/transcribe`
3. Gửi binary: chunks PCM 16-bit, 16 kHz, mono
4. Gửi text `flush` để xử lý buffer và nhận transcript
5. Nhận JSON: `{"type": "partial"|"final", "text": "..."}`

**VAD:** Silero VAD cắt segment có tiếng nói trước khi gửi Whisper.
""")

with st.expander("Ví dụ Python client"):
    st.code("""
import asyncio
import websockets
import numpy as np
import soundfile as sf

async def stream_transcribe(audio_path):
    y, sr = sf.read(audio_path)
    if sr != 16000:
        # resample to 16kHz
        from scipy import signal
        y = signal.resample(y, int(len(y) * 16000 / sr))
    # PCM 16-bit
    chunks = (y * 32767).astype(np.int16).tobytes()
    chunk_size = 16000 * 2  # 1 second
    async with websockets.connect("ws://localhost:8000/ws/transcribe") as ws:
        for i in range(0, len(chunks), chunk_size):
            await ws.send(chunks[i:i+chunk_size])
        await ws.send("flush")
        while True:
            msg = await ws.recv()
            # parse JSON and print text
            import json
            d = json.loads(msg)
            if d.get("text"):
                print(d["text"], end=" ", flush=True)
""", language="python")

render_footer()
