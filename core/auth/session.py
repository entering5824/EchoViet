"""
Session management for user authentication and state
"""
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from .roles import UserRole, set_user_role, get_user_role

def init_session():
    """Initialize session state with default values"""
    # User info
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Guest User"
    if "user_role" not in st.session_state:
        st.session_state.user_role = UserRole.USER.value
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    
    # Session metadata
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = datetime.now()
    if "transcripts_history" not in st.session_state:
        st.session_state.transcripts_history = []
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    
    # Audio/transcription state (existing)
    if "audio_data" not in st.session_state:
        st.session_state.audio_data = None
    if "audio_sr" not in st.session_state:
        st.session_state.audio_sr = None
    if "transcript_result" not in st.session_state:
        st.session_state.transcript_result = None
    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = ""
    if "audio_info" not in st.session_state:
        st.session_state.audio_info = None
    if "speaker_segments" not in st.session_state:
        st.session_state.speaker_segments = None

def get_current_user() -> Dict[str, Any]:
    """Get current user information"""
    return {
        "user_id": st.session_state.get("user_id"),
        "user_name": st.session_state.get("user_name", "Guest User"),
        "user_email": st.session_state.get("user_email"),
        "user_role": get_user_role(),
        "session_start_time": st.session_state.get("session_start_time"),
    }

def login_user(user_id: str, user_name: str, user_email: Optional[str] = None, role: UserRole = UserRole.USER):
    """Login a user (for demo purposes - in production, use proper authentication)"""
    st.session_state.user_id = user_id
    st.session_state.user_name = user_name
    st.session_state.user_email = user_email
    set_user_role(role)
    st.session_state.session_start_time = datetime.now()

def logout_user():
    """Logout current user"""
    st.session_state.user_id = None
    st.session_state.user_name = "Guest User"
    st.session_state.user_email = None
    set_user_role(UserRole.USER)
    # Clear sensitive data but keep session state structure
    st.session_state.transcripts_history = []

def add_to_history(transcript_data: Dict[str, Any]):
    """Add a transcript to history"""
    if "transcripts_history" not in st.session_state:
        st.session_state.transcripts_history = []
    
    transcript_entry = {
        "id": len(st.session_state.transcripts_history),
        "timestamp": datetime.now().isoformat(),
        **transcript_data
    }
    st.session_state.transcripts_history.append(transcript_entry)
    
    # Keep only last 100 entries
    if len(st.session_state.transcripts_history) > 100:
        st.session_state.transcripts_history = st.session_state.transcripts_history[-100:]












