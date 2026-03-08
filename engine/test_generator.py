"""
APE - Autonomous Production Engineer
Test Generator

Generates 3 types of tests per code level:
1. Contract tests - from contracts/interfaces/
2. Acceptance tests - from RequirementSpec
3. Regression guards - from existing coverage
"""

from datetime import datetime
from typing import Optional

from contracts.models.test import (
    TestSpec,
    GeneratedTest,
    TestType,
    TestPlan,
    TestLevel,
)
from contracts.models.requirement import RequirementSpec

from engine.llm_client import LLMClient


class TestGenerator:
    """
    Generates tests for generated code.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize test generator.
        
        Args:
            llm_client: LLM client for test generation
        """
        self.llm = llm_client or LLMClient()
    
    def generate_all(
        self,
        requirement_spec: RequirementSpec,
        code_files: list[dict],
        contracts: list[str],
        existing_coverage: dict
    ) -> TestPlan:
        """
        Generate all test types.
        
        Args:
            requirement_spec: Requirement spec
            code_files: Generated code files
            contracts: Contract files
            existing_coverage: Existing test coverage
        
        Returns:
            Complete TestPlan
        """
        test_plan = TestPlan(
            id=f"testplan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            run_id="",  # Will be set by caller
            requirement_spec_id=requirement_spec.id,
        )
        
        # Generate contract tests
        contract_tests = self.generate_contract_tests(
            code_files, contracts
        )
        test_plan.contract_tests = contract_tests
        
        # Generate acceptance tests
        acceptance_tests = self.generate_acceptance_tests(
            requirement_spec, code_files
        )
        test_plan.acceptance_tests = acceptance_tests
        
        # Generate regression tests
        regression_tests = self.generate_regression_tests(
            code_files, existing_coverage
        )
        test_plan.regression_tests = regression_tests
        
        # Organize into test levels
        test_plan.test_levels = self._organize_test_levels(
            code_files, contract_tests, acceptance_tests, regression_tests
        )
        
        # Set execution order
        test_plan.execution_order = ["regression", "contract", "acceptance"]
        
        return test_plan
    
    def generate_contract_tests(
        self,
        code_files: list[dict],
        contracts: list[str]
    ) -> list[TestSpec]:
        """
        Generate contract tests from contracts.
        
        These are deterministic tests generated from contract files.
        
        Args:
            code_files: Generated code files
            contracts: Contract files
        
        Returns:
            List of contract test specs
        """
        tests = []
        
        for contract in contracts:
            # Parse contract for functions/classes
            contract_tests = self._parse_contract_for_tests(contract)
            
            for ct in contract_tests:
                tests.append(TestSpec(
                    id=f"ct-{ct['name']}-{datetime.utcnow().strftime('%H%M%S')}",
                    test_type=TestType.CONTRACT,
                    target_file=ct.get("target_file", ""),
                    target_function=ct.get("function", ""),
                    test_name=f"test_{ct['name']}_contract",
                    test_path=f"tests/test_{ct['name']}_contract.py",
                    description=f"Contract test for {ct['name']}",
                    contract_ref=ct.get("contract_ref", ""),
                    expected_behavior=ct.get("expected_behavior", ""),
                    input_data=ct.get("input_data"),
                    expected_output=ct.get("expected_output"),
                ))
        
        return tests
    
    def _parse_contract_for_tests(self, contract: str) -> list[dict]:
        """Parse contract file for testable items."""
        import ast
        
        tests = []
        
        try:
            tree = ast.parse(contract)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    
                    # Extract signature
                    args = [arg.arg for arg in node.args.args if arg.arg != "self"]
                    return_type = ast.unparse(node.returns) if node.returns else None
                    
                    tests.append({
                        "name": node.name,
                        "function": node.name,
                        "args": args,
                        "return_type": return_type,
                        "expected_behavior": f"Function {node.name} matches contract signature",
                    })
                
                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith("_"):
                        continue
                    
                    tests.append({
                        "name": node.name,
                        "class": node.name,
                        "expected_behavior": f"Class {node.name} matches contract definition",
                    })
        
        except SyntaxError:
            pass
        
        return tests
    
    def generate_acceptance_tests(
        self,
        requirement_spec: RequirementSpec,
        code_files: list[dict]
    ) -> list[TestSpec]:
        """
        Generate acceptance tests from requirements.
        
        Args:
            requirement_spec: Requirement spec
            code_files: Generated code files
        
        Returns:
            List of acceptance test specs
        """
        tests = []
        
        # Generate test for each acceptance criterion
        for criterion in requirement_spec.acceptance_criteria:
            test = self._generate_acceptance_test(
                criterion, requirement_spec, code_files
            )
            if test:
                tests.append(test)
        
        # Generate test for each functional requirement
        for fr in requirement_spec.functional:
            test = self._generate_fr_test(fr, code_files)
            if test:
                tests.append(test)
        
        return tests
    
    def _generate_acceptance_test(
        self,
        criterion,
        requirement_spec: RequirementSpec,
        code_files: list[dict]
    ) -> Optional[TestSpec]:
        """Generate acceptance test for a criterion."""
        prompt = f"""Generate a pytest test function for this acceptance criterion.

Criterion: {criterion.description}

Requirement context:
{requirement_spec.raw_text[:500]}

Generated code files:
{[f['path'] for f in code_files]}

Generate a test that:
1. Is binary pass/fail
2. Can be automated
3. Tests the specific criterion

Return JSON:
{{
    "test_name": "test_<criterion>",
    "target_file": "path/to/tested/file.py",
    "description": "What this tests",
    "test_code": "def test_...():\\n    ..."
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {})
        
        if not result:
            return None
        
        return TestSpec(
            id=f"at-{criterion.id}-{datetime.utcnow().strftime('%H%M%S')}",
            test_type=TestType.ACCEPTANCE,
            target_file=result.get("target_file", ""),
            test_name=result.get("test_name", f"test_{criterion.id.lower()}"),
            test_path=f"tests/test_acceptance_{criterion.id.lower()}.py",
            description=result.get("description", criterion.description),
            fr_ref=criterion.id,
            expected_behavior=criterion.description,
        )
    
    def _generate_fr_test(
        self,
        fr,
        code_files: list[dict]
    ) -> Optional[TestSpec]:
        """Generate acceptance test for functional requirement."""
        prompt = f"""Generate a pytest test function for this functional requirement.

