"""
Analytics: export transcript (TXT/DOCX/PDF), statistics, and optional settings/API info.
"""
import os
import sys
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from services.export_service import export_txt, export_docx, export_pdf, export_srt, export_vtt
from utils.metrics import compute_wer, compute_bleu

apply_custom_css()
st.set_page_config(page_title="Export & Analytics - Vietnamese Speech to Text", page_icon="📊", layout="wide")

for k, v in [("transcript_text", ""), ("audio_info", None), ("transcript_segments", [])]:
    st.session_state.setdefault(k, v)

render_page_header("Export & Analytics", "Xuất transcript và xem thống kê", "📊")

tab_export, tab_stats, tab_metrics, tab_info = st.tabs(["📤 Export", "📈 Thống kê", "📐 WER/BLEU", "ℹ️ Hệ thống"])

transcript = st.session_state.get("transcript_text") or ""
segments = st.session_state.get("transcript_segments") or []

with tab_export:
    if transcript.strip():
        st.subheader("Xuất file")
        meta = {}
        if st.session_state.get("audio_info"):
            meta["duration"] = st.session_state.audio_info.get("duration")
            meta["word_count"] = len(transcript.split())
            meta["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        col1, col2, col3 = st.columns(3)
        with col1:
            data, fname = export_txt(transcript, "transcript.txt")
            st.download_button("Tải TXT", data, file_name=fname, mime="text/plain")
        with col2:
            data, fname = export_docx(transcript, meta, "transcript.docx")
            st.download_button("Tải DOCX", data, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col3:
            data, fname = export_pdf(transcript, meta, "transcript.pdf")
            st.download_button("Tải PDF", data, file_name=fname, mime="application/pdf")
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
    else:
        st.info("Chưa có transcript. Chạy Transcription trước.")

with tab_stats:
    if transcript.strip():
        words = len(transcript.split())
        sents = max(1, transcript.count(".") + transcript.count("!") + transcript.count("?"))
        dur = (st.session_state.audio_info or {}).get("duration") or 0
        wpm = (words / (dur / 60.0)) if dur > 0 else 0
        st.metric("Số từ", words)
        st.metric("Số câu (ước lượng)", sents)
        st.metric("Thời lượng (s)", f"{dur:.1f}")
        st.metric("Từ/phút", f"{wpm:.1f}")
    else:
        st.info("Chưa có transcript.")

with tab_metrics:
    st.subheader("WER & BLEU")
    st.caption("So sánh reference (bản chuẩn) với hypothesis (output ASR hoặc dịch).")
    ref = st.text_area("Reference (bản chuẩn)", height=100, key="ref_metric")
    hyp = st.text_area("Hypothesis (output cần đánh giá)", height=100, key="hyp_metric")
    if st.button("Tính WER & BLEU", key="btn_metric"):
        if ref.strip() and hyp.strip():
            wer = compute_wer(ref, hyp)
            bleu = compute_bleu(ref, hyp)
            st.metric("WER (Word Error Rate)", f"{wer:.4f}")
            st.metric("BLEU", f"{bleu:.2f}")
        else:
            st.warning("Nhập cả reference và hypothesis.")

with tab_info:
    st.caption("Model: Whisper / Faster-Whisper. Dịch: NLLB, SeamlessM4T, M2M100. Pipeline: Upload → Record/Upload → Transcript → Export.")
    try:
        from services.audio_service import get_ffmpeg_info
        ok, msg = get_ffmpeg_info()
        st.write("FFmpeg:", msg)
    except Exception:
        st.write("FFmpeg: N/A")

render_footer()
