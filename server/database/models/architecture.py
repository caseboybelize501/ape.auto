"""
APE - Autonomous Production Engineer
Architecture Models

SQLAlchemy models for architecture planning entities.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class ChangeTypeEnum(str, enum.Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"
    MOVE = "move"


class RiskLevelEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategoryEnum(str, enum.Enum):
    SECURITY = "security"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    TECHNICAL_DEBT = "technical_debt"


class ArchitecturePlanModel(Base):
    """
    Architecture plan for implementing a requirement.
    """
    __tablename__ = "architecture_plans"

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey("requirements.id"), unique=True, nullable=False)
    repo_id = Column(String, nullable=False)

    # Status tracking
    status = Column(String, default="draft")  # draft, pending_approval, approved, rejected, revised
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Codebase patterns
    existing_patterns = Column(JSON, default=dict)
    test_patterns = Column(JSON, default=dict)
    naming_conventions = Column(JSON, default=dict)

    # Relationships
    requirement = relationship("RequirementModel", back_populates="architecture_plan")
    modified_modules = relationship(
        "ModuleChangeModel",
        back_populates="architecture_plan",
        cascade="all, delete-orphan"
    )
    new_modules = relationship(
        "ModuleSpecModel",
        back_populates="architecture_plan",
        cascade="all, delete-orphan"
    )
    risk_flags = relationship(
        "RiskModel",
        back_populates="architecture_plan",
        cascade="all, delete-orphan"
    )
    generation_run = relationship(
        "GenerationRunModel",
        back_populates="architecture_plan",
        uselist=False,
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<ArchitecturePlanModel(id={self.id}, status={self.status})>"


class ModuleChangeModel(Base):
    """
    Specification for modifying an existing module.
    """
    __tablename__ = "module_changes"

    id = Column(String, primary_key=True)
    architecture_plan_id = Column(String, ForeignKey("architecture_plans.id"), nullable=False)
    
    path = Column(String, nullable=False)
    change_type = Column(SQLEnum(ChangeTypeEnum), nullable=False)
    description = Column(Text, nullable=False)
    affected_functions = Column(JSON, default=list)
    new_functions = Column(JSON, default=list)
    removed_functions = Column(JSON, default=list)
    estimated_complexity = Column(String(20), default="medium")

    # Relationship
    architecture_plan = relationship("ArchitecturePlanModel", back_populates="modified_modules")

    def __repr__(self):
        return f"<ModuleChangeModel(path={self.path}, change_type={self.change_type})>"


class ModuleSpecModel(Base):
    """
    Specification for a new module to be created.
    """
    __tablename__ = "module_specs"

    id = Column(String, primary_key=True)
    architecture_plan_id = Column(String, ForeignKey("architecture_plans.id"), nullable=False)
    
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    exports = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    estimated_complexity = Column(String(20), default="medium")

    # Relationship
    architecture_plan = relationship("ArchitecturePlanModel", back_populates="new_modules")

    def __repr__(self):
        return f"<ModuleSpecModel(name={self.name}, path={self.path})>"


class RiskModel(Base):
    """
    Identified risk in the architecture.
    """
    __tablename__ = "risks"

    id = Column(String, primary_key=True)
    architecture_plan_id = Column(String, ForeignKey("architecture_plans.id"), nullable=False)
    
    category = Column(SQLEnum(RiskCategoryEnum), nullable=False)
    level = Column(SQLEnum(RiskLevelEnum), nullable=False)
    description = Column(Text, nullable=False)
    mitigation = Column(Text, nullable=True)
    affected_areas = Column(JSON, default=list)

    # Relationship
    architecture_plan = relationship("ArchitecturePlanModel", back_populates="risk_flags")

    def __repr__(self):
        return f"<RiskModel(id={self.id}, level={self.level})>"