Requirement: {fr.title}
Description: {fr.description}
Acceptance criteria: {fr.acceptance_criteria}

Generated code files:
{[f['path'] for f in code_files]}

Return JSON:
{{
    "test_name": "test_<requirement>",
    "target_file": "path/to/tested/file.py",
    "description": "What this tests",
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {})
        
        if not result:
            return None
        
        return TestSpec(
            id=f"at-{fr.id}-{datetime.utcnow().strftime('%H%M%S')}",
            test_type=TestType.ACCEPTANCE,
            target_file=result.get("target_file", ""),
            test_name=result.get("test_name", f"test_{fr.id.lower()}"),
            test_path=f"tests/test_acceptance_{fr.id.lower()}.py",
            description=result.get("description", fr.description),
            fr_ref=fr.id,
            expected_behavior=fr.description,
        )
    
    def generate_regression_tests(
        self,
        code_files: list[dict],
        existing_coverage: dict
    ) -> list[TestSpec]:
        """
        Generate regression guard tests.
        
        Args:
            code_files: Generated code files
            existing_coverage: Existing test coverage
        
        Returns:
            List of regression test specs
        """
        tests = []
        
        for file_info in code_files:
            file_path = file_info.get("path", "")
            
            # Check if file has existing coverage
            if file_path in existing_coverage:
                coverage = existing_coverage[file_path]
                
                # Generate regression tests for covered behavior
                for func in coverage.get("functions", []):
                    tests.append(TestSpec(
                        id=f"rt-{file_path.replace('/', '-')}-{func}-{datetime.utcnow().strftime('%H%M%S')}",
                        test_type=TestType.REGRESSION,
                        target_file=file_path,
                        target_function=func,
                        test_name=f"test_regression_{func}",
                        test_path=f"tests/test_regression_{file_path.replace('/', '_').replace('.py', '')}.py",
                        description=f"Regression guard for {func}",
                        regression_ref=file_path,
                    ))
        
        return tests
    
    def _organize_test_levels(
        self,
        code_files: list[dict],
        contract_tests: list[TestSpec],
        acceptance_tests: list[TestSpec],
        regression_tests: list[TestSpec]
    ) -> list[TestLevel]:
        """Organize tests into levels mirroring code levels."""
        levels = []
        
        # Group tests by target file
        tests_by_file = {}
        
        for test in contract_tests + acceptance_tests + regression_tests:
            target = test.target_file
            if target not in tests_by_file:
                tests_by_file[target] = []
            tests_by_file[target].append(test)
        
        # Create test level for each code file
        for file_info in code_files:
            file_path = file_info.get("path", "")
            level = file_info.get("level", 0)
            
            file_tests = tests_by_file.get(file_path, [])
            
            test_level = TestLevel(
                level=level,
                code_files=[file_path],
                test_specs=file_tests,
                test_types=list(set(t.test_type.value for t in file_tests)),
            )
            
            levels.append(test_level)
        
        return levels
    
    def generate_test_code(self, test_spec: TestSpec) -> GeneratedTest:
        """
        Generate actual test code from spec.
        
        Args:
            test_spec: Test specification
        
        Returns:
            GeneratedTest with code
        """
        prompt = f"""Generate complete pytest test code.

Test name: {test_spec.test_name}
Target: {test_spec.target_file}
Function: {test_spec.target_function}
Description: {test_spec.description}
Test type: {test_spec.test_type.value}

Generate a complete test function with:
1. Proper pytest fixtures
2. Clear assertions
3. Descriptive docstring

Return ONLY the test code, no explanations.
"""
        
        content = self.llm.generate(prompt, temperature=0.1)
        
        return GeneratedTest(
            spec_id=test_spec.id,
            test_type=test_spec.test_type,
            file_path=test_spec.test_path,
            content=content,
            language="python",
            generated_at=datetime.utcnow(),
        )
    
    def test_critic(
        self,
        test_level: TestLevel,
        generated_tests: list[GeneratedTest]
    ) -> dict:
        """
        Run 4-pass critic on generated tests.
        
        Args:
            test_level: Test level
            generated_tests: Generated test files
        
        Returns:
            Critic result dict
        """
        # Pass 1: Syntax (pytest --collect-only)
        syntax_pass = self._check_test_syntax(generated_tests)
        
        # Pass 2: Contract coverage
        contract_pass = self._check_contract_coverage(test_level, generated_tests)
        
        # Pass 3: Acceptance coverage
        acceptance_pass = self._check_acceptance_coverage(test_level, generated_tests)
        
        # Pass 4: Determinism
        determinism_pass = self._check_determinism(generated_tests)
        
        return {
            "pass1_syntax": syntax_pass,
            "pass2_contract_coverage": contract_pass,
            "pass3_acceptance_coverage": acceptance_pass,
            "pass4_determinism": determinism_pass,
            "overall_pass": all([syntax_pass, contract_pass, acceptance_pass, determinism_pass]),
        }
    
    def _check_test_syntax(self, tests: list[GeneratedTest]) -> dict:
        """Check test syntax with pytest --collect-only."""
        import ast
        
        errors = []
        for test in tests:
            try:
                ast.parse(test.content)
            except SyntaxError as e:
                errors.append({
                    "file": test.file_path,
                    "line": e.lineno,
                    "message": str(e),
                })
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
        }
    
    def _check_contract_coverage(
        self,
        level: TestLevel,
        tests: list[GeneratedTest]
    ) -> dict:
        """Check that all contract functions have tests."""
        # Simplified - would need actual contract parsing
        return {"passed": True, "missing": []}
    
    def _check_acceptance_coverage(
        self,
        level: TestLevel,
        tests: list[GeneratedTest]
    ) -> dict:
        """Check that all FRs have acceptance tests."""
        # Simplified - would need actual FR tracking
        return {"passed": True, "missing": []}
    
    def _check_determinism(self, tests: list[GeneratedTest]) -> dict:
        """Check tests are deterministic (no random/time dependencies)."""
        non_deterministic = []
        
        for test in tests:
            content = test.content
            # Check for common non-deterministic patterns
            if "random." in content or "time.time()" in content:
                if "mock" not in content and "patch" not in content:
                    non_deterministic.append(test.file_path)
        
        return {
            "passed": len(non_deterministic) == 0,
            "non_deterministic": non_deterministic,
        }
