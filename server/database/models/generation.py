"""
APE - Autonomous Production Engineer
Generation Models

SQLAlchemy models for generation runs, jobs, and critic results.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class GenerationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REPAIRING = "repairing"


class CriticPassResultEnum(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"


class GenerationRunModel(Base):
    """
    Main generation run tracking.
    """
    __tablename__ = "generation_runs"

    id = Column(String, primary_key=True)
    requirement_spec_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    architecture_plan_id = Column(String, ForeignKey("architecture_plans.id"), nullable=True)
    repo_id = Column(String, nullable=False)

    # Deduplication
    dedup_key = Column(String, unique=True, nullable=False, index=True)

    # Status
    status = Column(SQLEnum(GenerationStatusEnum), default=GenerationStatusEnum.PENDING)
    current_level = Column(Integer, default=0)
    total_levels = Column(Integer, default=0)

    # Metrics
    total_files_generated = Column(Integer, default=0)
    total_files_passed = Column(Integer, default=0)
    total_repairs = Column(Integer, default=0)
    total_halts = Column(Integer, default=0)

    # Relationships
    requirement = relationship("RequirementModel", back_populates="generation_runs")
    architecture_plan = relationship("ArchitecturePlanModel", back_populates="generation_run")
    jobs = relationship(
        "GenerationJobModel",
        back_populates="run",
        cascade="all, delete-orphan"
    )
    level_results = relationship(
        "CriticResultModel",
        back_populates="run",
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<GenerationRunModel(id={self.id}, status={self.status})>"


class GenerationJobModel(Base):
    """
    Individual file generation job.
    """
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("generation_runs.id"), nullable=False)
    level = Column(Integer, nullable=False)

    file_path = Column(String, nullable=False)
    file_type = Column(String, default="source")
    language = Column(String, default="python")

    # Context
    node_spec = Column(JSON, default=dict)
    relevant_contracts = Column(JSON, default=list)
    fr_refs = Column(JSON, default=list)
    codebase_patterns = Column(JSON, default=dict)
    dependency_outputs = Column(JSON, default=dict)

    # Result
    generated_content = Column(Text, nullable=True)
    generation_prompt_tokens = Column(Integer, nullable=True)
    generation_completion_tokens = Column(Integer, nullable=True)
    generation_model = Column(String, nullable=True)

    # Status
    status = Column(SQLEnum(GenerationStatusEnum), default=GenerationStatusEnum.PENDING)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Relationship
    run = relationship("GenerationRunModel", back_populates="jobs")
    critic_results = relationship(
        "CriticResultModel",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<GenerationJobModel(file_path={self.file_path}, status={self.status})>"


class CriticResultModel(Base):
    """
    Critic results for a file or level.
    """
    __tablename__ = "critic_results"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("generation_runs.id"), nullable=False)
    job_id = Column(String, ForeignKey("generation_jobs.id"), nullable=True)
    level = Column(Integer, nullable=False)

    file_path = Column(String, nullable=True)  # Null for level-level results

    # Pass 1: Syntax
    pass1_result = Column(SQLEnum(CriticPassResultEnum), default=CriticPassResultEnum.SKIPPED)
    pass1_errors = Column(JSON, default=list)
    pass1_duration_ms = Column(Integer, nullable=True)

    # Pass 2: Contract
    pass2_result = Column(SQLEnum(CriticPassResultEnum), default=CriticPassResultEnum.SKIPPED)
    pass2_violations = Column(JSON, default=list)
    pass2_duration_ms = Column(Integer, nullable=True)

    # Pass 3: Completeness
    pass3_result = Column(SQLEnum(CriticPassResultEnum), default=CriticPassResultEnum.SKIPPED)
    pass3_score = Column(String(20), nullable=True)
    pass3_reasoning = Column(Text, nullable=True)
    pass3_duration_ms = Column(Integer, nullable=True)

    # Pass 4: Logic
    pass4_result = Column(SQLEnum(CriticPassResultEnum), default=CriticPassResultEnum.SKIPPED)
    pass4_score = Column(String(20), nullable=True)
    pass4_reasoning = Column(Text, nullable=True)
    pass4_errors = Column(JSON, default=list)
    pass4_duration_ms = Column(Integer, nullable=True)

    # Overall
    overall_result = Column(SQLEnum(CriticPassResultEnum), default=CriticPassResultEnum.SKIPPED)
    repair_count = Column(Integer, default=0)
    level_result = Column(String(20), nullable=True)  # pass/fail/halt for level results

    # Relationships
    run = relationship("GenerationRunModel", back_populates="level_results")
    job = relationship("GenerationJobModel", back_populates="critic_results")
    repair_attempts = relationship(
        "RepairAttemptModel",
        back_populates="critic_result",
        cascade="all, delete-orphan"
    )

    run_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<CriticResultModel(file_path={self.file_path}, overall={self.overall_result})>"


class RepairAttemptModel(Base):
    """
    Record of a repair attempt.
    """
    __tablename__ = "repair_attempts"

    id = Column(String, primary_key=True)
    critic_result_id = Column(String, ForeignKey("critic_results.id"), nullable=False)
    
    attempt_number = Column(Integer, nullable=False)
    job_id = Column(String, nullable=False)
    
    # Context
    failing_passes = Column(JSON, default=list)
    error_details = Column(JSON, default=dict)
    original_content = Column(Text, nullable=False)
    
    # Result
    repaired_content = Column(Text, nullable=True)
    changes_summary = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    
    # Metrics
    duration_ms = Column(Integer, nullable=True)

    # Relationship
    critic_result = relationship("CriticResultModel", back_populates="repair_attempts")

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RepairAttemptModel(attempt={self.attempt_number}, success={self.success})>"
