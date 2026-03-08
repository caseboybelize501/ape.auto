"""
APE - Autonomous Production Engineer
Unit Tests for Authentication

Tests for server/models/auth.py
"""

import pytest
import os
from datetime import datetime, timedelta

from server.models.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenData,
    UserRole,
    Permission,
    RolePermissions,
    require_permission,
    require_role,
)


class TestPasswordHashing:
    """Tests for password hashing."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2")  # bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_different_for_same_password(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # bcrypt uses salt, so hashes should be different
        assert hash1 != hash2


class TestJWTToken:
    """Tests for JWT token creation and verification."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = type('User', (), {
            'id': 'test-user-123',
            'tenant_id': 'test-tenant',
            'email': 'test@example.com',
            'role': 'admin',
        })()
        return user
    
    def test_create_access_token(self, mock_user):
        """Test access token creation."""
        token = create_access_token(mock_user)
        
        assert token is not None
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts
    
    def test_create_refresh_token(self, mock_user):
        """Test refresh token creation."""
        token = create_refresh_token(mock_user)
        
        assert token is not None
        assert len(token) > 0
    
    def test_verify_access_token(self, mock_user):
        """Test verifying access token."""
        token = create_access_token(mock_user)
        token_data = verify_token(token, "access")
        
        assert token_data is not None
        assert token_data.user_id == mock_user.id
        assert token_data.tenant_id == mock_user.tenant_id
        assert token_data.email == mock_user.email
        assert token_data.role == UserRole.ADMIN
    
    def test_verify_refresh_token(self, mock_user):
        """Test verifying refresh token."""
        token = create_refresh_token(mock_user)
        token_data = verify_token(token, "refresh")
        
        assert token_data is not None
        assert token_data.user_id == mock_user.id
    
    def test_verify_wrong_token_type(self, mock_user):
        """Test verifying access token as refresh token."""
        access_token = create_access_token(mock_user)
        token_data = verify_token(access_token, "refresh")
        
        assert token_data is None
    
    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        token_data = verify_token("invalid.token.here", "access")
        
        assert token_data is None
    
    def test_token_expiration(self, mock_user):
        """Test token expiration."""
        # Create token that expires in 1 minute
        token = create_access_token(
            mock_user,
            expires_delta=timedelta(minutes=1)
        )
        token_data = verify_token(token, "access")
        
        assert token_data is not None
        assert token_data.exp > datetime.utcnow()
    
    def test_token_permissions(self, mock_user):
        """Test token includes correct permissions."""
        mock_user.role = "admin"
        token = create_access_token(mock_user)
        token_data = verify_token(token, "access")
        
        assert token_data.permissions is not None
        assert len(token_data.permissions) > 0
    
    def test_has_permission(self, mock_user):
        """Test permission checking."""
        mock_user.role = "admin"
        token = create_access_token(mock_user)
        token_data = verify_token(token, "access")
        
        # Admin should have all permissions
        assert token_data.has_permission(Permission.USERS_MANAGE) is True
        assert token_data.has_permission(Permission.REQUIREMENTS_CREATE) is True


class TestRBAC:
    """Tests for Role-Based Access Control."""
    
    def test_role_permissions_mapping(self):
        """Test role to permissions mapping."""
        assert UserRole.VIEWER in RolePermissions
        assert UserRole.MEMBER in RolePermissions
        assert UserRole.ADMIN in RolePermissions
    
    def test_viewer_permissions(self):
        """Test viewer has read-only permissions."""
        viewer_perms = RolePermissions[UserRole.VIEWER]
        
        assert Permission.REQUIREMENTS_READ in viewer_perms
        assert Permission.REQUIREMENTS_CREATE not in viewer_perms
        assert Permission.USERS_MANAGE not in viewer_perms
    
    def test_member_permissions(self):
        """Test member has create/update permissions."""
        member_perms = RolePermissions[UserRole.MEMBER]
        
        assert Permission.REQUIREMENTS_CREATE in member_perms
        assert Permission.REQUIREMENTS_UPDATE in member_perms
        assert Permission.GATES_APPROVE in member_perms
        assert Permission.USERS_MANAGE not in member_perms
    
    def test_admin_permissions(self):
        """Test admin has all permissions."""
        admin_perms = RolePermissions[UserRole.ADMIN]
        
        assert len(admin_perms) > len(RolePermissions[UserRole.MEMBER])
        assert Permission.USERS_MANAGE in admin_perms
        assert Permission.BILLING_MANAGE in admin_perms


class TestRequirePermission:
    """Tests for permission requirement decorator."""
    
    @pytest.mark.asyncio
    async def test_require_permission_success(self):
        """Test permission check passes."""
        # This would need a full FastAPI test client to properly test
        # For now, just verify the function exists and returns a callable
        checker = require_permission(Permission.REQUIREMENTS_READ)
        assert callable(checker)
    
    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test role check passes."""
        checker = require_role(UserRole.MEMBER)
        assert callable(checker)
