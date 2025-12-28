"""
Home / Dashboard Page
Trang chính – overview & navigation
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from app.components.status_display import render_status_display
from app.components.footer import render_footer
from app.components.pipeline_diagram import render_pipeline_diagram

# Page config
st.set_page_config(
    page_title="Dashboard - Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide"
)

apply_custom_css()

# ===== Header =====
st.markdown(
    '<div class="main-header">🎤 Vietnamese Speech to Text</div>',
    unsafe_allow_html=True
)
st.caption("Hệ thống chuyển đổi giọng nói tiếng Việt thành văn bản – tối ưu cho họp & ghi chép")

# ===== Main =====
col_main, col_nav = st.columns([2.2, 1])

with col_main:
    st.markdown("### 📌 Tổng quan")

    st.markdown("""
    Hệ thống hỗ trợ **chuyển đổi audio tiếng Việt → văn bản** với độ chính xác cao,
    tập trung vào **cuộc họp, phỏng vấn và ghi chú dài**.
    """)
    
    # Pipeline Diagram
    st.markdown("#### 🔄 Quy trình xử lý")
    render_pipeline_diagram()

    st.markdown("#### ✨ Tính năng nổi bật")
    st.markdown("""
    - 🎤 **Nhận diện giọng nói** tiếng Việt (Whisper)
    - 👥 **Phân biệt người nói** (Speaker Diarization)
    - ✨ **AI Text Enhancement** (dấu câu, viết hoa, làm sạch)
    - 📤 **Xuất đa định dạng** (TXT / DOCX / PDF / JSON)
    """)

with col_nav:
    st.markdown("### 🚀 Bắt đầu")

    if st.button("🎤 Audio Input", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🎤_Audio_Input.py")

    st.divider()

    st.markdown("### 🔗 Điều hướng nhanh")

    if st.button("📝 Transcription", use_container_width=True):
        st.switch_page("pages/2_📝_Transcription.py")

    if st.button("✨ Speaker & Enhancement", use_container_width=True):
        st.switch_page("pages/3_✨_Speaker_Enhancement.py")

    if st.button("📊 Export & Reporting", use_container_width=True):
        st.switch_page("pages/4_📊_Export_Reporting.py")
    
    st.divider()
    st.markdown("### ⚙️ Advanced")
    
    with st.expander("🔧 Technical Settings"):
        if st.button("⚙️ Advanced Settings", use_container_width=True):
            st.switch_page("pages/5_⚙️_Advanced_Settings.py")
        
        if st.button("📈 Analysis & Evaluation", use_container_width=True):
            st.switch_page("pages/6_📈_Analysis_Evaluation.py")
        
        if st.button("🔌 API / System Info", use_container_width=True):
            st.switch_page("pages/7_🔌_API_System.py")

# ===== System status =====
st.divider()
render_status_display()

# ===== Help / Info =====
st.divider()
col_help1, col_help2 = st.columns(2)

with col_help1:
    with st.expander("💡 Tips sử dụng"):
        st.markdown("""
        - Ưu tiên audio **ít nhiễu**, rõ giọng
        - File dài sẽ được **tự động chia đoạn**
        - Speaker diarization hiệu quả nhất với **2–4 người nói**
        """)

with col_help2:
    with st.expander("🔒 Quyền riêng tư & bảo mật"):
        st.markdown("""
        - Audio xử lý trên server, **không chia sẻ bên thứ ba**
        - File tạm được **tự động xóa**
        - Không lưu audio / transcript nếu không export
        """)

# ===== Footer =====
render_footer()
