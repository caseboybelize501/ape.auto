"""
APE - Autonomous Production Engineer
Tenant Models

SQLAlchemy models for multi-tenancy: tenants, users, repos, subscriptions.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class TenantStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SubscriptionTierEnum(str, enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class RepoPlatformEnum(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ConnectionStatusEnum(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTH_EXPIRED = "auth_expired"


class TenantModel(Base):
    """
    Multi-tenant organization.
    """
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    # Contact
    admin_email = Column(String, nullable=False)
    company_name = Column(String, nullable=True)

    # Subscription
    tier = Column(SQLEnum(SubscriptionTierEnum), default=SubscriptionTierEnum.STARTER)
    status = Column(SQLEnum(TenantStatusEnum), default=TenantStatusEnum.PENDING)

    # Limits
    max_repos = Column(Integer, default=1)
    max_runs_per_month = Column(Integer, default=10)
    max_users = Column(Integer, default=3)

    # Usage tracking
    repos_connected = Column(Integer, default=0)
    runs_this_month = Column(Integer, default=0)
    users_count = Column(Integer, default=0)

    # Billing
    stripe_customer_id = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)

    # Settings
    default_llm_provider = Column(String, default="openai")
    auto_deploy_enabled = Column(Boolean, default=False)
    auto_repair_enabled = Column(Boolean, default=True)

    # Relationships
    users = relationship(
        "UserModel",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    repos = relationship(
        "RepoModel",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "SubscriptionModel",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TenantModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    """
    User within a tenant.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # Profile
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="member")  # admin, member, viewer

    # Auth
    auth_provider = Column(String, nullable=False)  # email, github, gitlab, sso
    auth_provider_id = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # For email auth

    # Permissions
    can_submit_requirements = Column(Boolean, default=True)
    can_approve_gates = Column(Boolean, default=True)
    can_manage_repos = Column(Boolean, default=False)
    can_manage_billing = Column(Boolean, default=False)

    # Activity
    last_login_at = Column(DateTime, nullable=True)

    # Relationship
    tenant = relationship("TenantModel", back_populates="users")

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email})>"


class RepoModel(Base):
    """
    Connected repository.
    """
    __tablename__ = "repos"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # Platform details
    platform = Column(SQLEnum(RepoPlatformEnum), nullable=False)
    platform_repo_id = Column(Integer, nullable=True)

    # Repo identity
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    # Connection
    connection_status = Column(SQLEnum(ConnectionStatusEnum), default=ConnectionStatusEnum.DISCONNECTED)
    connected_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Codebase graph status
    codebase_graph_built = Column(Boolean, default=False)
    codebase_graph_version = Column(String, nullable=True)
    last_graph_update = Column(DateTime, nullable=True)

    # CI/CD integration
    ci_platform = Column(String, nullable=True)
    ci_configured = Column(Boolean, default=False)

    # Main branch
    default_branch = Column(String, default="main")

    # Metadata
    language = Column(String, nullable=True)
    description = Column(String, nullable=True)
    private = Column(Boolean, default=True)

    # Relationship
    tenant = relationship("TenantModel", back_populates="repos")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RepoModel(full_name={self.full_name}, platform={self.platform})>"


class SubscriptionModel(Base):
    """
    Subscription record for billing.
    """
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # Plan
    tier = Column(SQLEnum(SubscriptionTierEnum), nullable=False)

    # Pricing
    monthly_price_usd = Column(Float, nullable=False)
    annual_price_usd = Column(Float, nullable=True)

    # Billing cycle
    billing_cycle = Column(String, default="monthly")
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)

    # Status
    status = Column(String, default="active")  # active, cancelled, past_due, trialing
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)

    # Stripe integration
    stripe_subscription_id = Column(String, nullable=True)
    stripe_price_id = Column(String, nullable=True)

    # Usage tracking
    usage_this_period = Column(JSON, default=dict)

    # Relationship
    tenant = relationship("TenantModel", back_populates="subscriptions")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SubscriptionModel(tenant_id={self.tenant_id}, tier={self.tier})>"
