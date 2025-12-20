"""
Role definitions and permission management
"""
from enum import Enum
from typing import List, Optional
import streamlit as st

class UserRole(Enum):
    """User roles in the system"""
    USER = "user"  # Regular user
    AI_SPECIALIST = "ai_specialist"  # AI/ML specialist
    ADMIN = "admin"  # Administrator
    MANAGER = "manager"  # Manager/Admin (same as admin for now)

# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.USER: [
        "upload_audio",
        "transcribe",
        "edit_transcript",
        "export_transcript",
        "view_history",
        "share_transcript",
    ],
    UserRole.AI_SPECIALIST: [
        "upload_audio",
        "transcribe",
        "edit_transcript",
        "export_transcript",
        "view_history",
        "share_transcript",
        "manage_models",
        "configure_models",
        "evaluate_models",
        "manage_datasets",
        "view_logs",
        "run_benchmarks",
    ],
    UserRole.ADMIN: [
        "upload_audio",
        "transcribe",
        "edit_transcript",
        "export_transcript",
        "view_history",
        "share_transcript",
        "manage_models",
        "configure_models",
        "evaluate_models",
        "manage_datasets",
        "view_logs",
        "run_benchmarks",
        "manage_users",
        "view_analytics",
        "manage_settings",
        "view_audit_logs",
        "manage_billing",
    ],
    UserRole.MANAGER: [
        "upload_audio",
        "transcribe",
        "edit_transcript",
        "export_transcript",
        "view_history",
        "share_transcript",
        "view_analytics",
        "view_audit_logs",
        "manage_billing",
    ],
}

def get_user_role() -> UserRole:
    """
    Get current user's role from session state
    Defaults to USER if not set
    """
    role_str = st.session_state.get("user_role", "user")
    try:
        return UserRole(role_str)
    except ValueError:
        return UserRole.USER

def set_user_role(role: UserRole):
    """Set user role in session state"""
    st.session_state.user_role = role.value

def has_permission(permission: str, role: Optional[UserRole] = None) -> bool:
    """
    Check if user has a specific permission
    
    Args:
        permission: Permission name to check
        role: User role (if None, uses current user's role)
    
    Returns:
        True if user has permission, False otherwise
    """
    if role is None:
        role = get_user_role()
    
    return permission in ROLE_PERMISSIONS.get(role, [])

def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific roles for a function
    
    Usage:
        @require_role(UserRole.ADMIN, UserRole.AI_SPECIALIST)
        def admin_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_role = get_user_role()
            if current_role not in allowed_roles:
                st.error(f"❌ Bạn không có quyền truy cập. Yêu cầu role: {', '.join([r.value for r in allowed_roles])}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: str):
    """
    Decorator to require a specific permission
    
    Usage:
        @require_permission("manage_models")
        def model_management():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not has_permission(permission):
                st.error(f"❌ Bạn không có quyền: {permission}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator












