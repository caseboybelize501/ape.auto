"""
APE - Autonomous Production Engineer
Authentication API

Endpoints for login, registration, token management.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr

from server.database.config import get_db
from server.database.models.tenant import UserModel, TenantModel
from server.models.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    get_current_user,
    TokenPair,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ===========================================
# Request/Response Models
# ===========================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    tenant_name: str = None  # Optional, creates new tenant if not provided


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    tenant_id: str
    tenant_name: str


# ===========================================
# Authentication Endpoints
# ===========================================

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access token and refresh token.
    """
    # Find user by email
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check tenant status
    if user.tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    If tenant_name is provided, creates a new tenant.
    Otherwise, user must be invited to existing tenant.
    """
    from server.database.models.tenant import TenantModel
    from pydantic import EmailStr
    
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create or get tenant
    if request.tenant_name:
        tenant = TenantModel(
            id=f"tenant-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=request.tenant_name,
            admin_email=request.email,
            status="active",
        )
        db.add(tenant)
        db.flush()  # Get tenant ID
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name required for registration"
        )
    
    # Create user
    user = UserModel(
        id=f"user-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        tenant_id=tenant.id,
        email=request.email,
        name=request.name,
        role="admin",  # First user is admin
        password_hash=hash_password(request.password),
        can_submit_requirements=True,
        can_approve_gates=True,
        can_manage_repos=True,
        can_manage_billing=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    token_data = verify_token(refresh_token, "refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Create new tokens
    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name,
    )


@router.post("/logout")
async def logout(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Logout (invalidate tokens).
    
    Note: With JWT, tokens are stateless. For true logout,
    implement a token blacklist in Redis.
    """
    # For now, just return success
    # In production, add token to blacklist
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    """
    # Verify old password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Update password
    current_user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# ===========================================
# OAuth2 Login (GitHub/GitLab)
# ===========================================

@router.get("/oauth/github")
async def github_oauth_login():
    """
    Initiate GitHub OAuth login.
    """
    from urllib.parse import urlencode
    
    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/github/callback")
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user:email",
    }
    
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    return {"authorization_url": auth_url}


@router.get("/oauth/github/callback")
async def github_oauth_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    GitHub OAuth callback.
    """
    import requests
    
    # Exchange code for token
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI")
    
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"}
    )
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from GitHub"
        )
    
    # Get user info from GitHub
    github_user = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    # Get emails
    github_emails = requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    primary_email = next((e["email"] for e in github_emails if e["primary"]), None)
    
    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email found in GitHub account"
        )
    
    # Find or create user
    user = db.query(UserModel).filter(UserModel.email == primary_email).first()
    
    if not user:
        # Create new user with default tenant
        from server.database.models.tenant import TenantModel
        
        tenant = TenantModel(
            id=f"tenant-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=github_user.get("login", "GitHub User"),
            admin_email=primary_email,
            status="active",
        )
        db.add(tenant)
        db.flush()
        
        user = UserModel(
            id=f"user-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            tenant_id=tenant.id,
            email=primary_email,
            name=github_user.get("name", github_user.get("login")),
            role="admin",
            auth_provider="github",
            auth_provider_id=str(github_user.get("id")),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create tokens
    access_token_jwt = create_access_token(user)
    refresh_token_jwt = create_refresh_token(user)
    
    return {
        "access_token": access_token_jwt,
        "refresh_token": refresh_token_jwt,
        "token_type": "bearer",
    }
