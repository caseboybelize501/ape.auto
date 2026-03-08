"""
APE - Autonomous Production Engineer
Test Models

SQLAlchemy models for test plans and test specifications.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from server.database.config import Base


class TestTypeEnum(str, enum.Enum):
    CONTRACT = "contract"
    ACCEPTANCE = "acceptance"
    REGRESSION = "regression"
    UNIT = "unit"
    INTEGRATION = "integration"
    PROPERTY = "property"


class TestResultEnum(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"
    XFAIL = "xfail"


class TestPlanModel(Base):
    """
    Test plan for a generation run.
    """
    __tablename__ = "test_plans"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("generation_runs.id"), nullable=False)
    requirement_spec_id = Column(String, ForeignKey("requirements.id"), nullable=False)

    # Status
    status = Column(String, default="pending")  # pending, generating, generated, executing, completed, failed

    # Execution order
    execution_order = Column(JSON, default=list)

    # Relationships
    generation_run = relationship("GenerationRunModel", backref="test_plans")
    requirement = relationship("RequirementModel")
    test_specs = relationship(
        "TestSpecModel",
        back_populates="test_plan",
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TestPlanModel(id={self.id}, status={self.status})>"


class TestSpecModel(Base):
    """
    Test specification for a single test.
    """
    __tablename__ = "test_specs"

    id = Column(String, primary_key=True)
    test_plan_id = Column(String, ForeignKey("test_plans.id"), nullable=False)

    # Test definition
    test_type = Column(SQLEnum(TestTypeEnum), nullable=False)
    test_name = Column(String, nullable=False)
    test_path = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Target
    target_file = Column(String, nullable=False)
    target_function = Column(String, nullable=True)

    # References
    contract_ref = Column(String, nullable=True)
    fr_ref = Column(String, nullable=True)
    regression_ref = Column(String, nullable=True)

    # Expected behavior
    expected_behavior = Column(Text, nullable=False)
    input_data = Column(JSON, nullable=True)
    expected_output = Column(JSON, nullable=True)

    # Generated content
    generated_content = Column(Text, nullable=True)
    syntax_valid = Column(Boolean, default=True)

    # Execution result
    execution_result = Column(SQLEnum(TestResultEnum), nullable=True)
    execution_duration_ms = Column(Integer, nullable=True)
    execution_error = Column(Text, nullable=True)

    # Relationship
    test_plan = relationship("TestPlanModel", back_populates="test_specs")

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TestSpecModel(name={self.test_name}, type={self.test_type})>"
