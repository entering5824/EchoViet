"""
Authentication and authorization module
Role-based access control for the transcription system
"""

from .roles import UserRole, get_user_role, require_role
from .session import init_session, get_current_user

__all__ = ['UserRole', 'get_user_role', 'require_role', 'init_session', 'get_current_user']












