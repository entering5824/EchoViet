"""
Export: xuất transcript sang TXT, DOCX, PDF, JSON, SRT, VTT.
"""
import sys
from datetime import datetime
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from services.export_service import export_txt, export_docx, export_pdf, export_srt, export_vtt, export_json

apply_custom_css()
st.set_page_config(page_title="Export - Vietnamese Speech to Text", page_icon="📤", layout="wide")

for k, v in [("transcript_text", ""), ("audio_info", None), ("transcript_segments", [])]:
    st.session_state.setdefault(k, v)

render_page_header("Export", "Xuất transcript sang nhiều định dạng", "📤")

transcript = st.session_state.get("transcript_text") or ""
segments = st.session_state.get("transcript_segments") or []
audio_info = st.session_state.get("audio_info") or {}
duration = audio_info.get("duration") or 0

if not transcript.strip():
    st.info("Chưa có transcript. Chạy Transcription trước.")
    if st.button("Đi tới Transcription"):
        st.switch_page("pages/2_Transcription.py")
    st.stop()

meta = {
    "duration": duration,
    "word_count": len(transcript.split()),
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "segments_count": len(segments),
}

st.subheader("Document")
col1, col2, col3, col4 = st.columns(4)
with col1:
    data, fname = export_txt(transcript, "transcript.txt")
    st.download_button("Tải TXT", data, file_name=fname, mime="text/plain", key="dl_txt")
with col2:
    data, fname = export_docx(transcript, meta, "transcript.docx")
    st.download_button("Tải DOCX", data, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_docx")
with col3:
    data, fname = export_pdf(transcript, meta, "transcript.pdf")
    st.download_button("Tải PDF", data, file_name=fname, mime="application/pdf", key="dl_pdf")
with col4:
    data, fname = export_json(segments, transcript, meta, "transcript.json")
    st.download_button("Tải JSON", data, file_name=fname, mime="application/json", key="dl_json")

if segments:
    st.subheader("Subtitle")
    dual = bool(segments and segments[0].get("translated_text"))
    c1, c2 = st.columns(2)
    with c1:
        srt_data, srt_name = export_srt(segments, "subtitles.srt", dual=dual)
        st.download_button("Tải SRT", srt_data, file_name=srt_name, mime="text/plain", key="dl_srt")
    with c2:
        vtt_data, vtt_name = export_vtt(segments, "subtitles.vtt", dual=dual)
        st.download_button("Tải VTT", vtt_data, file_name=vtt_name, mime="text/vtt", key="dl_vtt")

render_footer()
