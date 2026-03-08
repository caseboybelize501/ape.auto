"""
APE - Autonomous Production Engineer
Deploy Models

SQLAlchemy models for deployments and pull requests.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class DeployStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    DEPLOYING_STAGING = "deploying_staging"
    STAGING_DEPLOYED = "staging_deployed"
    TESTING_STAGING = "testing_staging"
    PENDING_APPROVAL = "pending_approval"
    DEPLOYING_PROD = "deploying_prod"
    PROD_DEPLOYED = "prod_deployed"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DeployEnvironmentEnum(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    SHADOW = "shadow"


class DeployStrategyEnum(str, enum.Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class HealthStatusEnum(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PRStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    APPROVED = "approved"
    MERGED = "merged"
    CLOSED = "closed"


class PullRequestModel(Base):
    """
    Pull request created by APE.
    """
    __tablename__ = "pull_requests"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("generation_runs.id"), nullable=False)
    repo_id = Column(String, nullable=False)

    # Platform details
    platform = Column(String, nullable=False)  # github, gitlab
    pr_number = Column(Integer, nullable=True)
    pr_url = Column(String, nullable=True)

    # Content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    branch_name = Column(String, nullable=False)
    target_branch = Column(String, default="main")

    # Files changed
    files_changed = Column(JSON, default=list)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    # Status
    status = Column(SQLEnum(PRStatusEnum), default=PRStatusEnum.DRAFT)
    approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    merged = Column(Boolean, default=False)
    merged_at = Column(DateTime, nullable=True)

    # CI/CD status
    ci_status = Column(String, default="pending")
    ci_url = Column(String, nullable=True)

    # Deployment
    deployment = relationship(
        "DeploymentModel",
        back_populates="pull_request",
        uselist=False,
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PullRequestModel(pr_number={self.pr_number}, status={self.status})>"


class DeploymentModel(Base):
    """
    Deployment record for staging or production.
    """
    __tablename__ = "deployments"

    id = Column(String, primary_key=True)
    pr_id = Column(String, ForeignKey("pull_requests.id"), nullable=False)
    run_id = Column(String, nullable=False)
    repo_id = Column(String, nullable=False)

    # Environment
    environment = Column(SQLEnum(DeployEnvironmentEnum), nullable=False)
    environment_url = Column(String, nullable=True)

    # Strategy
    strategy = Column(SQLEnum(DeployStrategyEnum), default=DeployStrategyEnum.ROLLING)
    canary_percentage = Column(Float, nullable=True)

    # Version info
    commit_sha = Column(String, nullable=True)
    image_tag = Column(String, nullable=True)
    version = Column(String, nullable=True)

    # Status
    status = Column(SQLEnum(DeployStatusEnum), default=DeployStatusEnum.PENDING)
    health_status = Column(SQLEnum(HealthStatusEnum), default=HealthStatusEnum.UNKNOWN)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Health checks
    health_check_url = Column(String, nullable=True)
    health_check_result = Column(JSON, nullable=True)

    # Rollback info
    rollback_available = Column(Boolean, default=True)
    rollback_commit_sha = Column(String, nullable=True)

    # Relationship
    pull_request = relationship("PullRequestModel", back_populates="deployment")

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<DeploymentModel(id={self.id}, environment={self.environment})>"
