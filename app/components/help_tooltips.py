"""
Help Tooltips Component
Cung cấp tooltips và help sections cho các pages
"""
import streamlit as st

def render_help_tooltip(text: str, icon: str = "💡"):
    """
    Render một help tooltip
    
    Args:
        text: Nội dung tooltip
        icon: Icon để hiển thị (default: 💡)
    """
    st.markdown(f"""
    <div style="
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    ">
        <strong>{icon}</strong> {text}
    </div>
    """, unsafe_allow_html=True)

def render_help_section(title: str, items: list):
    """
    Render một help section với danh sách items
    
    Args:
        title: Tiêu đề section
        items: List of strings hoặc dict với 'title' và 'description'
    """
    with st.expander(f"❓ {title}", expanded=False):
        for item in items:
            if isinstance(item, dict):
                st.markdown(f"**{item.get('title', '')}**: {item.get('description', '')}")
            else:
                st.markdown(f"- {item}")

def render_quick_tips(tips: list):
    """
    Render quick tips box
    
    Args:
        tips: List of tip strings
    """
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
    ">
        <h4 style="color: white; margin-top: 0;">💡 Quick Tips</h4>
    </div>
    """, unsafe_allow_html=True)
    
    for tip in tips:
        st.markdown(f"✅ {tip}")

def get_field_help(field_name: str) -> str:
    """
    Get help text for common fields
    
    Args:
        field_name: Tên field
        
    Returns:
        Help text string
    """
    help_texts = {
        "audio_upload": "Tải lên file audio để bắt đầu. Hỗ trợ: WAV, MP3, FLAC, M4A, OGG",
        "model_selection": "Chọn mô hình ASR. Whisper được khuyến nghị cho tiếng Việt",
        "quality_preset": "Chọn chất lượng: Nhanh (nhanh, ít chính xác), Cân bằng (khuyến nghị), Chính xác (chậm, chính xác nhất)",
        "preprocessing": "Tiền xử lý audio để cải thiện chất lượng nhận diện",
        "speaker_diarization": "Phân biệt và gán nhãn người nói trong audio",
        "text_enhancement": "Cải thiện văn bản với AI: sửa dấu câu, viết hoa, làm sạch",
        "export": "Xuất transcript ra các định dạng khác nhau"
    }
    return help_texts.get(field_name, "")
