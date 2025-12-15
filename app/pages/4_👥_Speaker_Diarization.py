"""
Speaker Diarization Page
"""
import streamlit as st
import os
import sys
import pandas as pd
import altair as alt
from core.audio.audio_processor import chunk_signal

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.diarization.speaker_diarization import (
    simple_speaker_segmentation, format_with_speakers
)
from core.asr.transcription_service import format_transcript
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Ensure session_state keys exist when page is opened directly
for key, default in (
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_result", None),
    ("transcript_text", ""),
    ("speaker_segments", None),
):
    if key not in st.session_state:
        st.session_state[key] = default

# Render sidebar with logo
render_sidebar()

st.header("👥 Speaker Diarization")
if st.session_state.audio_data is None:
    st.warning("⚠️ Vui lòng upload audio file trước tại trang 'Upload & Record'")
elif st.session_state.transcript_result is None:
    st.warning("⚠️ Vui lòng transcribe audio trước tại trang 'Transcription'")
else:
    st.info("💡 Speaker diarization phân biệt các người nói khác nhau trong audio.")
    chunk_len = st.selectbox(
        "Chunk giả lập (fallback nếu thiếu timestamps)",
        [10, 15, 30, 45],
        index=1,
        help="Dùng để chia đoạn khi transcript không có timestamps",
    )
    
    if st.button("🔍 Phân tích Speaker", type="primary"):
        if 'segments' in st.session_state.transcript_result and st.session_state.transcript_result['segments']:
            base_segments = st.session_state.transcript_result['segments']
        else:
            # Tạo segments giả dựa trên chunking nếu không có timestamps
            ranges = chunk_signal(st.session_state.audio_data, st.session_state.audio_sr, int(chunk_len))
            base_segments = [{"start": s0 / st.session_state.audio_sr, "end": s1 / st.session_state.audio_sr, "text": ""} for s0, s1 in ranges]

            with st.spinner("Đang phân tích speaker..."):
                speaker_segments = simple_speaker_segmentation(
                    st.session_state.audio_data,
                    st.session_state.audio_sr,
                base_segments
                )
                
                if speaker_segments:
                st.session_state.speaker_segments = speaker_segments
                    st.session_state.transcript_text = format_with_speakers(speaker_segments)
                    st.success("✅ Đã phân tích speaker thành công!")
                    st.rerun()
                else:
                    st.warning("⚠️ Không thể phân tích speaker. Có thể do audio không có segments chi tiết.")
    
    # Hiển thị diarized transcript
    if st.session_state.transcript_text and any("Speaker" in line for line in st.session_state.transcript_text.split('\n')):
        st.subheader("📝 Diarized Transcript")
        st.text_area(
            "Transcript với speaker labels:",
            st.session_state.transcript_text,
            height=500,
            key="diarized_transcript"
        )
        
        # Speaker statistics
        st.subheader("📊 Speaker Statistics")
        lines = st.session_state.transcript_text.split('\n')
        speakers = {}
        for line in lines:
            if "Speaker" in line:
                speaker = line.split(":")[0].split("]")[-1].strip()
                if speaker not in speakers:
                    speakers[speaker] = 0
                speakers[speaker] += len(line.split())
        
        if speakers:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Số lượng speaker:**", len(speakers))
            with col2:
                st.write("**Tổng số từ:**", sum(speakers.values()))
            
            st.write("**Phân bố từ theo speaker:**")
            for speaker, word_count in speakers.items():
                st.write(f"- {speaker}: {word_count} từ")

        # Timeline chart
        if st.session_state.get("speaker_segments"):
            df = pd.DataFrame(st.session_state.speaker_segments)
            chart = alt.Chart(df).mark_bar().encode(
                x='start:Q',
                x2='end:Q',
                y='speaker:N',
                tooltip=['speaker', 'start', 'end', 'text']
            ).properties(height=200)
            st.subheader("⏱️ Speaker Timeline")
            st.altair_chart(chart, use_container_width=True)

