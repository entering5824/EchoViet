"""
Speaker & Text Enhancement Page
Combined page: Speaker Diarization + AI Text Enhancement
Làm transcript "đẹp & dùng được"
"""
import streamlit as st
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from app.components.diarization_timeline import render_diarization_timeline
from core.diarization.speaker_diarization import (
    simple_speaker_segmentation, format_with_speakers, format_time
)
from core.nlp.post_processing import format_text, correct_punctuation, capitalize_sentences
from core.nlp.keyword_extraction import extract_keywords, simple_summarize
from core.utils.export import export_docx, export_txt
from core.audio.ffmpeg_setup import ensure_ffmpeg

# Setup FFmpeg
ensure_ffmpeg(silent=True)

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="Speaker & Enhancement - Vietnamese Speech to Text",
    page_icon="✨",
    layout="wide"
)

# Initialize session state
for key, default in (
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_text", ""),
    ("transcript_segments", []),
    ("speaker_segments", []),
    ("transcript_enhanced", ""),
):
    st.session_state.setdefault(key, default)

st.header("✨ Speaker & Text Enhancement")
st.caption("Phân biệt người nói và làm sạch văn bản với AI")

# Check prerequisites
if not st.session_state.transcript_text:
    st.warning("⚠️ Vui lòng chạy transcription trước tại trang 'Transcription'")
    if st.button("📝 Go to Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
    st.stop()

st.info("✅ Transcript đã sẵn sàng cho enhancement")

# Tabs for Speaker Diarization and Text Enhancement
tab1, tab2 = st.tabs(["👥 Speaker Diarization", "✨ AI Text Enhancement"])

# ===== TAB 1: Speaker Diarization =====
with tab1:
    st.subheader("👥 Speaker Diarization")
    st.caption("Phân biệt và gán nhãn người nói")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Cần audio data để chạy diarization. Vui lòng upload audio trước.")
        if st.button("🎤 Go to Audio Input", type="primary"):
            st.switch_page("pages/1_🎤_Audio_Input.py")
    else:
        # Simple settings (hide technical VAD parameters)
        col1, col2 = st.columns(2)
        
        with col1:
            max_speakers = st.number_input(
                "Số lượng người nói",
                min_value=1,
                max_value=10,
                value=4,
                help="Số lượng người nói dự kiến trong audio"
            )
        
        with col2:
            st.info("💡 Diarization sử dụng energy-based segmentation. Cài đặt nâng cao có trong Advanced Settings.")
        
        # Run diarization
        if st.button("🚀 Chạy Speaker Diarization", type="primary", use_container_width=True):
            with st.spinner("Đang phân tích speaker..."):
                try:
                    # Use simple segmentation
                    speaker_segments = simple_speaker_segmentation(
                        st.session_state.audio_data,
                        st.session_state.audio_sr,
                        st.session_state.transcript_segments if st.session_state.transcript_segments else [],
                        min_silence_duration=0.5
                    )
                    
                    if speaker_segments:
                        st.session_state.speaker_segments = speaker_segments
                        num_speakers = len(set(seg.get('speaker') for seg in speaker_segments))
                        st.success(f"✅ Đã phát hiện {num_speakers} người nói!")
                    else:
                        st.warning("⚠️ Không thể phân biệt speaker. Có thể do audio quá ngắn hoặc chỉ có 1 người nói.")
                except Exception as e:
                    st.error(f"❌ Lỗi khi chạy diarization: {str(e)}")
                    import traceback
                    with st.expander("🔍 Chi tiết lỗi"):
                        st.code(traceback.format_exc())
        
        # Display results
        if st.session_state.speaker_segments:
            st.markdown("---")
            st.subheader("📊 Diarization Results")
            
            # Timeline visualization
            duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
            render_diarization_timeline(st.session_state.speaker_segments, duration)
            
            # Transcript with speakers
            st.subheader("📝 Transcript với Speaker Labels")
            formatted_transcript = format_with_speakers(st.session_state.speaker_segments)
            st.text_area(
                "Transcript với speakers:",
                formatted_transcript,
                height=300,
                key="diarized_transcript"
            )
            
            # Statistics
            speakers = set(seg.get('speaker') for seg in st.session_state.speaker_segments)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Số người nói", len(speakers))
            
            with col2:
                total_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in st.session_state.speaker_segments)
                st.metric("Tổng thời gian nói", f"{total_duration:.1f}s")
            
            with col3:
                st.metric("Số segments", len(st.session_state.speaker_segments))
            
            # Update transcript text with speaker labels
            if st.button("💾 Áp dụng Speaker Labels vào Transcript", type="primary"):
                st.session_state.transcript_text = formatted_transcript
                st.success("✅ Đã cập nhật transcript với speaker labels!")
                st.rerun()

