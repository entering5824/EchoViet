"""
Transcription: chạy ASR pipeline, chuyển speech thành text.
"""
import os
import sys
import tempfile
import streamlit as st
import soundfile as sf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.sidebar_config import render_sidebar_config
from services.transcription_service import transcribe_with_pipeline
from core.audio.ffmpeg_setup import ensure_ffmpeg
from utils.language_utils import detect_language

ensure_ffmpeg(silent=True)
apply_custom_css()
st.set_page_config(page_title="Transcription - Vietnamese Speech to Text", page_icon="📝", layout="wide")

for k, v in [
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_text", ""),
    ("transcript_result", None),
    ("transcript_segments", []),
]:
    st.session_state.setdefault(k, v)

if st.session_state.audio_data is None and st.session_state.get("recorded_audio_array") is not None:
    st.session_state.audio_data = st.session_state.recorded_audio_array
    st.session_state.audio_sr = st.session_state.get("recorded_sr", 16000)
    st.session_state.audio_info = {"duration": len(st.session_state.audio_data) / st.session_state.audio_sr}

config = render_sidebar_config("transcript")
render_page_header("Transcription", "Chạy ASR để chuyển audio thành text", "📝")

if st.session_state.audio_data is None:
    st.warning("Chưa có audio. Vui lòng upload hoặc ghi âm ở trang Upload / Record.")
    if st.button("Đi tới Upload / Record", type="primary"):
        st.switch_page("pages/1_Upload_Record.py")
    st.stop()

st.info(f"Duration: {st.session_state.audio_info.get('duration', 0):.1f}s | SR: {st.session_state.audio_sr} Hz")

with st.expander("Cấu hình ASR & Dịch"):
    auto_lang = st.checkbox("Tự động phát hiện ngôn ngữ", value=False, key="auto_lang")
    enable_translation = st.checkbox("Bật dịch (low-latency)", value=False, key="enable_trans")
    tgt_lang = st.selectbox("Ngôn ngữ đích", ["en", "vi", "fr", "zh", "ja"], key="tgt_lang") if enable_translation else "en"
    trans_backend = st.selectbox("Model dịch", ["nllb", "m2m100", "seamless_m4t"], key="trans_backend") if enable_translation else "nllb"

if st.button("Chạy transcription", type="primary"):
    with st.spinner("Đang transcribe..."):
        audio_path = None
        try:
            if isinstance(st.session_state.audio_data, str) and os.path.isfile(st.session_state.audio_data):
                audio_path = st.session_state.audio_data
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp.close()
                sf.write(tmp.name, st.session_state.audio_data, st.session_state.audio_sr, subtype="PCM_16")
                audio_path = tmp.name
            language = config["language"]
            if st.session_state.get("auto_lang"):
                model_id = config.get("model_id", "whisper")
                use_fw = model_id in ("faster_whisper", "distil_whisper", "whisper_large_v3_turbo")
                detected = detect_language(audio_path=audio_path, use_faster_whisper=use_fw)
                if detected:
                    language = detected
            result = transcribe_with_pipeline(
                audio_path,
                model_size=config["model_size"],
                language=language,
                vad_threshold=config["vad_threshold"],
                model_id=config.get("model_id", "whisper"),
            )
            if result:
                st.session_state.transcript_result = result
                st.session_state.transcript_text = result.get("text", "")
                segs = result.get("segments", [])
                st.session_state.transcript_segments = list(segs)
                if st.session_state.get("enable_translation") and segs:
                    with st.spinner("Đang dịch từng segment..."):
                        from services.translation_service import translate_segments
                        translated = translate_segments(
                            segs, src_lang=language, tgt_lang=st.session_state.get("tgt_lang", "en"),
                            backend=st.session_state.get("trans_backend", "nllb"),
                        )
                        st.session_state.transcript_segments = translated
                st.success("Transcribe xong.")
                st.rerun()
            else:
                st.error("Transcribe thất bại.")
        finally:
            if audio_path and audio_path != getattr(st.session_state, "audio_data", ""):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

if st.session_state.transcript_text:
    st.success("Đã có transcript.")
    if st.button("Xem transcript →"):
        st.switch_page("pages/3_Transcript.py")

render_footer()
