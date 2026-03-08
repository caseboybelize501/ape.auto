"""
APE - Autonomous Production Engineer
Authentication Package

JWT authentication, OAuth integration, and RBAC.
"""

from server.models.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password,
    TokenData,
    TokenPair,
)

from server.models.auth import (
    UserRole,
    Permission,
    RolePermissions,
)

__all__ = [
    # Token functions
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    # Password functions
    "hash_password",
    "verify_password",
    # Models
    "TokenData",
    "TokenPair",
    "UserRole",
    "Permission",
    "RolePermissions",
]
