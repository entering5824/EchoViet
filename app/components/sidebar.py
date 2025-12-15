"""
Shared Sidebar Component
Hiển thị logo và navigation cho tất cả pages
"""
import streamlit as st
import os

def render_sidebar(logo_width=110):
    """
    Render sidebar với logo và title
    
    Args:
        logo_width: Chiều rộng logo (default: 110)
    """
    # Get project root (2 levels up from app/components/)
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    img_path = os.path.join(base, "assets", "logo.webp")
    
    # Display logo
    if os.path.exists(img_path):
        st.sidebar.image(img_path, width=logo_width)
    else:
        # Fallback nếu không có logo
        st.sidebar.markdown("### 🎤")
    
    st.sidebar.title("🎤 Vietnamese Speech to Text")
    st.sidebar.markdown("---")
    
    pages = [
        ("app/main.py", "🏠 Home"),
        ("app/pages/1_📤_Upload_Record.py", "📤 Upload & Record"),
        ("app/pages/2_🎧_Preprocessing.py", "🎧 Preprocessing"),
        ("app/pages/3_📝_Transcription.py", "📝 Transcription"),
        ("app/pages/4_👥_Speaker_Diarization.py", "👥 Speaker Diarization"),
        ("app/pages/5_📊_Export_Statistics.py", "📊 Export & Statistics"),
        ("app/pages/6_🔬_ASR_Benchmark.py", "🔬 ASR Benchmark"),
        ("app/pages/Analysis.py", "📊 Analysis (Single-file)"),
        ("app/pages/Training_Info.py", "📚 Training Info"),
        ("app/pages/Streaming.py", "📡 Streaming"),
        ("app/pages/API_Docs.py", "🧩 API Docs"),
    ]

    nav_choice = None
    try:
        st.sidebar.markdown("#### 🚀 Điều hướng nhanh")
        for path, label in pages:
            st.sidebar.page_link(path, label=label)
    except Exception:
        st.sidebar.markdown("#### 🚀 Điều hướng (fallback)")
        nav_choice = st.sidebar.radio(
            "Chọn trang:",
            [label for _, label in pages],
            index=0,
        )
        st.session_state["nav_choice"] = nav_choice

    st.sidebar.markdown("""
    <div style="font-size: 0.9em; color: #666; padding: 10px 0;">
    Nếu menu link không khả dụng, dùng radio fallback hoặc chạy trực tiếp `streamlit run app/main.py`.
    </div>
    """, unsafe_allow_html=True)
