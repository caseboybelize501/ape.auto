"""
APE - Autonomous Production Engineer
Requirement Models

SQLAlchemy models for requirements and related entities.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AMBIGUOUS = "ambiguous"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class RequirementModel(Base):
    """
    Main requirement specification table.
    """
    __tablename__ = "requirements"

    id = Column(String, primary_key=True)
    repo_id = Column(String, nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    source = Column(String, default="manual")
    source_id = Column(String, nullable=True)

    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.MEDIUM)
    status = Column(SQLEnum(RequirementStatusEnum), default=RequirementStatusEnum.DRAFT)

    requirement_hash = Column(String, unique=True, nullable=False, index=True)
    codebase_snapshot_hash = Column(String, nullable=True)

    # Relationships
    functional_requirements = relationship(
        "FunctionalRequirementModel",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )
    non_functional_requirements = relationship(
        "NonFunctionalRequirementModel",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )
    acceptance_criteria = relationship(
        "CriterionModel",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )
    ambiguities = relationship(
        "QuestionModel",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )
    architecture_plan = relationship(
        "ArchitecturePlanModel",
        back_populates="requirement",
        uselist=False,
        cascade="all, delete-orphan"
    )
    generation_runs = relationship(
        "GenerationRunModel",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<RequirementModel(id={self.id}, status={self.status})>"


class FunctionalRequirementModel(Base):
    """
    Functional requirements (FR-N).
    """
    __tablename__ = "functional_requirements"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    verb = Column(String(50), nullable=False)
    noun = Column(String(100), nullable=False)
    acceptance_criteria = Column(JSON, default=list)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.MEDIUM)

    # Relationship
    requirement = relationship("RequirementModel", back_populates="functional_requirements")

    def __repr__(self):
        return f"<FunctionalRequirementModel(id={self.id}, title={self.title})>"


class NonFunctionalRequirementModel(Base):
    """
    Non-functional requirements (NFR-N).
    """
    __tablename__ = "non_functional_requirements"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    
    category = Column(String(50), nullable=False)  # performance, security, scalability, etc.
    description = Column(Text, nullable=False)
    metric = Column(String(200), nullable=True)
    threshold = Column(String(200), nullable=True)

    # Relationship
    requirement = relationship("RequirementModel", back_populates="non_functional_requirements")

    def __repr__(self):
        return f"<NonFunctionalRequirementModel(id={self.id}, category={self.category})>"


class CriterionModel(Base):
    """
    Acceptance criteria (binary pass/fail).
    """
    __tablename__ = "acceptance_criteria"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    
    description = Column(Text, nullable=False)
    testable = Column(Boolean, default=True)
    automated = Column(Boolean, default=True)

    # Relationship
    requirement = relationship("RequirementModel", back_populates="acceptance_criteria")

    def __repr__(self):
        return f"<CriterionModel(id={self.id})>"


class QuestionModel(Base):
    """
    Ambiguity questions requiring human resolution.
    """
    __tablename__ = "ambiguity_questions"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    
    question = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    suggested_answer = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)

    # Relationship
    requirement = relationship("RequirementModel", back_populates="ambiguities")

    def __repr__(self):
        return f"<QuestionModel(id={self.id}, resolved={self.resolved})>"
