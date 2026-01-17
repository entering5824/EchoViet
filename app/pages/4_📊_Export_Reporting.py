"""
Export & Reporting Page
Export transcript and display statistics with advanced visualization
"""
import streamlit as st
import os
import sys
import json
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple

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

render_page_header("Export & Reporting", "Export transcript and view detailed statistics", "📊")

# Helper functions
def validate_transcript(transcript: str) -> Tuple[bool, Optional[str]]:
    """Validate transcript before export"""
    if not transcript or not transcript.strip():
        return False, "Transcript is empty"
    if len(transcript) < 10:
        return False, "Transcript is too short (minimum 10 characters)"
    return True, None

def safe_export_txt(transcript: str, filename: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Safely export to TXT with error handling"""
    try:
        is_valid, error_msg = validate_transcript(transcript)
        if not is_valid:
            return None, None, error_msg
        data, fname = export_txt(transcript, filename)
        return data, fname, None
    except Exception as e:
        return None, None, f"Error exporting TXT: {str(e)}"

def safe_export_docx(transcript: str, metadata: Dict, filename: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Safely export to DOCX with error handling"""
    try:
        is_valid, error_msg = validate_transcript(transcript)
        if not is_valid:
            return None, None, error_msg
        data, fname = export_docx(transcript, metadata, filename)
        return data, fname, None
    except Exception as e:
        return None, None, f"Error exporting DOCX: {str(e)}"

def safe_export_pdf(transcript: str, metadata: Dict, filename: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Safely export to PDF with error handling"""
    try:
        is_valid, error_msg = validate_transcript(transcript)
        if not is_valid:
            return None, None, error_msg
        data, fname = export_pdf(transcript, metadata, filename)
        return data, fname, None
    except Exception as e:
        return None, None, f"Error exporting PDF: {str(e)}"

def export_statistics_csv(stats: Dict, filename: str = "statistics.csv") -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Export statistics to CSV"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Metric", "Value"])
        
        # Write main stats
        writer.writerow(["Word Count", stats.get("word_count", 0)])
        writer.writerow(["Sentence Count", stats.get("sentence_count", 0)])
        writer.writerow(["Duration (seconds)", stats.get("duration", 0)])
        writer.writerow(["Words Per Minute", f"{stats.get('words_per_minute', 0):.2f}"])
        writer.writerow(["Characters", stats.get("character_count", 0)])
        
        # Write speaker stats if available
        if stats.get("speakers", 0) > 0:
            writer.writerow([])
            writer.writerow(["Speaker Statistics"])
            writer.writerow(["Speaker", "Duration (s)", "Words", "WPM", "Segments"])
            for speaker, speaker_stat in stats.get("speaker_stats", {}).items():
                writer.writerow([
                    speaker,
                    f"{speaker_stat['duration']:.2f}",
                    speaker_stat['word_count'],
                    f"{speaker_stat['words_per_minute']:.2f}",
                    speaker_stat['segments']
                ])
        
        csv_data = output.getvalue().encode('utf-8')
        return csv_data, filename, None
    except Exception as e:
        return None, None, f"Error exporting CSV: {str(e)}"

# Check if transcript is available
if not st.session_state.transcript_text:
    st.warning("⚠️ Vui lòng chạy transcription trước tại trang 'Transcription'")
    if st.button("📝 Đi đến Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
else:
    # Calculate statistics
    duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
    stats = calculate_statistics(
        st.session_state.transcript_text,
        duration,
        st.session_state.speaker_segments if st.session_state.speaker_segments else None
    )
    
    # Validate transcript
    is_valid, validation_error = validate_transcript(st.session_state.transcript_text)
    if not is_valid:
        st.error(f"❌ {validation_error}")
        st.info("💡 Vui lòng quay lại trang Transcription để tạo transcript hợp lệ")
        st.stop()
    
    # Display statistics with enhanced visualization
    st.subheader("📊 Thống kê")
    
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
        duration_min = stats['duration'] / 60 if stats['duration'] > 0 else 0
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{duration_min:.2f} phút</h3>
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
                    "Người nói": speaker,
                    "Thời gian (s)": f"{speaker_stat['duration']:.1f}",
                    "Số từ": speaker_stat['word_count'],
                    "WPM": f"{speaker_stat['words_per_minute']:.1f}",
                    "Số segments": speaker_stat['segments']
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
                    labels={"x": "Người nói", "y": "Thời gian (giây)"},
                    color=list(durations.keys()),
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_duration.update_layout(showlegend=False)
                st.plotly_chart(fig_duration, use_container_width=True)
            
            with col2:
                # Word count per speaker
                word_counts = {k: v['word_count'] for k, v in stats["speaker_stats"].items()}
                fig_words = px.bar(
                    x=list(word_counts.keys()),
                    y=list(word_counts.values()),
                    title="Số từ theo người",
                    labels={"x": "Người nói", "y": "Số từ"},
                    color=list(word_counts.keys()),
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_words.update_layout(showlegend=False)
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
    st.subheader("📤 Xuất Transcript")
    
    # Prepare metadata
    metadata = {
        "duration": duration,
        "word_count": stats["word_count"],
        "sentence_count": stats["sentence_count"],
        "words_per_minute": stats["words_per_minute"],
        "timestamp": st.session_state.transcript_result.get("timestamp") if st.session_state.transcript_result else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if st.session_state.speaker_segments:
        metadata["speakers"] = stats["speakers"]
        metadata["speaker_stats"] = stats["speaker_stats"]
    
    # Export options with tabs
    export_tab1, export_tab2 = st.tabs(["📄 Xuất Transcript", "📊 Xuất Thống kê"])
    
    with export_tab1:
        # Batch export option
        batch_export = st.checkbox("📦 Xuất tất cả định dạng cùng lúc", value=False, help="Xuất transcript ra tất cả các định dạng có sẵn")
        
        if batch_export:
            if st.button("📦 Tạo tất cả file export", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                export_results = {}
                
                try:
                    status_text.text("⏳ Đang tạo file TXT...")
                    progress_bar.progress(10)
                    txt_data, txt_filename, txt_error = safe_export_txt(st.session_state.transcript_text, "transcript.txt")
                    export_results["TXT"] = (txt_data, txt_filename, txt_error)
                    
                    status_text.text("⏳ Đang tạo file DOCX...")
                    progress_bar.progress(30)
                    docx_data, docx_filename, docx_error = safe_export_docx(st.session_state.transcript_text, metadata, "transcript.docx")
                    export_results["DOCX"] = (docx_data, docx_filename, docx_error)
                    
                    status_text.text("⏳ Đang tạo file PDF...")
                    progress_bar.progress(60)
                    pdf_data, pdf_filename, pdf_error = safe_export_pdf(st.session_state.transcript_text, metadata, "transcript.pdf")
                    export_results["PDF"] = (pdf_data, pdf_filename, pdf_error)
                    
                    status_text.text("⏳ Đang tạo file JSON...")
                    progress_bar.progress(80)
                    json_data = {
                        "transcript": st.session_state.transcript_text,
                        "metadata": metadata,
                        "statistics": stats
                    }
                    if st.session_state.speaker_segments:
                        json_data["speaker_segments"] = st.session_state.speaker_segments
                    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                    export_results["JSON"] = (json_str.encode('utf-8'), "transcript.json", None)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Hoàn thành!")
                    
                    # Display results
                    st.success("✅ Đã tạo tất cả file export!")
                    for format_name, (data, filename, error) in export_results.items():
                        if error:
                            st.error(f"❌ Lỗi khi tạo {format_name}: {error}")
                        else:
                            mime_types = {
                                "TXT": "text/plain",
                                "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                "PDF": "application/pdf",
                                "JSON": "application/json"
                            }
                            st.download_button(
                                f"📥 Tải {format_name}",
                                data=data,
                                file_name=filename,
                                mime=mime_types.get(format_name, "application/octet-stream"),
                                key=f"batch_download_{format_name}"
                            )
                    
                    progress_bar.empty()
                    status_text.empty()
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text("❌ Lỗi!")
                    st.error(f"❌ Lỗi khi tạo batch export: {str(e)}")
                    with st.expander("🔍 Chi tiết lỗi"):
                        st.code(traceback.format_exc())
        else:
            # Individual export options
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # TXT export
                txt_data, txt_filename, txt_error = safe_export_txt(st.session_state.transcript_text, "transcript.txt")
                if txt_error:
                    st.error(f"❌ {txt_error}")
                else:
                    st.download_button(
                        "⬇️ Tải TXT",
                        data=txt_data,
                        file_name=txt_filename,
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                # DOCX export
                docx_data, docx_filename, docx_error = safe_export_docx(st.session_state.transcript_text, metadata, "transcript.docx")
                if docx_error:
                    st.error(f"❌ {docx_error}")
                else:
                    st.download_button(
                        "⬇️ Tải DOCX",
                        data=docx_data,
                        file_name=docx_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            
            with col3:
                # PDF export
                pdf_data, pdf_filename, pdf_error = safe_export_pdf(st.session_state.transcript_text, metadata, "transcript.pdf")
                if pdf_error:
                    st.error(f"❌ {pdf_error}")
                else:
                    st.download_button(
                        "⬇️ Tải PDF",
                        data=pdf_data,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            with col4:
                # JSON export
                try:
                    json_data = {
                        "transcript": st.session_state.transcript_text,
                        "metadata": metadata,
                        "statistics": stats
                    }
                    if st.session_state.speaker_segments:
                        json_data["speaker_segments"] = st.session_state.speaker_segments
                    
                    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                    st.download_button(
                        "⬇️ Tải JSON",
                        data=json_str.encode('utf-8'),
                        file_name="transcript.json",
                        mime="application/json",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Lỗi khi tạo JSON: {str(e)}")
    
    with export_tab2:
        st.markdown("**Xuất thống kê ra file:**")
        
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            # CSV export
            csv_data, csv_filename, csv_error = export_statistics_csv(stats, "statistics.csv")
            if csv_error:
                st.error(f"❌ {csv_error}")
            else:
                st.download_button(
                    "📊 Tải CSV",
                    data=csv_data,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col_stat2:
            # JSON statistics export
            try:
                stats_json = {
                    "statistics": stats,
                    "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                stats_json_str = json.dumps(stats_json, ensure_ascii=False, indent=2)
                st.download_button(
                    "📊 Tải JSON",
                    data=stats_json_str.encode('utf-8'),
                    file_name="statistics.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo JSON: {str(e)}")
    
    # Preview transcript with better layout
    st.markdown("---")
    st.subheader("📝 Xem trước Transcript")
    
    preview_mode = st.radio(
        "Chế độ xem:",
        ["Đầy đủ", "Rút gọn (500 ký tự đầu)"],
        horizontal=True,
        help="Chọn cách hiển thị transcript"
    )
    
    if preview_mode == "Rút gọn (500 ký tự đầu)":
        preview_text = st.session_state.transcript_text[:500] + "..." if len(st.session_state.transcript_text) > 500 else st.session_state.transcript_text
        st.text_area(
            "Transcript (xem trước):",
            preview_text,
            height=200,
            key="export_preview_short",
            help=f"Hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu tiên. Tổng: {len(st.session_state.transcript_text)} ký tự"
        )
        st.caption(f"💡 Hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu tiên. Chọn 'Đầy đủ' để xem toàn bộ transcript.")
    else:
        st.text_area(
            "Transcript:",
            st.session_state.transcript_text,
            height=300,
            key="export_preview_full",
            help="Xem toàn bộ transcript trước khi xuất"
        )

# ===== Footer =====
render_footer()

