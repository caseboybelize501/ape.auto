"""
APE - Autonomous Production Engineer
Contract: Test Models

Immutable Pydantic schemas for test generation,
test execution, and coverage tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TestType(str, Enum):
    CONTRACT = "contract"
    ACCEPTANCE = "acceptance"
    REGRESSION = "regression"
    UNIT = "unit"
    INTEGRATION = "integration"
    PROPERTY = "property"


class TestStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"
    XFAIL = "xfail"  # Expected failure


class TestSpec(BaseModel):
    """
    Specification for a single test to generate.
    """
    id: str = Field(..., description="Unique test specification ID")
    test_type: TestType = Field(..., description="Type of test")
    
    # Target
    target_file: str = Field(..., description="File being tested")
    target_function: Optional[str] = Field(None, description="Specific function being tested")
    
    # Test definition
    test_name: str = Field(..., description="Test function name")
    test_path: str = Field(..., description="Test file path")
    description: str = Field(..., description="What this test verifies")
    
    # Generation context
    contract_ref: Optional[str] = Field(None, description="Contract file if contract test")
    fr_ref: Optional[str] = Field(None, description="FR ID if acceptance test")
    regression_ref: Optional[str] = Field(None, description="Original behavior if regression test")
    
    # Expected behavior
    expected_behavior: str = Field(..., description="Expected behavior in plain language")
    input_data: Optional[dict] = Field(None, description="Test input data")
    expected_output: Optional[dict] = Field(None, description="Expected output")
    
    # Fixtures and mocks
    fixtures: list[str] = Field(default_factory=list)
    mocks: list[dict] = Field(default_factory=list)
    
    class Config:
        frozen = True


class GeneratedTest(BaseModel):
    """
    A generated test file/content.
    """
    spec_id: str = Field(..., description="Reference to TestSpec")
    test_type: TestType = Field(..., description="Type of test")
    
    # Generated content
    file_path: str = Field(..., description="Test file path")
    content: str = Field(..., description="Complete test file content")
    language: str = Field("python", description="Test file language")
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    
    # Validation
    syntax_valid: bool = True
    imports_valid: bool = True
    
    class Config:
        frozen = False


class TestExecutionResult(BaseModel):
    """
    Result of executing a single test.
    """
    test_id: str = Field(..., description="Test specification ID")
    test_name: str = Field(..., description="Test function name")
    test_path: str = Field(..., description="Test file path")
    test_type: TestType = Field(..., description="Type of test")
    
    # Execution result
    result: TestResult = Field(..., description="Test result")
    duration_ms: Optional[int] = None
    
    # Failure details
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    assertion_error: Optional[str] = None
    
    # Output
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    
    # Coverage
    covered_lines: list[int] = Field(default_factory=list)
    covered_branches: list[int] = Field(default_factory=list)
    
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class TestSuiteResult(BaseModel):
    """
    Result of executing a test suite.
    """
    suite_id: str = Field(..., description="Unique suite ID")
    suite_name: str = Field(..., description="Suite name")
    suite_type: TestType = Field(..., description="Type of tests in suite")
    
    # Execution results
    total_tests: int = Field(..., description="Total tests in suite")
    passed: int = Field(0, description="Passed tests")
    failed: int = Field(0, description="Failed tests")
    skipped: int = Field(0, description="Skipped tests")
    errors: int = Field(0, description="Tests with errors")
    
    # Individual results
    test_results: list[TestExecutionResult] = Field(default_factory=list)
    
    # Coverage
    total_lines: int = Field(0, description="Total lines in tested code")
    covered_lines: int = Field(0, description="Covered lines")
    line_coverage_percent: Optional[float] = None
    branch_coverage_percent: Optional[float] = None
    
    # Timing
    total_duration_ms: Optional[int] = None
    average_duration_ms: Optional[float] = None
    
    # Status
    success: bool = True  # True if no failures or errors
    regression_detected: bool = False
    
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def get_failed_tests(self) -> list[TestExecutionResult]:
        """Return list of failed tests."""
        return [r for r in self.test_results if r.result in (TestResult.FAIL, TestResult.ERROR)]
    
    class Config:
        frozen = False


class CoverageReport(BaseModel):
    """
    Code coverage report.
    """
    run_id: str = Field(..., description="Associated run ID")
    repo_id: str = Field(..., description="Repository ID")
    
    # Overall coverage
    total_files: int = Field(..., description="Total files analyzed")
    total_lines: int = Field(..., description="Total lines of code")
    total_covered: int = Field(..., description="Total covered lines")
    line_coverage_percent: float = Field(..., description="Overall line coverage")
    
    # Branch coverage
    total_branches: int = Field(0, description="Total branches")
    covered_branches: int = Field(0, description="Covered branches")
    branch_coverage_percent: Optional[float] = None
    
    # Per-file coverage
    file_coverage: list[dict] = Field(default_factory=list)
    # [{path, lines, covered, percent, missing_lines}]
    
    # Uncovered files
    uncovered_files: list[str] = Field(default_factory=list)
    
    # Critical files coverage (files with 0% coverage)
    critical_uncovered: list[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False


class TestPlan(BaseModel):
    """
    Complete test plan for a generation run.
    """
    id: str = Field(..., description="Unique test plan ID")
    run_id: str = Field(..., description="Associated generation run ID")
    requirement_spec_id: str = Field(..., description="Reference to RequirementSpec")
    
    # Test levels (mirror code levels)
    test_levels: list["TestLevel"] = Field(default_factory=list)
    
    # Test specifications
    contract_tests: list[TestSpec] = Field(default_factory=list)
    acceptance_tests: list[TestSpec] = Field(default_factory=list)
    regression_tests: list[TestSpec] = Field(default_factory=list)
    
    # Execution order
    execution_order: list[str] = Field(default_factory=list)
    # Order: regression guards -> contract tests -> acceptance tests
    
    # Status
    status: str = Field("pending", enum=["pending", "generating", "generated", "executing", "completed", "failed"])
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class TestLevel(BaseModel):
    """
    Test generation level - mirrors code levels.
    """
    level: int = Field(..., description="Associated code level")
    code_files: list[str] = Field(..., description="Code files being tested")
    
    # Generated tests
    test_specs: list[TestSpec] = Field(default_factory=list)
    generated_tests: list[GeneratedTest] = Field(default_factory=list)
    
    # Execution results
    execution_results: Optional[TestSuiteResult] = None
    
    # Status
    generation_status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed"])
    execution_status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed"])
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generation_completed_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class TestCriticResult(BaseModel):
    """
    Result of running 4-pass critic on tests.
    """
    test_level: int = Field(..., description="Test level being critiqued")
    run_id: str = Field(..., description="Associated run ID")
    
    # Pass 1: Syntax (pytest --collect-only)
    pass1_result: str = Field(..., enum=["pass", "fail"])
    pass1_errors: list[str] = Field(default_factory=list)
    
    # Pass 2: Contract coverage
    pass2_result: str = Field(..., enum=["pass", "fail"])
    pass2_missing_coverage: list[str] = Field(default_factory=list)
    # Functions without tests
    
    # Pass 3: Acceptance coverage
    pass3_result: str = Field(..., enum=["pass", "fail"])
    pass3_missing_fr_coverage: list[str] = Field(default_factory=list)
    # FRs without acceptance tests
    
    # Pass 4: Determinism (run twice, same results)
    pass4_result: str = Field(..., enum=["pass", "fail"])
    pass4_nondeterministic_tests: list[str] = Field(default_factory=list)
    
    # Overall
    overall_result: str = Field(..., enum=["pass", "fail"])
    
    run_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False
