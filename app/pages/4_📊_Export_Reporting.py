"""
Export & Reporting Page
Xuất transcript và hiển thị statistics với visualization nâng cao
"""
import streamlit as st
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
from app.components.statistics_display import calculate_statistics
from app.components.footer import render_footer
from core.utils.export import export_txt, export_docx, export_pdf

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="Export & Reporting - Vietnamese Speech to Text",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
for key, default in (
    ("transcript_text", ""),
    ("transcript_result", None),
    ("audio_info", None),
    ("speaker_segments", []),
):
    st.session_state.setdefault(key, default)

render_page_header("Export & Reporting", "Xuất transcript và xem thống kê chi tiết", "📊")

# Check if transcript is available
if not st.session_state.transcript_text:
    st.warning("⚠️ Vui lòng chạy transcription trước tại trang 'Transcription'")
    if st.button("📝 Go to Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
else:
    # Calculate statistics
    duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
    stats = calculate_statistics(
        st.session_state.transcript_text,
        duration,
        st.session_state.speaker_segments if st.session_state.speaker_segments else None
    )
    
    # Display statistics with enhanced visualization
    st.subheader("📊 Statistics")
    
    # Main metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{stats['word_count']:,}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Số từ</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        duration_min = stats['duration'] / 60
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{duration_min:.2f} min</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Thời lượng audio</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{stats['words_per_minute']:.1f}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Tốc độ nói (WPM)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{stats['sentence_count']:,}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Số câu</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Speaker statistics with visual charts
    if stats.get("speakers", 0) > 0:
        st.markdown("---")
        st.subheader("👥 Thống kê theo người nói")
        
        try:
            import pandas as pd
            import plotly.express as px
            
            # Prepare data for visualization
            speaker_data = []
            for speaker, speaker_stat in stats["speaker_stats"].items():
                speaker_data.append({
                    "Speaker": speaker,
                    "Thời gian (s)": f"{speaker_stat['duration']:.1f}",
                    "Số từ": speaker_stat['word_count'],
                    "WPM": f"{speaker_stat['words_per_minute']:.1f}",
                    "Segments": speaker_stat['segments']
                })
            
            df_speakers = pd.DataFrame(speaker_data)
            st.dataframe(df_speakers, use_container_width=True, hide_index=True)
            
            # Visual comparison
            col1, col2 = st.columns(2)
            
            with col1:
                # Duration per speaker (bar chart)
                durations = {k: v['duration'] for k, v in stats["speaker_stats"].items()}
                fig_duration = px.bar(
                    x=list(durations.keys()),
                    y=list(durations.values()),
                    title="Thời gian nói theo người",
                    labels={"x": "Speaker", "y": "Thời gian (giây)"}
                )
                st.plotly_chart(fig_duration, use_container_width=True)
            
            with col2:
                # Word count per speaker
                word_counts = {k: v['word_count'] for k, v in stats["speaker_stats"].items()}
                fig_words = px.bar(
                    x=list(word_counts.keys()),
                    y=list(word_counts.values()),
                    title="Số từ theo người",
                    labels={"x": "Speaker", "y": "Số từ"}
                )
                st.plotly_chart(fig_words, use_container_width=True)
        except ImportError:
            # Fallback if plotly/pandas not available
            for speaker, speaker_stat in stats["speaker_stats"].items():
                with st.expander(f"{speaker} - {speaker_stat['word_count']} từ"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Thời gian nói", f"{speaker_stat['duration']:.2f}s")
                    with col2:
                        st.metric("Số segments", speaker_stat['segments'])
                    with col3:
                        st.metric("WPM", f"{speaker_stat['words_per_minute']:.1f}")
    else:
        # Show basic statistics if no speaker diarization
        st.info("💡 Chạy Speaker Diarization để xem thống kê chi tiết theo người nói")
    
    # Export section
    st.markdown("---")
    st.subheader("📤 Export Transcript")
    
    # Prepare metadata
    metadata = {
        "duration": duration,
        "word_count": stats["word_count"],
        "sentence_count": stats["sentence_count"],
        "words_per_minute": stats["words_per_minute"],
        "timestamp": st.session_state.transcript_result.get("timestamp") if st.session_state.transcript_result else None
    }
    
    if st.session_state.speaker_segments:
        metadata["speakers"] = stats["speakers"]
        metadata["speaker_stats"] = stats["speaker_stats"]
    
    # Export options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # TXT export
        txt_data, txt_filename = export_txt(st.session_state.transcript_text, "transcript.txt")
        st.download_button(
            "⬇️ Download TXT",
            data=txt_data,
            file_name=txt_filename,
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        # DOCX export
        docx_data, docx_filename = export_docx(st.session_state.transcript_text, metadata, "transcript.docx")
        st.download_button(
            "⬇️ Download DOCX",
            data=docx_data,
            file_name=docx_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    with col3:
        # PDF export
        pdf_data, pdf_filename = export_pdf(st.session_state.transcript_text, metadata, "transcript.pdf")
        st.download_button(
            "⬇️ Download PDF",
            data=pdf_data,
            file_name=pdf_filename,
            mime="application/pdf",
            use_container_width=True
        )
    
    with col4:
        # JSON export
        json_data = {
            "transcript": st.session_state.transcript_text,
            "metadata": metadata,
            "statistics": stats
        }
        if st.session_state.speaker_segments:
            json_data["speaker_segments"] = st.session_state.speaker_segments
        
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ Download JSON",
            data=json_str.encode('utf-8'),
            file_name="transcript.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Preview transcript with better layout
    st.markdown("---")
    st.subheader("📝 Xem Trước Transcript")
    
    preview_mode = st.radio(
        "Chế độ xem:",
        ["Toàn bộ", "Rút gọn (500 ký tự đầu)"],
        horizontal=True,
        help="Chọn cách hiển thị transcript"
    )
    
    if preview_mode == "Rút gọn (500 ký tự đầu)":
        preview_text = st.session_state.transcript_text[:500] + "..." if len(st.session_state.transcript_text) > 500 else st.session_state.transcript_text
        st.text_area(
            "Transcript (preview):",
            preview_text,
            height=200,
            key="export_preview_short",
            help=f"Hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu. Tổng: {len(st.session_state.transcript_text)} ký tự"
        )
        st.caption(f"💡 Đang hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu. Chọn 'Toàn bộ' để xem đầy đủ.")
    else:
        st.text_area(
            "Transcript:",
            st.session_state.transcript_text,
            height=300,
            key="export_preview_full",
            help="Xem toàn bộ transcript trước khi export"
        )

# ===== Footer =====
render_footer()

