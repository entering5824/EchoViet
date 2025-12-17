"""
Pipeline Diagram Component
Hiển thị sơ đồ luồng xử lý: Audio → Preprocessing → Transcription → Enhancement → Export
"""
import streamlit as st

def render_pipeline_diagram():
    """
    Render pipeline diagram với step boxes và icons
    Hiển thị flow: Audio → Preprocessing → Transcription → Enhancement → Export
    """
    st.markdown("""
    <style>
    .pipeline-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 2rem 0;
        margin: 2rem 0;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .pipeline-step {
        flex: 1;
        min-width: 150px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem 1rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }
    
    .pipeline-step:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    
    .pipeline-step-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .pipeline-step-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .pipeline-step-desc {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    .pipeline-arrow {
        font-size: 2rem;
        color: #667eea;
        margin: 0 0.5rem;
        flex-shrink: 0;
    }
    
    .pipeline-step-1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .pipeline-step-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .pipeline-step-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .pipeline-step-4 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .pipeline-step-5 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    
    @media (max-width: 768px) {
        .pipeline-container {
            flex-direction: column;
        }
        .pipeline-arrow {
            transform: rotate(90deg);
            margin: 0.5rem 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Pipeline steps
    steps = [
        {
            "icon": "🎤",
            "title": "Audio Input",
            "desc": "Upload hoặc ghi âm",
            "page": "pages/1_🎤_Audio_Input.py",
            "class": "pipeline-step-1"
        },
        {
            "icon": "🔧",
            "title": "Preprocessing",
            "desc": "Chuẩn hóa & làm sạch",
            "page": "pages/1_🎤_Audio_Input.py",
            "class": "pipeline-step-2"
        },
        {
            "icon": "📝",
            "title": "Transcription",
            "desc": "Speech → Text",
            "page": "pages/2_📝_Transcription.py",
            "class": "pipeline-step-3"
        },
        {
            "icon": "✨",
            "title": "Enhancement",
            "desc": "Speaker & Text AI",
            "page": "pages/3_✨_Speaker_Enhancement.py",
            "class": "pipeline-step-4"
        },
        {
            "icon": "📤",
            "title": "Export",
            "desc": "TXT / DOCX / PDF",
            "page": "pages/4_📊_Export_Reporting.py",
            "class": "pipeline-step-5"
        }
    ]
    
    # Render pipeline
    html = '<div class="pipeline-container">'
    
    for i, step in enumerate(steps):
        html += f'''
        <div class="pipeline-step {step['class']}" onclick="window.location.href='{step['page']}'">
            <div class="pipeline-step-icon">{step['icon']}</div>
            <div class="pipeline-step-title">{step['title']}</div>
            <div class="pipeline-step-desc">{step['desc']}</div>
        </div>
        '''
        
        # Add arrow between steps (not after last step)
        if i < len(steps) - 1:
            html += '<div class="pipeline-arrow">→</div>'
    
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Alternative: Use Streamlit columns for better interactivity
    st.markdown("---")
    cols = st.columns(5)
    
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if st.button(
                f"{step['icon']}\n\n**{step['title']}**\n\n{step['desc']}",
                key=f"pipeline_btn_{i}",
                use_container_width=True,
                help=f"Chuyển đến {step['title']}"
            ):
                st.switch_page(step['page'])

