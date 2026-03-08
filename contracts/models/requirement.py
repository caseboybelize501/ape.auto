"""
APE - Autonomous Production Engineer
Contract: Requirement Models

Immutable Pydantic schemas for requirement specification.
These models define the structure of functional requirements,
non-functional requirements, and acceptance criteria.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import hashlib


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AMBIGUOUS = "ambiguous"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class FunctionalRequirement(BaseModel):
    """
    A functional requirement describes a specific behavior or feature.
    Format: verb + noun + acceptance criteria
    """
    id: str = Field(..., description="Unique identifier, e.g., FR-001")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    verb: str = Field(..., description="Action verb, e.g., 'create', 'update', 'validate'")
    noun: str = Field(..., description="Target entity, e.g., 'user session', 'API endpoint'")
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    
    class Config:
        frozen = True  # Immutable after creation


class NonFunctionalRequirement(BaseModel):
    """
    Non-functional requirements: performance, security, scalability.
    """
    id: str = Field(..., description="Unique identifier, e.g., NFR-001")
    category: str = Field(..., description="Category: performance, security, scalability, reliability")
    description: str = Field(..., min_length=1)
    metric: Optional[str] = Field(None, description="Measurable metric, e.g., 'p99 latency < 200ms'")
    threshold: Optional[str] = Field(None, description="Acceptable threshold value")
    
    class Config:
        frozen = True


class Criterion(BaseModel):
    """
    Binary pass/fail acceptance criterion for testing.
    """
    id: str = Field(..., description="Unique identifier, e.g., AC-001")
    description: str = Field(..., min_length=1)
    testable: bool = Field(True, description="Must be binary pass/fail")
    automated: bool = Field(True, description="Can be automated as a test")
    
    class Config:
        frozen = True


class Question(BaseModel):
    """
    Ambiguity that requires human clarification before implementation.
    """
    id: str = Field(..., description="Unique identifier, e.g., Q-001")
    question: str = Field(..., min_length=1)
    context: str = Field(..., description="Why this question matters")
    suggested_answer: Optional[str] = Field(None, description="AI-suggested answer")
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class RequirementSpec(BaseModel):
    """
    Complete requirement specification extracted from raw input.
    This is the ground truth for all downstream generation.
    """
    id: str = Field(..., description="Unique requirement specification ID")
    repo_id: str = Field(..., description="Target repository ID")
    raw_text: str = Field(..., description="Original requirement text")
    source: str = Field(..., description="Source: ticket, PRD, voice, manual")
    source_id: Optional[str] = Field(None, description="Original ticket/PRD ID if applicable")
    
    functional: list[FunctionalRequirement] = Field(default_factory=list)
    non_functional: list[NonFunctionalRequirement] = Field(default_factory=list)
    affected_modules: list[str] = Field(default_factory=list)
    new_modules: list[str] = Field(default_factory=list)
    acceptance_criteria: list[Criterion] = Field(default_factory=list)
    ambiguities: list[Question] = Field(default_factory=list)
    
    priority: Priority = Priority.MEDIUM
    status: RequirementStatus = RequirementStatus.DRAFT
    
    # Immutable hash for deduplication
    requirement_hash: str = Field(..., description="SHA256 of normalized requirement")
    codebase_snapshot_hash: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    @classmethod
    def compute_hash(cls, raw_text: str, repo_id: str) -> str:
        """Compute deterministic hash for deduplication."""
        content = f"{repo_id}:{raw_text.strip().lower()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def has_unresolved_ambiguities(self) -> bool:
        """Check if any ambiguities need human resolution."""
        return any(not q.resolved for q in self.ambiguities)
    
    def get_unresolved_questions(self) -> list[Question]:
        """Return list of unresolved questions."""
        return [q for q in self.ambiguities if not q.resolved]