# ===== TAB 2: AI Text Enhancement =====
with tab2:
    st.subheader("✨ AI Text Enhancement")
    st.caption("Làm sạch và cải thiện văn bản với AI")
    
    # Display original transcript
    st.markdown("#### 📝 Original Transcript")
    st.text_area(
        "Original:",
        st.session_state.transcript_text,
        height=200,
        key="original_transcript_enhance",
        disabled=True
    )
    
    # Post-processing options
    st.markdown("#### 🔧 Enhancement Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_punctuation = st.checkbox("Tự động sửa dấu câu", value=True)
        capitalize_sent = st.checkbox("Viết hoa đầu câu", value=True)
        remove_spaces = st.checkbox("Loại bỏ khoảng trắng thừa", value=True)
    
    with col2:
        extract_keywords_enabled = st.checkbox("Extract keywords", value=False)
        summarize_enabled = st.checkbox("Tạo summary", value=False)
        num_keywords = st.number_input(
            "Số keywords",
            min_value=5,
            max_value=50,
            value=10,
            disabled=not extract_keywords_enabled
        )
        num_sentences = st.number_input(
            "Số câu trong summary",
            min_value=1,
            max_value=10,
            value=3,
            disabled=not summarize_enabled
        )
    
    # Apply post-processing
    if st.button("✨ Apply AI Enhancement", type="primary", use_container_width=True):
        with st.spinner("Đang xử lý với AI..."):
            # Format text
            formatting_options = {
                "punctuation": auto_punctuation,
                "capitalize": capitalize_sent,
                "remove_extra_spaces": remove_spaces
            }
            
            enhanced_text = format_text(st.session_state.transcript_text, formatting_options)
            st.session_state.transcript_enhanced = enhanced_text
            
            st.success("✅ Đã xử lý thành công!")
            st.rerun()
    
    # Display enhanced transcript
    if st.session_state.transcript_enhanced:
        st.markdown("---")
        st.subheader("✨ Enhanced Transcript")
        
        enhanced_text = st.text_area(
            "Enhanced:",
            st.session_state.transcript_enhanced,
            height=300,
            key="enhanced_transcript_display"
        )
        
        if st.button("💾 Lưu Enhanced Transcript", type="primary"):
            st.session_state.transcript_text = enhanced_text
            st.session_state.transcript_enhanced = ""
            st.success("✅ Đã lưu enhanced transcript!")
            st.rerun()
        
        # Keywords
        if extract_keywords_enabled:
            st.markdown("---")
            st.subheader("🔑 Keywords")
            keywords = extract_keywords(enhanced_text, top_k=num_keywords)
            if keywords:
                st.write(", ".join([f"**{kw}**" for kw in keywords]))
            else:
                st.info("Không tìm thấy keywords")
        
        # Summary
        if summarize_enabled:
            st.markdown("---")
            st.subheader("📄 Summary")
            summary = simple_summarize(enhanced_text, max_sentences=num_sentences)
            if summary:
                st.info(summary)
            else:
                st.info("Không thể tạo summary")

# ===== Navigation =====
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Go to Export & Report", use_container_width=True):
        st.switch_page("pages/4_📊_Export_Reporting.py")

with col2:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("pages/0_🏠_Home_Dashboard.py")

