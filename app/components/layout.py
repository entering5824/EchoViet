"""
Layout Utilities và CSS Styles
"""
import streamlit as st
import os

def render_logo():
    """Render logo ở đầu trang"""
    # Tìm logo từ nhiều vị trí có thể
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '../../assets/logo.webp'),
        os.path.join(os.path.dirname(__file__), '../assets/logo.webp'),
        'assets/logo.webp',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../assets/logo.webp')),
    ]
    
    logo_path = None
    for path in possible_paths:
        abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
        if os.path.exists(abs_path):
            logo_path = abs_path
            break
    
    if logo_path:
        # Center logo với kích thước nhỏ
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.image(logo_path, width=120)  # Kích thước cố định 120px
    else:
        # Fallback nếu không tìm thấy logo
        st.markdown("<!-- Logo not found -->", unsafe_allow_html=True)

def render_page_header(title: str, caption: str = None, icon: str = None, show_logo: bool = True):
    """
    Render page header thống nhất cho tất cả các page
    
    Args:
        title: Tiêu đề page
        caption: Mô tả ngắn (optional)
        icon: Icon emoji (optional, sẽ được thêm vào title nếu có)
        show_logo: Hiển thị logo (default: True)
    """
    # Render logo nếu được yêu cầu
    if show_logo:
        render_logo()
    
    # Format title với icon
    if icon:
        header_text = f"{icon} {title}"
    else:
        header_text = title
    
    # Render header với class main-header
    st.markdown(
        f'<div class="main-header">{header_text}</div>',
        unsafe_allow_html=True
    )
    
    # Render caption nếu có
    if caption:
        st.caption(caption)

def apply_custom_css():
    """Apply custom CSS styles cho toàn bộ app"""
    st.markdown("""
    <style>
    /* Logo Container */
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
    }
    
    .logo-container img {
        max-width: 200px;
        height: auto;
        margin: 0 auto;
    }
    
    /* Main Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }
    
    /* Stat Box */
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
    }
    
    /* Card Container */
    .card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    
    /* Improved Button Styles */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Better Typography */
    h1, h2, h3 {
        color: #1f4e79;
    }
    
    /* Improved Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Info/Warning/Success Boxes */
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    
    /* Model Badge */
    .model-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85em;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .model-badge-recommended {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffc107;
    }
    
    .model-badge-transformer {
        background-color: #d1ecf1;
        color: #0c5460;
        border: 1px solid #17a2b8;
    }
    
    .model-badge-ctc {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #28a745;
    }
    
    /* Spacing Helpers */
    .spacing-top {
        margin-top: 2rem;
    }
    
    .spacing-bottom {
        margin-bottom: 2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def create_card(title=None, content=None):
    """
    Tạo card container
    
    Args:
        title: Tiêu đề card (optional)
        content: Nội dung card (optional)
    
    Returns:
        Streamlit container
    """
    with st.container():
        if title:
            st.subheader(title)
        if content:
            st.markdown(content)
        return st.container()

