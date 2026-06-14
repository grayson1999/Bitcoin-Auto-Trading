"""Auth module - authentication dependencies."""

from src.modules.auth.deps import (
    AdminUser,
    CurrentUser,
    ResolvedUser,
    get_current_user,
    require_admin,
    resolve_user,
)

__all__ = [
    "AdminUser",
    "CurrentUser",
    "ResolvedUser",
    "get_current_user",
    "require_admin",
    "resolve_user",
]
