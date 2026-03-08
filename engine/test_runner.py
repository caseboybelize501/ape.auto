"""
APE - Autonomous Production Engineer
Test Runner

Executes tests in topological order:
- Regression guards first
- Contract tests second
- Acceptance tests third
- Fail fast on first failure
"""

import subprocess
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from contracts.models.test import (
    TestPlan,
    TestLevel,
    TestSuiteResult,
    TestExecutionResult,
    TestResult,
    TestType,
)


class TestRunner:
    """
    Executes tests with topological ordering.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize test runner.
        
        Args:
            repo_path: Path to repository
        """
        self.repo_path = Path(repo_path)
    
    def run_all(self, test_plan: TestPlan) -> list[TestSuiteResult]:
        """
        Run all tests in topological order.
        
        Args:
            test_plan: Test plan
        
        Returns:
            List of test suite results per level
        """
        results = []
        
        # Sort levels by level number
        sorted_levels = sorted(test_plan.test_levels, key=lambda l: l.level)
        
        for test_level in sorted_levels:
            # Run regression tests first
            regression_result = self._run_suite(
                test_level, TestType.REGRESSION
            )
            if regression_result and not regression_result.success:
                # Fail fast - regression failure
                results.append(regression_result)
                break
            
            # Run contract tests
            contract_result = self._run_suite(
                test_level, TestType.CONTRACT
            )
            if contract_result and not contract_result.success:
                results.append(contract_result)
                break
            
            # Run acceptance tests
            acceptance_result = self._run_suite(
                test_level, TestType.ACCEPTANCE
            )
            
            results.append(acceptance_result or TestSuiteResult(
                suite_id=f"suite-level{test_level.level}",
                suite_name=f"Level {test_level.level} Tests",
                suite_type=TestType.ACCEPTANCE,
                total_tests=0,
                success=True,
            ))
        
        return results
    
    def _run_suite(
        self,
        test_level: TestLevel,
        test_type: TestType
    ) -> Optional[TestSuiteResult]:
        """
        Run test suite for a specific type.
        
        Args:
            test_level: Test level
            test_type: Type of tests to run
        
        Returns:
            Test suite result
        """
        # Get tests of this type
        tests = [
            t for t in test_level.test_specs
            if t.test_type == test_type
        ]
        
        if not tests:
            return None
        
        # Generate test files if needed
        test_files = [t.test_path for t in tests]
        
        # Run pytest
        result = self._run_pytest(test_files, test_type.value)
        
        return result
    
    def _run_pytest(
        self,
        test_files: list[str],
        suite_type: str
    ) -> TestSuiteResult:
        """
        Run pytest on test files.
        
        Args:
            test_files: Test file paths
            suite_type: Suite type for naming
        
        Returns:
            Test suite result
        """
        suite_result = TestSuiteResult(
            suite_id=f"suite-{suite_type}-{datetime.utcnow().strftime('%H%M%S')}",
            suite_name=f"{suite_type.title()} Tests",
            suite_type=TestType(suite_type) if suite_type in [t.value for t in TestType] else TestType.UNIT,
            total_tests=len(test_files),
        )
        
        try:
            # Build pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=/dev/null",  # We'll parse stdout
            ] + test_files
            
            # Run pytest
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse output
            suite_result = self._parse_pytest_output(
                result.stdout, result.stderr, result.returncode, suite_result
            )
            
        except subprocess.TimeoutExpired:
            suite_result.success = False
            suite_result.test_results.append(TestExecutionResult(
                test_id="timeout",
                test_name="test_suite",
                test_path="*",
                test_type=suite_result.suite_type,
                result=TestResult.ERROR,
                error_message="Test suite timed out after 5 minutes",
            ))
        
        except Exception as e:
            suite_result.success = False
            suite_result.test_results.append(TestExecutionResult(
                test_id="error",
                test_name="test_suite",
                test_path="*",
                test_type=suite_result.suite_type,
                result=TestResult.ERROR,
                error_message=str(e),
            ))
        
        return suite_result
    
    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
        suite_result: TestSuiteResult
    ) -> TestSuiteResult:
        """
        Parse pytest output.
        
        Args:
            stdout: pytest stdout
            stderr: pytest stderr
            returncode: pytest return code
            suite_result: Suite result to populate
        
        Returns:
            Populated suite result
        """
        # Parse summary line
        # Example: "5 passed, 2 failed, 1 error in 1.23s"
        import re
        
        summary_match = re.search(
            r"(\d+) passed,? (\d+) failed,? (\d+) error",
            stdout
        )
        
        if summary_match:
            suite_result.passed = int(summary_match.group(1))
            suite_result.failed = int(summary_match.group(2))
            suite_result.errors = int(summary_match.group(3))
        else:
            # Fallback
            if returncode == 0:
                suite_result.passed = suite_result.total_tests
            else:
                suite_result.failed = suite_result.total_tests
        
        suite_result.success = returncode == 0
        suite_result.regression_detected = not suite_result.success
        
        # Parse individual test results
        for line in stdout.split("\n"):
            if line.startswith("test_"):
                # Parse: "test_file.py::test_name PASSED" or "FAILED"
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0].split("::")[-1]
                    status = parts[-1]
                    
                    result = TestResult.PASS if status == "PASSED" else TestResult.FAIL
                    
                    suite_result.test_results.append(TestExecutionResult(
                        test_id=test_name,
                        test_name=test_name,
                        test_path=parts[0].split("::")[0],
                        test_type=suite_result.suite_type,
                        result=result,
                    ))
        
        return suite_result
    
    def run_single_test(
        self,
        test_path: str,
        test_name: str
    ) -> TestExecutionResult:
        """
        Run a single test.
        
        Args:
            test_path: Test file path
            test_name: Test function name
        
        Returns:
            Test execution result
        """
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "-v",
                f"{test_path}::{test_name}",
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return TestExecutionResult(
                test_id=test_name,
                test_name=test_name,
                test_path=test_path,
                test_type=TestType.UNIT,
                result=TestResult.PASS if result.returncode == 0 else TestResult.FAIL,
                error_message=result.stderr if result.returncode != 0 else None,
            )
            
        except Exception as e:
            return TestExecutionResult(
                test_id=test_name,
                test_name=test_name,
                test_path=test_path,
                test_type=TestType.UNIT,
                result=TestResult.ERROR,
                error_message=str(e),
            )
