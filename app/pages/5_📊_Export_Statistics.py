"""
Export & Statistics Page
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.asr.transcription_service import get_transcript_statistics
from export.export_utils import export_txt, export_docx, export_pdf
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

st.header("📊 Export & Statistics")
if st.session_state.transcript_result and st.session_state.audio_info and st.session_state.transcript_text:
    # Statistics
    st.subheader("📈 Thống kê")
    
    stats = get_transcript_statistics(
        st.session_state.transcript_result,
        st.session_state.audio_info['duration']
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Số từ", f"{stats.get('word_count', 0):,}")
    with col2:
        st.metric("Số ký tự", f"{stats.get('character_count', 0):,}")
    with col3:
        st.metric("Độ dài", f"{stats.get('duration', 0):.2f} giây")
    with col4:
        st.metric("Từ/phút", f"{stats.get('words_per_minute', 0):.1f}")
    
    # Keywords (đơn giản)
    st.subheader("🔑 Keywords (tần suất cao)")
    words = [w.lower().strip(",.;:") for w in st.session_state.transcript_text.split()]
    stop = {"và", "là", "của", "the", "a", "an", "to", "in", "on", "for", "với", "có"}
    freq = {}
    for w in words:
        if w and w not in stop:
            freq[w] = freq.get(w, 0) + 1
    top_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_keywords:
        st.write(", ".join([f\"{k} ({v})\" for k, v in top_keywords]))
    else:
        st.write("Không có từ khoá nổi bật.")
    
    # Export options (hiển thị trực tiếp download buttons)
    st.subheader("💾 Export Transcript")
    
    metadata = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'duration': stats.get('duration', 0),
        'word_count': stats.get('word_count', 0),
        'character_count': stats.get('character_count', 0)
    }
    
            try:
        txt_bytes, txt_name = export_txt(
                        st.session_state.transcript_text,
                        f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    )
        st.download_button("⬇️ Tải TXT", data=txt_bytes, file_name=txt_name, mime="text/plain")
                
        docx_bytes, docx_name = export_docx(
                        st.session_state.transcript_text,
                        metadata,
                        f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    )
        st.download_button("⬇️ Tải DOCX", data=docx_bytes, file_name=docx_name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                
        pdf_bytes, pdf_name = export_pdf(
                        st.session_state.transcript_text,
                        metadata,
                        f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    )
        st.download_button("⬇️ Tải PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf")
                st.success("✅ File đã sẵn sàng để tải xuống!")
            except Exception as e:
        st.error(f\"❌ Lỗi khi export: {str(e)}\")
else:
    st.info("ℹ️ Vui lòng transcribe audio trước để xem thống kê và export.")

