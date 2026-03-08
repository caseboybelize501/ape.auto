"""
APE - Autonomous Production Engineer
Contract: Deploy Models

Immutable Pydantic schemas for deployment,
CI/CD integration, and production promotion.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DeployStatus(str, Enum):
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


class DeployEnvironment(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    SHADOW = "shadow"


class DeployStrategy(str, Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PRStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    APPROVED = "approved"
    MERGED = "merged"
    CLOSED = "closed"


class PullRequest(BaseModel):
    """
    Pull request created by APE for human review (GATE-2).
    """
    id: str = Field(..., description="Unique PR ID")
    run_id: str = Field(..., description="Associated generation run ID")
    repo_id: str = Field(..., description="Repository ID")
    
    # Platform details
    platform: str = Field(..., description="Platform: github, gitlab")
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    
    # Content
    title: str = Field(..., description="PR title")
    description: str = Field(..., description="PR description with context")
    branch_name: str = Field(..., description="Source branch name")
    target_branch: str = Field("main", description="Target branch")
    
    # Files changed
    files_changed: list[str] = Field(default_factory=list)
    additions: int = Field(0, description="Lines added")
    deletions: int = Field(0, description="Lines deleted")
    
    # Status
    status: PRStatus = PRStatus.DRAFT
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    merged: bool = False
    merged_at: Optional[datetime] = None
    
    # CI/CD status
    ci_status: str = Field("pending", enum=["pending", "running", "success", "failure"])
    ci_url: Optional[str] = None
    regression_tests: Optional[str] = None
    contract_tests: Optional[str] = None
    acceptance_tests: Optional[str] = None
    
    # Review
    review_comments: list[dict] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class Deployment(BaseModel):
    """
    Deployment record for staging or production.
    """
    id: str = Field(..., description="Unique deployment ID")
    run_id: str = Field(..., description="Associated generation run ID")
    pr_id: str = Field(..., description="Associated PR ID")
    repo_id: str = Field(..., description="Repository ID")
    
    # Environment
    environment: DeployEnvironment = Field(..., description="Target environment")
    environment_url: Optional[str] = None
    
    # Strategy
    strategy: DeployStrategy = DeployStrategy.ROLLING
    canary_percentage: Optional[float] = None
    
    # Version info
    commit_sha: Optional[str] = None
    image_tag: Optional[str] = None
    version: Optional[str] = None
    
    # Status
    status: DeployStatus = DeployStatus.PENDING
    health_status: HealthStatus = HealthStatus.UNKNOWN
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Health checks
    health_check_url: Optional[str] = None
    health_check_result: Optional[dict] = None
    
    # Rollback info
    rollback_available: bool = True
    rollback_commit_sha: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    class Config:
        frozen = False


class DeploymentMetrics(BaseModel):
    """
    Metrics collected during/after deployment.
    """
    deployment_id: str = Field(..., description="Associated deployment ID")
    
    # Error rate
    error_rate_before: float = Field(..., description="Error rate before deploy")
    error_rate_after: float = Field(..., description="Error rate after deploy")
    error_rate_change_percent: float = Field(..., description="Percentage change")
    
    # Latency
    p50_latency_before: float = Field(..., description="P50 latency before (ms)")
    p50_latency_after: float = Field(..., description="P50 latency after (ms)")
    p99_latency_before: float = Field(..., description="P99 latency before (ms)")
    p99_latency_after: float = Field(..., description="P99 latency after (ms)")
    
    # Throughput
    requests_per_second_before: float = Field(..., description="RPS before")
    requests_per_second_after: float = Field(..., description="RPS after")
    
    # Custom metrics
    custom_metrics: dict = Field(default_factory=dict)
    
    # Assessment
    regression_detected: bool = False
    regression_severity: Optional[str] = None
    
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class RollbackInfo(BaseModel):
    """
    Information about a rollback operation.
    """
    deployment_id: str = Field(..., description="Deployment being rolled back")
    reason: str = Field(..., description="Reason for rollback")
    trigger: str = Field(..., description="What triggered rollback: auto, manual")
    
    # Rollback target
    target_commit_sha: str = Field(..., description="Commit to roll back to")
    target_version: Optional[str] = None
    
    # Status
    status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed"])
    error_message: Optional[str] = None
    
    # Timing
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class SmokeTest(BaseModel):
    """
    Post-deploy smoke test.
    """
    id: str = Field(..., description="Unique smoke test ID")
    deployment_id: str = Field(..., description="Associated deployment")
    
    # Test definition
    name: str = Field(..., description="Smoke test name")
    endpoint: str = Field(..., description="Endpoint to test")
    method: str = Field("GET", description="HTTP method")
    expected_status: int = Field(200, description="Expected HTTP status")
    
    # Result
    status: str = Field("pending", enum=["pending", "passed", "failed", "skipped"])
    actual_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    
    executed_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class DeployApproval(BaseModel):
    """
    Human approval record for deployment gates.
    """
    deployment_id: str = Field(..., description="Deployment being approved")
    gate: str = Field(..., description="Gate: GATE-2 (PR), GATE-3 (prod deploy)")
    
    # Decision
    approved: bool = Field(..., description="Approval decision")
    approver: str = Field(..., description="User who approved")
    notes: Optional[str] = Field(None, description="Approval notes")
    
    # Context at approval time
    pr_status: Optional[dict] = None
    test_results: Optional[dict] = None
    staging_metrics: Optional[dict] = None
    
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True
