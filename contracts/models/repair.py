"""
APE - Autonomous Production Engineer
Contract: Repair Models

Immutable Pydantic schemas for micro-repair loop,
repair context, and repair tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RepairStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    HALTED = "halted"


class RepairTrigger(str, Enum):
    CRITIC_FAIL = "critic_fail"
    TEST_FAIL = "test_fail"
    PRODUCTION_REGRESSION = "production_regression"
    MANUAL_REQUEST = "manual_request"


class RepairScope(str, Enum):
    FILE = "file"
    MODULE = "module"
    RUN = "run"


class RepairContext(BaseModel):
    """
    Context assembled for a repair attempt.
    This is the complete information provided to the LLM for repair.
    """
    repair_id: str = Field(..., description="Unique repair ID")
    scope: RepairScope = Field(RepairScope.FILE, description="Repair scope")
    trigger: RepairTrigger = Field(..., description="What triggered the repair")
    
    # Target file
    file_path: str = Field(..., description="File to repair")
    current_content: str = Field(..., description="Current file content")
    language: str = Field("python", description="File language")
    
    # Failure context
    failing_passes: list[str] = Field(default_factory=list, description="Which critic passes failed")
    error_details: dict = Field(default_factory=dict, description="Detailed error information")
    test_failures: list[dict] = Field(default_factory=list, description="Failed tests if test-triggered")
    
    # Immutable references
    contract: Optional[str] = Field(None, description="Relevant contract file content")
    fr_refs: list[str] = Field(default_factory=list, description="Functional requirements this file satisfies")
    
    # History
    prior_attempts: list[dict] = Field(default_factory=list, description="Previous repair attempts")
    
    # Codebase context
    codebase_patterns: dict = Field(default_factory=dict, description="Style patterns from codebase")
    dependency_outputs: dict = Field(default_factory=dict, description="Outputs from dependencies")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True


class RepairInstruction(BaseModel):
    """
    Instruction template for repair LLM.
    """
    scope: RepairScope = Field(..., description="Scope this instruction applies to")
    trigger_type: RepairTrigger = Field(..., description="Trigger type")
    
    # Core instruction
    primary_instruction: str = Field(..., description="Primary repair instruction")
    
    # Constraints
    constraints: list[str] = Field(default_factory=list, description="Constraints LLM must follow")
    
    # Examples (few-shot)
    examples: list[dict] = Field(default_factory=list, description="Few-shot examples")
    
    # Output format
    output_format: str = Field("complete_file", description="Expected output format")
    
    class Config:
        frozen = True


class RepairResult(BaseModel):
    """
    Result of a repair attempt.
    """
    repair_id: str = Field(..., description="Unique repair ID")
    attempt_number: int = Field(..., ge=1, description="Attempt number")
    
    # Input
    original_content: str = Field(..., description="Content before repair")
    repair_context: RepairContext = Field(..., description="Context provided to LLM")
    
    # Output
    repaired_content: Optional[str] = None
    changes_summary: Optional[str] = Field(None, description="LLM summary of changes made")
    
    # Validation
    post_repair_validation: dict = Field(default_factory=dict, description="Validation results after repair")
    critic_rerun_result: Optional[dict] = None
    test_rerun_result: Optional[dict] = None
    
    # Status
    success: bool = False
    failure_reason: Optional[str] = None
    
    # Metrics
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class MicroRepairConfig(BaseModel):
    """
    Configuration for micro-repair loop.
    """
    max_attempts: int = Field(3, ge=1, description="Maximum repair attempts per file")
    timeout_seconds: int = Field(300, ge=60, description="Timeout per repair attempt")
    
    # What to include in context
    include_contract: bool = Field(True, description="Include contract in context")
    include_fr_refs: bool = Field(True, description="Include FR references")
    include_prior_attempts: bool = Field(True, description="Include prior attempt history")
    include_codebase_patterns: bool = Field(True, description="Include codebase patterns")
    
    # Validation after repair
    rerun_all_critic_passes: bool = Field(True, description="Rerun all 4 critic passes after repair")
    rerun_level_tests: bool = Field(False, description="Rerun tests for entire level after repair")
    
    # Halt conditions
    halt_on_uncertain: bool = Field(False, description="Halt if LLM returns 'uncertain'")
    halt_on_repeated_failure: bool = Field(True, description="Halt after max_attempts failures")
    
    class Config:
        frozen = True


class ProductionRegressionSignal(BaseModel):
    """
    Signal indicating a production regression.
    """
    id: str = Field(..., description="Unique signal ID")
    deployment_id: str = Field(..., description="Associated deployment ID")
    signal_type: str = Field(..., description="Type: error_rate, latency, sentry_fingerprint, custom")
    
    # Signal details
    metric_name: str = Field(..., description="Metric that regressed")
    baseline_value: float = Field(..., description="Baseline value before deploy")
    current_value: float = Field(..., description="Current value after deploy")
    regression_percentage: float = Field(..., description="Percentage regression")
    
    # Localization
    affected_files: list[str] = Field(default_factory=list, description="Files likely causing regression")
    affected_lines: list[int] = Field(default_factory=list, description="Specific lines if traceable")
    sentry_fingerprint: Optional[str] = Field(None, description="Sentry fingerprint if applicable")
    error_traceback: Optional[str] = Field(None, description="Error traceback if available")
    
    # Severity
    severity: str = Field("medium", enum=["low", "medium", "high", "critical"])
    auto_rollback_triggered: bool = False
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class SelfRepairSession(BaseModel):
    """
    Complete self-repair session for production regression.
    """
    id: str = Field(..., description="Unique session ID")
    deployment_id: str = Field(..., description="Deployment being repaired")
    regression_signal_id: str = Field(..., description="Triggering regression signal")
    
    # Localization phase
    localized_file: Optional[str] = None
    localized_line: Optional[int] = None
    reproduced: bool = False
    reproduction_test: Optional[str] = None
    
    # Repair attempts
    repair_attempts: list[RepairResult] = Field(default_factory=list)
    
    # Shadow deployment
    shadow_deployed: bool = False
    shadow_url: Optional[str] = None
    shadow_results: Optional[dict] = None
    
    # Final outcome
    success: bool = False
    promoted_to_prod: bool = False
    rollback_triggered: bool = False
    halted: bool = False
    halt_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        frozen = False
