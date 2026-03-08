"""
APE - Autonomous Production Engineer
Authentication Models

JWT token handling, password hashing, and RBAC.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from server.database.config import get_db
from server.database.models.tenant import UserModel

# ===========================================
# Configuration
# ===========================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-min-32-chars")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ===========================================
# Enums for RBAC
# ===========================================

class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions."""
    # Requirements
    REQUIREMENTS_CREATE = "requirements:create"
    REQUIREMENTS_READ = "requirements:read"
    REQUIREMENTS_UPDATE = "requirements:update"
    REQUIREMENTS_DELETE = "requirements:delete"
    
    # Architecture/Gates
    GATES_APPROVE = "gates:approve"
    ARCHITECTURE_READ = "architecture:read"
    
    # Deployments
    DEPLOYMENTS_APPROVE = "deployments:approve"
    DEPLOYMENTS_READ = "deployments:read"
    
    # Admin
    USERS_MANAGE = "users:manage"
    REPOS_MANAGE = "repos:manage"
    BILLING_MANAGE = "billing:manage"
    TENANT_SETTINGS = "tenant:settings"


# Role to permissions mapping
RolePermissions = {
    UserRole.VIEWER: {
        Permission.REQUIREMENTS_READ,
        Permission.ARCHITECTURE_READ,
        Permission.DEPLOYMENTS_READ,
    },
    UserRole.MEMBER: {
        Permission.REQUIREMENTS_CREATE,
        Permission.REQUIREMENTS_READ,
        Permission.REQUIREMENTS_UPDATE,
        Permission.GATES_APPROVE,
        Permission.ARCHITECTURE_READ,
        Permission.DEPLOYMENTS_READ,
    },
    UserRole.ADMIN: {
        Permission.REQUIREMENTS_CREATE,
        Permission.REQUIREMENTS_READ,
        Permission.REQUIREMENTS_UPDATE,
        Permission.REQUIREMENTS_DELETE,
        Permission.GATES_APPROVE,
        Permission.ARCHITECTURE_READ,
        Permission.DEPLOYMENTS_APPROVE,
        Permission.DEPLOYMENTS_READ,
        Permission.USERS_MANAGE,
        Permission.REPOS_MANAGE,
        Permission.BILLING_MANAGE,
        Permission.TENANT_SETTINGS,
    },
}


# ===========================================
# Token Models
# ===========================================

class TokenData:
    """Decoded JWT token data."""
    
    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        role: UserRole,
        permissions: set[Permission],
        exp: datetime
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.role = role
        self.permissions = permissions
        self.exp = exp
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions


class TokenPair:
    """Access and refresh token pair."""
    
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
    
    def dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": "bearer",
            "expires_in": self.expires_in,
        }


# ===========================================
# Password Functions
# ===========================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


# ===========================================
# JWT Token Functions
# ===========================================

def create_access_token(
    user: UserModel,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user: User model
        expires_delta: Optional custom expiration
    
    Returns:
        JWT access token
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # Get permissions for user's role
    permissions = RolePermissions.get(UserRole(user.role), set())
    
    to_encode = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "role": user.role,
        "permissions": [p.value for p in permissions],
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user: UserModel,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user: User model
        expires_delta: Optional custom expiration
    
    Returns:
        JWT refresh token
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    
    to_encode = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type (access/refresh)
    
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        # Extract data
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        email = payload.get("email")
        role = payload.get("role")
        permissions = payload.get("permissions", [])
        exp = payload.get("exp")
        
        if user_id is None or tenant_id is None:
            return None
        
        # Convert permissions to enum set
        perm_set = {Permission(p) for p in permissions} if permissions else set()
        
        return TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email or "",
            role=UserRole(role) if role else UserRole.VIEWER,
            permissions=perm_set,
            exp=datetime.fromtimestamp(exp) if exp else datetime.utcnow(),
        )
        
    except JWTError:
        return None


# ===========================================
# FastAPI Dependencies
# ===========================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        UserModel if authenticated
    
    Raises:
        HTTPException: If not authenticated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    token_data = verify_token(token, "access")
    if token_data is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if user.tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended"
        )
    
    return user


def require_permission(permission: Permission):
    """
    Dependency factory for requiring specific permissions.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_permission(Permission.USERS_MANAGE))):
            ...
    
    Args:
        permission: Required permission
    
    Returns:
        Dependency function
    """
    async def permission_checker(
        user: UserModel = Depends(get_current_user)
    ) -> UserModel:
        user_permissions = RolePermissions.get(UserRole(user.role), set())
        
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}"
            )
        
        return user
    
    return permission_checker


def require_role(minimum_role: UserRole):
    """
    Dependency factory for requiring minimum role.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_role(UserRole.ADMIN))):
            ...
    
    Args:
        minimum_role: Minimum required role
    
    Returns:
        Dependency function
    """
    role_hierarchy = {
        UserRole.VIEWER: 0,
        UserRole.MEMBER: 1,
        UserRole.ADMIN: 2,
    }
    
    async def role_checker(
        user: UserModel = Depends(get_current_user)
    ) -> UserModel:
        user_role = UserRole(user.role)
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(minimum_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Minimum role required: {minimum_role.value}"
            )
        
        return user
    
    return role_checker


# ===========================================
# Utility Functions
# ===========================================

def generate_api_key() -> str:
    """
    Generate a secure API key for service accounts.
    
    Returns:
        Random API key string
    """
    return hashlib.sha256(os.urandom(32)).hexdigest()


def verify_api_key_format(api_key: str) -> bool:
    """
    Verify API key format (64 char hex string).
    
    Args:
        api_key: API key to verify
    
    Returns:
        True if valid format
    """
    if len(api_key) != 64:
        return False
    
    try:
        int(api_key, 16)
        return True
    except ValueError:
        return False
