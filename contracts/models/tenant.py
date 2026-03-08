"""
APE - Autonomous Production Engineer
Contract: Tenant Models

Immutable Pydantic schemas for multi-tenancy,
repository connections, and subscription management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SubscriptionTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class RepoPlatform(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTH_EXPIRED = "auth_expired"


class Tenant(BaseModel):
    """
    Multi-tenant organization.
    """
    id: str = Field(..., description="Unique tenant ID")
    name: str = Field(..., description="Organization name")
    
    # Contact
    admin_email: str = Field(..., description="Admin contact email")
    company_name: Optional[str] = None
    
    # Subscription
    tier: SubscriptionTier = SubscriptionTier.STARTER
    status: TenantStatus = TenantStatus.PENDING
    
    # Limits
    max_repos: int = Field(1, description="Maximum repositories")
    max_runs_per_month: int = Field(10, description="Maximum runs per month")
    max_users: int = Field(3, description="Maximum users")
    
    # Usage tracking
    repos_connected: int = Field(0, description="Currently connected repos")
    runs_this_month: int = Field(0, description="Runs used this month")
    users_count: int = Field(0, description="Current user count")
    
    # Billing
    stripe_customer_id: Optional[str] = None
    billing_email: Optional[str] = None
    
    # Settings
    default_llm_provider: str = Field("openai", description="Default LLM provider")
    auto_deploy_enabled: bool = Field(False, description="Enable auto-deploy to prod")
    auto_repair_enabled: bool = Field(True, description="Enable auto-repair")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class User(BaseModel):
    """
    User within a tenant.
    """
    id: str = Field(..., description="Unique user ID")
    tenant_id: str = Field(..., description="Parent tenant ID")
    
    # Profile
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    role: str = Field("member", enum=["admin", "member", "viewer"])
    
    # Auth
    auth_provider: str = Field(..., description="Auth provider: email, github, gitlab, sso")
    auth_provider_id: Optional[str] = None
    
    # Permissions
    can_submit_requirements: bool = True
    can_approve_gates: bool = True
    can_manage_repos: bool = False
    can_manage_billing: bool = False
    
    # Activity
    last_login_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class Repo(BaseModel):
    """
    Connected repository.
    """
    id: str = Field(..., description="Unique repo ID")
    tenant_id: str = Field(..., description="Parent tenant ID")
    
    # Platform details
    platform: RepoPlatform = Field(..., description="Platform: github, gitlab")
    platform_repo_id: Optional[int] = Field(None, description="Platform's repo ID")
    
    # Repo identity
    owner: str = Field(..., description="Repo owner/org")
    name: str = Field(..., description="Repo name")
    full_name: str = Field(..., description="Full name: owner/name")
    
    # Connection
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    connected_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    
    # Codebase graph status
    codebase_graph_built: bool = False
    codebase_graph_version: Optional[str] = None
    last_graph_update: Optional[datetime] = None
    
    # CI/CD integration
    ci_platform: Optional[str] = Field(None, description="CI platform: github_actions, jenkins, argocd")
    ci_configured: bool = False
    
    # Main branch
    default_branch: str = Field("main", description="Default branch name")
    
    # Metadata
    language: Optional[str] = None
    description: Optional[str] = None
    private: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_platform_url(self) -> str:
        """Get platform URL for this repo."""
        if self.platform == RepoPlatform.GITHUB:
            return f"https://github.com/{self.full_name}"
        elif self.platform == RepoPlatform.GITLAB:
            return f"https://gitlab.com/{self.full_name}"
        return ""
    
    class Config:
        frozen = False


class SourceProfile(BaseModel):
    """
    Profile for a source system (repo, CI/CD, observability).
    """
    id: str = Field(..., description="Unique profile ID")
    tenant_id: str = Field(..., description="Parent tenant ID")
    
    # Source type
    source_type: str = Field(..., description="Type: repo, ci, observability, issue_tracker")
    provider: str = Field(..., description="Provider: github, jenkins, datadog, etc.")
    
    # Connection
    connection_config: dict = Field(..., description="Connection configuration")
    credentials_ref: str = Field(..., description="Reference to stored credentials")
    
    # Status
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_health_check: Optional[datetime] = None
    health_error: Optional[str] = None
    
    # Usage
    used_by_repos: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class Subscription(BaseModel):
    """
    Subscription record for billing.
    """
    id: str = Field(..., description="Unique subscription ID")
    tenant_id: str = Field(..., description="Parent tenant ID")
    
    # Plan
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    
    # Pricing
    monthly_price_usd: float = Field(..., description="Monthly price in USD")
    annual_price_usd: Optional[float] = None
    
    # Billing cycle
    billing_cycle: str = Field("monthly", enum=["monthly", "annual"])
    current_period_start: datetime = Field(..., description="Current period start")
    current_period_end: datetime = Field(..., description="Current period end")
    
    # Status
    status: str = Field("active", enum=["active", "cancelled", "past_due", "trialing"])
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    
    # Stripe integration
    stripe_subscription_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    
    # Usage tracking
    usage_this_period: dict = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class AuditLog(BaseModel):
    """
    Audit log entry.
    """
    id: str = Field(..., description="Unique log ID")
    tenant_id: str = Field(..., description="Parent tenant ID")
    
    # Action
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    
    # Actor
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    is_system: bool = False  # System-initiated action
    
    # Details
    details: dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False
