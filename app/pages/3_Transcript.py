"""
Transcript: xem, chỉnh sửa và xuất transcript.
"""
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.transcript_viewer import render_transcript_viewer
from app.components.subtitle_viewer import render_subtitle_viewer
from services.export_service import export_srt, export_vtt
from core.diarization import simple_speaker_segmentation, format_with_speakers

apply_custom_css()
st.set_page_config(page_title="Transcript - Vietnamese Speech to Text", page_icon="📄", layout="wide")

for k, v in [("transcript_text", ""), ("transcript_result", None), ("transcript_segments", [])]:
    st.session_state.setdefault(k, v)

render_page_header("Transcript", "Xem, chỉnh sửa và xuất transcript", "📄")

transcript = st.session_state.get("transcript_text") or ""
segments = st.session_state.get("transcript_segments") or []

if not transcript.strip():
    st.info("Chưa có transcript. Chạy Transcription trước.")
    if st.button("Đi tới Transcription", type="primary"):
        st.switch_page("pages/2_Transcription.py")
    st.stop()

edited, _ = render_transcript_viewer(transcript, "transcript_view")
st.session_state.transcript_text = edited

segs = segments or (st.session_state.transcript_result.get("segments", []) if st.session_state.transcript_result else [])

if segs:
    st.subheader("Subtitle (segment)")
    sub_mode = st.radio("Hiển thị", ["source", "translation", "dual"], horizontal=True, key="sub_mode")
    render_subtitle_viewer(segs, mode=sub_mode, show_confidence=any(s.get("confidence_asr") is not None for s in segs))
    c1, c2 = st.columns(2)
    with c1:
        dual = bool(segs and segs[0].get("translated_text"))
        srt_data, srt_name = export_srt(segs, "subtitles.srt", dual=dual)
        st.download_button("Tải SRT", srt_data, file_name=srt_name, mime="text/plain", key="dl_srt")
    with c2:
        vtt_data, vtt_name = export_vtt(segs, "subtitles.vtt", dual=dual)
        st.download_button("Tải VTT", vtt_data, file_name=vtt_name, mime="text/vtt", key="dl_vtt")

if st.checkbox("Áp dụng speaker diarization (phân biệt người nói)", key="diar"):
    segs_for_diar = st.session_state.transcript_result.get("segments", []) if st.session_state.transcript_result else []
    if segs_for_diar and st.session_state.get("audio_data") is not None:
        speaker_segs = simple_speaker_segmentation(
            st.session_state.audio_data,
            st.session_state.audio_sr,
            segs_for_diar,
            max_speakers=4,
        )
        st.subheader("Transcript theo speaker")
        st.text(format_with_speakers(speaker_segs))

st.download_button("Tải TXT", st.session_state.transcript_text.encode("utf-8"), file_name="transcript.txt", mime="text/plain", key="dl_txt")

render_footer()
