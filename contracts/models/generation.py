"""
APE - Autonomous Production Engineer
Contract: Generation Models

Immutable Pydantic schemas for code generation jobs,
critic results, and generation tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REPAIRING = "repairing"


class CriticPassResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"


class CriticPassType(str, Enum):
    SYNTAX = "syntax"
    CONTRACT = "contract"
    COMPLETENESS = "completeness"
    LOGIC = "logic"


class GenerationJob(BaseModel):
    """
    A single file generation job.
    """
    id: str = Field(..., description="Unique job ID")
    run_id: str = Field(..., description="Parent run ID")
    level: int = Field(..., description="Topological level")
    
    file_path: str = Field(..., description="Target file path")
    file_type: str = Field(..., description="File type: source, test, config")
    language: str = Field("python", description="File language")
    
    # Context for generation
    node_spec: dict = Field(..., description="Node specification from DependencyGraph")
    relevant_contracts: list[str] = Field(default_factory=list, description="Contract files to reference")
    fr_refs: list[str] = Field(default_factory=list, description="Functional requirements to satisfy")
    codebase_patterns: dict = Field(default_factory=dict, description="Patterns from CodebaseGraph")
    dependency_outputs: dict = Field(default_factory=dict, description="Outputs from previous levels")
    
    # Generation result
    generated_content: Optional[str] = None
    generation_prompt_tokens: Optional[int] = None
    generation_completion_tokens: Optional[int] = None
    generation_model: Optional[str] = None
    
    # Status tracking
    status: GenerationStatus = GenerationStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = Field(0, ge=0)
    max_retries: int = Field(3, ge=1)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class SyntaxErrorDetail(BaseModel):
    """
    Detailed syntax error information.
    """
    line: int = Field(..., description="Line number of error")
    column: int = Field(..., description="Column number of error")
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of syntax error")


class ContractViolationDetail(BaseModel):
    """
    Detailed contract violation information.
    """
    contract_file: str = Field(..., description="Contract file with the spec")
    violation_type: str = Field(..., description="Type: signature_mismatch, missing_import, type_error")
    expected: str = Field(..., description="What was expected per contract")
    actual: str = Field(..., description="What was found in generated code")
    line: Optional[int] = None


class CriticResult(BaseModel):
    """
    Result of running the 4-pass critic on a single file.
    """
    job_id: str = Field(..., description="Associated generation job ID")
    file_path: str = Field(..., description="File being critiqued")
    level: int = Field(..., description="Topological level")
    
    # Pass 1: Syntax
    pass1_result: CriticPassResult = CriticPassResult.SKIPPED
    pass1_errors: list[SyntaxErrorDetail] = Field(default_factory=list)
    pass1_duration_ms: Optional[int] = None
    
    # Pass 2: Contract compliance
    pass2_result: CriticPassResult = CriticPassResult.SKIPPED
    pass2_violations: list[ContractViolationDetail] = Field(default_factory=list)
    pass2_duration_ms: Optional[int] = None
    
    # Pass 3: Completeness (LLM-judged)
    pass3_result: CriticPassResult = CriticPassResult.SKIPPED
    pass3_score: Optional[str] = Field(None, enum=["complete", "partial", "stub"])
    pass3_reasoning: Optional[str] = None
    pass3_duration_ms: Optional[int] = None
    
    # Pass 4: Logic correctness (LLM-judged)
    pass4_result: CriticPassResult = CriticPassResult.SKIPPED
    pass4_score: Optional[str] = Field(None, enum=["correct", "incorrect", "uncertain"])
    pass4_reasoning: Optional[str] = None
    pass4_errors: list[str] = Field(default_factory=list)
    pass4_duration_ms: Optional[int] = None
    
    # Overall result
    overall_result: CriticPassResult = CriticPassResult.SKIPPED
    repair_count: int = Field(0, ge=0)
    
    run_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None
    
    def all_passes_passed(self) -> bool:
        """Check if all 4 passes passed."""
        return (
            self.pass1_result == CriticPassResult.PASS and
            self.pass2_result == CriticPassResult.PASS and
            self.pass3_result == CriticPassResult.PASS and
            self.pass4_result == CriticPassResult.PASS
        )
    
    def get_failing_passes(self) -> list[CriticPassType]:
        """Return list of failing pass types."""
        failing = []
        if self.pass1_result != CriticPassResult.PASS:
            failing.append(CriticPassType.SYNTAX)
        if self.pass2_result != CriticPassResult.PASS:
            failing.append(CriticPassType.CONTRACT)
        if self.pass3_result != CriticPassResult.PASS:
            failing.append(CriticPassType.COMPLETENESS)
        if self.pass4_result != CriticPassResult.PASS:
            failing.append(CriticPassType.LOGIC)
        return failing


class LevelCriticResult(BaseModel):
    """
    Aggregated critic results for an entire level.
    """
    run_id: str = Field(..., description="Parent run ID")
    level: int = Field(..., description="Topological level")
    
    file_results: list[CriticResult] = Field(default_factory=list)
    
    # Aggregated stats
    total_files: int = Field(..., description="Total files in level")
    passed_files: int = Field(0, description="Files that passed all 4 passes")
    failed_files: int = Field(0, description="Files that failed any pass")
    repaired_files: int = Field(0, description="Files that required repair")
    
    # Level status
    level_result: str = Field("pending", enum=["pending", "pass", "fail", "halt"])
    halt_reason: Optional[str] = None
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    def all_files_passed(self) -> bool:
        """Check if all files in level passed."""
        return self.failed_files == 0 and self.level_result == "pass"


class RepairAttempt(BaseModel):
    """
    Record of a repair attempt on a file.
    """
    id: str = Field(..., description="Unique repair attempt ID")
    job_id: str = Field(..., description="Associated generation job ID")
    attempt_number: int = Field(..., ge=1, description="Attempt number (1, 2, 3)")
    
    # Context provided to LLM
    failing_passes: list[CriticPassType] = Field(default_factory=list)
    error_details: dict = Field(default_factory=dict)
    original_content: str = Field(..., description="Content before repair")
    
    # Repair result
    repaired_content: Optional[str] = None
    changes_made: Optional[str] = Field(None, description="LLM description of changes")
    
    # Result after re-running critic
    post_repair_result: Optional[CriticResult] = None
    success: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None


class HaltReport(BaseModel):
    """
    Report generated when critic blocks progress.
    Written to CRITIC_BLOCKED.md and triggers GATE-4.
    """
    id: str = Field(..., description="Unique halt report ID")
    run_id: str = Field(..., description="Parent run ID")
    level: int = Field(..., description="Blocked level")
    file_path: str = Field(..., description="Blocked file path")
    
    failing_passes: list[CriticPassType] = Field(default_factory=list)
    attempts: list[RepairAttempt] = Field(default_factory=list)
    
    # Recommendations
    recommended_action: Optional[str] = Field(None, description="LLM-suggested architectural change")
    alternative_approaches: list[str] = Field(default_factory=list)
    
    # Human response
    human_response: Optional[str] = Field(None, enum=["modify_architecture", "modify_requirement", "manual_fix", "skip_file"])
    human_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paged_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class GenerationRun(BaseModel):
    """
    Complete generation run tracking all levels.
    """
    id: str = Field(..., description="Unique run ID")
    requirement_spec_id: str = Field(..., description="Reference to RequirementSpec")
    architecture_plan_id: str = Field(..., description="Reference to ArchitecturePlan")
    build_plan_id: str = Field(..., description="Reference to BuildPlan")
    repo_id: str = Field(..., description="Repository ID")
    
    # Deduplication key
    dedup_key: str = Field(..., description="repo_id + requirement_hash + codebase_snapshot_hash")
    
    # Status
    status: GenerationStatus = GenerationStatus.PENDING
    current_level: int = Field(0, description="Current level being processed")
    total_levels: int = Field(0, description="Total levels to process")
    
    # Results
    level_results: list[LevelCriticResult] = Field(default_factory=list)
    halt_report: Optional[HaltReport] = None
    
    # Metrics
    total_files_generated: int = Field(0)
    total_files_passed: int = Field(0)
    total_repairs: int = Field(0)
    total_halts: int = Field(0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def is_blocked(self) -> bool:
        """Check if run is blocked by a halt."""
        return self.status == GenerationStatus.BLOCKED or self.halt_report is not None
    
    def is_complete(self) -> bool:
        """Check if run completed successfully."""
        return self.status == GenerationStatus.COMPLETED
