"""
Transcript: run ASR pipeline, view/edit transcript, optional speaker diarization.
"""
import os
import sys
import tempfile
import streamlit as st
import soundfile as sf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.transcript_viewer import render_transcript_viewer
from app.components.sidebar_config import render_sidebar_config
from app.components.subtitle_viewer import render_subtitle_viewer
from services.transcription_service import transcribe_with_pipeline
from services.export_service import export_txt, export_docx, export_srt, export_vtt
from services.translation_service import translate_segments
from core.diarization import simple_speaker_segmentation, format_with_speakers
from core.audio.ffmpeg_setup import ensure_ffmpeg
from utils.language_utils import detect_language

ensure_ffmpeg(silent=True)
apply_custom_css()
st.set_page_config(page_title="Transcription - Vietnamese Speech to Text", page_icon="📝", layout="wide")

for k, v in [("audio_data", None), ("audio_sr", None), ("audio_info", None), ("transcript_text", ""), ("transcript_result", None), ("transcript_segments", [])]:
    st.session_state.setdefault(k, v)
# Use recorded audio if no upload audio
if st.session_state.audio_data is None and st.session_state.get("recorded_audio_array") is not None:
    st.session_state.audio_data = st.session_state.recorded_audio_array
    st.session_state.audio_sr = st.session_state.get("recorded_sr", 16000)
    st.session_state.audio_info = {"duration": len(st.session_state.audio_data) / st.session_state.audio_sr}

config = render_sidebar_config("transcript")
render_page_header("Transcription", "Chạy ASR với Whisper, xem và chỉnh sửa transcript", "📝")

if st.session_state.audio_data is None:
    st.warning("Chưa có audio. Vui lòng upload ở trang Upload hoặc ghi âm ở trang Record.")
    if st.button("Đi tới Upload", type="primary"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

st.info(f"Duration: {st.session_state.audio_info.get('duration', 0):.1f}s | SR: {st.session_state.audio_sr} Hz")

with st.expander("Cấu hình ASR & Dịch"):
    asr_backend = st.selectbox("ASR backend", ["whisper", "faster_whisper"], key="asr_backend")
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
                detected = detect_language(audio_path=audio_path, use_faster_whisper=(asr_backend == "faster_whisper"))
                if detected:
                    language = detected
            result = transcribe_with_pipeline(
                audio_path,
                model_size=config["model_size"],
                language=language,
                vad_threshold=config["vad_threshold"],
                asr_backend=st.session_state.get("asr_backend", "whisper"),
            )
            if result:
                st.session_state.transcript_result = result
                st.session_state.transcript_text = result.get("text", "")
                segs = result.get("segments", [])
                st.session_state.transcript_segments = list(segs)
                if st.session_state.get("enable_translation") and segs:
                    with st.spinner("Đang dịch từng segment..."):
                        translated = translate_segments(
                            segs, src_lang=language, tgt_lang=st.session_state.get("tgt_lang", "en"),
                            backend=st.session_state.get("trans_backend", "nllb"),
                        )
                        st.session_state.transcript_segments = translated
                st.success("Transcribe xong.")
            else:
                st.error("Transcribe thất bại.")
        finally:
            if audio_path and audio_path != getattr(st.session_state, "audio_data", ""):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

if st.session_state.transcript_text:
    edited, _ = render_transcript_viewer(st.session_state.transcript_text, "transcript")
    st.session_state.transcript_text = edited
    segs = st.session_state.get("transcript_segments") or st.session_state.transcript_result.get("segments", []) if st.session_state.transcript_result else []
    if segs:
        st.subheader("Subtitle (segment)")
        sub_mode = st.radio("Hiển thị", ["source", "translation", "dual"], horizontal=True, key="sub_mode")
        render_subtitle_viewer(segs, mode=sub_mode, show_confidence=any(s.get("confidence_asr") is not None for s in segs))
        c1, c2 = st.columns(2)
        with c1:
            dual = bool(segs and (segs[0].get("translated_text")))
            srt_data, srt_name = export_srt(segs, "subtitles.srt", dual=dual)
            st.download_button("Tải SRT", srt_data, file_name=srt_name, mime="text/plain")
        with c2:
            vtt_data, vtt_name = export_vtt(segs, "subtitles.vtt", dual=dual)
            st.download_button("Tải VTT", vtt_data, file_name=vtt_name, mime="text/vtt")
    if st.checkbox("Áp dụng speaker diarization (phân biệt người nói)"):
        segs_for_diar = st.session_state.transcript_result.get("segments", []) if st.session_state.transcript_result else []
        if segs_for_diar and st.session_state.audio_data is not None:
            speaker_segs = simple_speaker_segmentation(
                st.session_state.audio_data,
                st.session_state.audio_sr,
                segs_for_diar,
                max_speakers=4,
            )
            st.subheader("Transcript theo speaker")
            st.text(format_with_speakers(speaker_segs))
    st.download_button("Tải TXT", st.session_state.transcript_text.encode("utf-8"), file_name="transcript.txt", mime="text/plain")

render_footer()
