"""
Home / Dashboard Page
Main page – overview & navigation with clear workflow guide
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
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
render_page_header(
    "Vietnamese Speech to Text",
    "Vietnamese speech-to-text conversion system – optimized for meetings & note-taking",
    "🎤",
    show_logo=True
)

# ===== Quick Start Guide =====
st.markdown("### 🚀 Quick Start Guide")
st.markdown("""
Just **3 simple steps** to convert audio to text:
""")

# Workflow steps with progress indicator
def get_workflow_progress():
    """Calculate workflow progress based on session state"""
    progress = 0
    if st.session_state.get("audio_data") is not None:
        progress += 1
    if st.session_state.get("transcript_text"):
        progress += 1
    if st.session_state.get("transcript_enhanced") or st.session_state.get("speaker_segments"):
        progress += 1
    return progress

workflow_progress = get_workflow_progress()

# Workflow steps
workflow_steps = [
    {
        "number": 1,
        "title": "Upload Audio",
        "description": "Upload audio file (WAV, MP3, FLAC, M4A, OGG)",
        "page": "pages/1_🎤_Audio_Input.py",
        "icon": "🎤",
        "completed": workflow_progress >= 1
    },
    {
        "number": 2,
        "title": "Transcription",
        "description": "Convert speech to text",
        "page": "pages/2_📝_Transcription.py",
        "icon": "📝",
        "completed": workflow_progress >= 2
    },
    {
        "number": 3,
        "title": "Enhancement & Export",
        "description": "Enhance text and export file",
        "page": "pages/3_✨_Speaker_Enhancement.py",
        "icon": "✨",
        "completed": workflow_progress >= 3
    }
]

# Display workflow with progress
col1, col2, col3 = st.columns(3)
for i, step in enumerate(workflow_steps):
    with [col1, col2, col3][i]:
        status_icon = "✅" if step["completed"] else "⏳"
        status_color = "#4caf50" if step["completed"] else "#ff9800"
        
        st.markdown(f"""
        <div style="
            border: 2px solid {status_color};
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            background: {'#e8f5e9' if step['completed'] else '#fff3e0'};
            margin-bottom: 1rem;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{step['icon']}</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: #1f4e79; margin-bottom: 0.5rem;">
                {status_icon} Step {step['number']}: {step['title']}
            </div>
            <div style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;">
                {step['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Start Step {step['number']}", key=f"workflow_btn_{i}", use_container_width=True):
            st.switch_page(step['page'])

# Progress bar
st.progress(workflow_progress / len(workflow_steps))
st.caption(f"Progress: {workflow_progress}/{len(workflow_steps)} steps completed")

# ===== Main Content =====
st.divider()
st.markdown("### 📌 Overview")

st.markdown("""
The system supports **Vietnamese audio → text conversion** with high accuracy,
focused on **meetings, interviews, and long notes**.
""")

# Pipeline Diagram
st.markdown("#### 🔄 Processing Pipeline")
render_pipeline_diagram()

# Features in a cleaner layout
st.markdown("#### ✨ Key Features")
col_feat1, col_feat2 = st.columns(2)

with col_feat1:
    st.markdown("""
    - 🎤 **Vietnamese speech recognition** (Whisper)
    - 👥 **Speaker diarization** (Speaker identification)
    """)

with col_feat2:
    st.markdown("""
    - ✨ **AI Text Enhancement** (punctuation, capitalization, cleaning)
    - 📤 **Multi-format export** (TXT / DOCX / PDF / JSON)
    """)

# ===== Quick Navigation =====
st.divider()
st.markdown("### 🔗 Quick Navigation")

nav_cols = st.columns(4)
nav_buttons = [
    ("🎤 Audio Input", "pages/1_🎤_Audio_Input.py", nav_cols[0]),
    ("📝 Transcription", "pages/2_📝_Transcription.py", nav_cols[1]),
    ("✨ Enhancement", "pages/3_✨_Speaker_Enhancement.py", nav_cols[2]),
    ("📊 Export", "pages/4_📊_Export_Reporting.py", nav_cols[3]),
]

for title, page, col in nav_buttons:
    with col:
        if st.button(title, key=f"nav_{title}", use_container_width=True):
            st.switch_page(page)

# ===== System status =====
st.divider()
render_status_display()

# ===== Help / Info =====
st.divider()
col_help1, col_help2 = st.columns(2)

with col_help1:
    with st.expander("💡 Usage Tips", expanded=False):
        st.markdown("""
        - ✅ Prefer audio with **low noise**, clear voice
        - ✅ Long files will be **automatically chunked**
        - ✅ Speaker diarization works best with **2–4 speakers**
        - ✅ Use "Recommended" mode for best results
        """)

with col_help2:
    with st.expander("🔒 Privacy & Security", expanded=False):
        st.markdown("""
        - 🔐 Audio processed on server, **not shared with third parties**
        - 🗑️ Temporary files are **automatically deleted** after processing
        - 📝 Audio / transcript not saved unless exported
        """)

# Advanced section (collapsed by default)
with st.expander("⚙️ Advanced Settings (For technical users)", expanded=False):
    adv_cols = st.columns(3)
    with adv_cols[0]:
        if st.button("⚙️ Advanced Settings", use_container_width=True):
            st.switch_page("pages/5_⚙️_Advanced_Settings.py")
    with adv_cols[1]:
        if st.button("📈 Analysis & Evaluation", use_container_width=True):
            st.switch_page("pages/6_📈_Analysis_Evaluation.py")
    with adv_cols[2]:
        if st.button("🔌 API / System Info", use_container_width=True):
            st.switch_page("pages/7_🔌_API_System.py")

# ===== Footer =====
render_footer()
