"""
APE - Autonomous Production Engineer
Unit Tests for Critic Engine

Tests for engine/critic_engine.py and critic passes.
"""

import pytest
import ast

from engine.critic_pass1 import SyntaxCritic
from engine.critic_pass2 import ContractCritic
from engine.critic_pass3 import CompletenessCritic
from engine.critic_pass4 import LogicCritic
from engine.critic_engine import CriticEngine


class TestSyntaxCritic:
    """Tests for Pass 1: Syntax validation."""
    
    def test_valid_python_syntax(self):
        """Test valid Python code passes syntax check."""
        critic = SyntaxCritic()
        
        valid_code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        passed, errors = critic.check("test.py", valid_code)
        
        assert passed is True
        assert len(errors) == 0
    
    def test_invalid_python_syntax(self):
        """Test invalid Python code fails syntax check."""
        critic = SyntaxCritic()
        
        invalid_code = '''
def broken_function(
    # Missing closing paren
    arg1: str,
    arg2: int
'''
        passed, errors = critic.check("test.py", invalid_code)
        
        assert passed is False
        assert len(errors) > 0
        assert errors[0]["type"] == "syntax"
    
    def test_syntax_error_location(self):
        """Test syntax error includes line number."""
        critic = SyntaxCritic()
        
        invalid_code = '''
def func1():
    pass

def func2(
    # Error on line 5
'''
        passed, errors = critic.check("test.py", invalid_code)
        
        assert passed is False
        assert errors[0]["line"] > 0


class TestContractCritic:
    """Tests for Pass 2: Contract compliance."""
    
    def test_matching_signature(self):
        """Test function matching contract signature passes."""
        critic = ContractCritic()
        
        contract = '''
def process_data(data: dict) -> dict:
    """Process data."""
    ...
'''
        implementation = '''
def process_data(data: dict) -> dict:
    """Process data."""
    return {"processed": True}
'''
        passed, violations = critic.check("test.py", implementation, [contract])
        
        assert passed is True
        assert len(violations) == 0
    
    def test_mismatched_signature(self):
        """Test function with mismatched signature fails."""
        critic = ContractCritic()
        
        contract = '''
def process_data(data: dict) -> dict:
    """Process data."""
    ...
'''
        implementation = '''
def process_data(data: str) -> str:
    """Process data."""
    return "processed"
'''
        passed, violations = critic.check("test.py", implementation, [contract])
        
        assert passed is False
        assert len(violations) > 0
    
    def test_missing_argument(self):
        """Test function with missing argument fails."""
        critic = ContractCritic()
        
        contract = '''
def create_user(name: str, email: str) -> dict:
    """Create user."""
    ...
'''
        implementation = '''
def create_user(name: str) -> dict:
    """Create user."""
    return {"name": name}
'''
        passed, violations = critic.check("test.py", implementation, [contract])
        
        assert passed is False


class TestCompletenessCritic:
    """Tests for Pass 3: Completeness check."""
    
    def test_complete_implementation(self, mock_llm_client):
        """Test complete implementation passes."""
        critic = CompletenessCritic(mock_llm_client)
        
        complete_code = '''
def process_user(user_id: int) -> dict:
    """Process user data."""
    if not user_id:
        raise ValueError("User ID required")
    
    user = {"id": user_id, "processed": True}
    return user
'''
        mock_llm_client.generate.return_value = '''
{
    "score": "complete",
    "reasoning": "All functions fully implemented",
    "issues": []
}
'''
        passed, score, reasoning = critic.check(complete_code, ["FR-001"])
        
        assert passed is True
        assert score == "complete"
    
    def test_stub_implementation(self, mock_llm_client):
        """Test stub implementation fails."""
        critic = CompletenessCritic(mock_llm_client)
        
        stub_code = '''
def process_user(user_id: int) -> dict:
    """Process user data."""
    pass  # TODO: implement
'''
        mock_llm_client.generate.return_value = '''
{
    "score": "stub",
    "reasoning": "Function contains only pass statement",
    "issues": [{"type": "pass_statement", "location": "process_user"}]
}
'''
        passed, score, reasoning = critic.check(stub_code, ["FR-001"])
        
        assert passed is False
        assert score == "stub"
    
    def test_is_trivial_body(self, mock_llm_client):
        """Test trivial body detection."""
        critic = CompletenessCritic(mock_llm_client)
        
        # Test pass statement
        tree = ast.parse("def func():\n    pass")
        func_node = tree.body[0]
        assert critic._is_trivial_body(func_node) is True
        
        # Test ellipsis
        tree = ast.parse("def func():\n    ...")
        func_node = tree.body[0]
        assert critic._is_trivial_body(func_node) is True
        
        # Test NotImplementedError
        tree = ast.parse("def func():\n    raise NotImplementedError")
        func_node = tree.body[0]
        assert critic._is_trivial_body(func_node) is True


class TestLogicCritic:
    """Tests for Pass 4: Logic correctness."""
    
    def test_correct_implementation(self, mock_llm_client):
        """Test logically correct implementation passes."""
        critic = LogicCritic(mock_llm_client)
        
        correct_code = '''
def calculate_discount(price: float, discount: float) -> float:
    """Calculate discounted price."""
    if discount < 0 or discount > 1:
        raise ValueError("Discount must be between 0 and 1")
    return price * (1 - discount)
'''
        mock_llm_client.generate.return_value = '''
{
    "score": "correct",
    "reasoning": "Implementation correctly handles all cases",
    "errors": []
}
'''
        passed, score, reasoning, errors = critic.check(
            correct_code,
            ["FR-001: Calculate discount"],
            ["def calculate_discount(price: float, discount: float) -> float"]
        )
        
        assert passed is True
        assert score == "correct"
    
    def test_incorrect_implementation(self, mock_llm_client):
        """Test logically incorrect implementation fails."""
        critic = LogicCritic(mock_llm_client)
        
        incorrect_code = '''
def calculate_discount(price: float, discount: float) -> float:
    """Calculate discounted price."""
    # Bug: multiplying instead of subtracting
    return price * discount
'''
        mock_llm_client.generate.return_value = '''
{
    "score": "incorrect",
    "reasoning": "Formula is wrong - should be price * (1 - discount)",
    "errors": ["Incorrect discount formula"]
}
'''
        passed, score, reasoning, errors = critic.check(
            incorrect_code,
            ["FR-001: Calculate discount"],
            ["def calculate_discount(price: float, discount: float) -> float"]
        )
        
        assert passed is False
        assert score == "incorrect"


class TestCriticEngine:
    """Tests for full CriticEngine."""
    
    def test_all_passes_pass(self, mock_llm_client):
        """Test all 4 passes passing."""
        engine = CriticEngine(mock_llm_client)
        
        valid_code = '''
def process_data(data: dict) -> dict:
    """Process data."""
    if not data:
        return {}
    return {"processed": True, **data}
'''
        mock_llm_client.generate.side_effect = [
            '{"score": "complete", "reasoning": "Complete", "issues": []}',
            '{"score": "correct", "reasoning": "Correct", "errors": []}',
        ]
        
        result = engine.critique_file(
            file_path="test.py",
            content=valid_code,
            level=0,
            contracts=["def process_data(data: dict) -> dict: ..."],
            fr_refs=["FR-001"],
        )
        
        assert result.all_passes_passed() is True
        assert result.overall_result.value == "pass"
    
    def test_syntax_fail(self, mock_llm_client):
        """Test syntax failure stops further passes."""
        engine = CriticEngine(mock_llm_client)
        
        invalid_code = '''
def broken(
    # Syntax error
'''
        result = engine.critique_file(
            file_path="test.py",
            content=invalid_code,
            level=0,
            contracts=[],
            fr_refs=[],
        )
        
        assert result.pass1_result.value == "fail"
        assert result.pass2_result.value == "skipped"  # Not run due to syntax fail
    
    def test_get_failing_files(self, mock_llm_client):
        """Test getting list of failing files."""
        engine = CriticEngine(mock_llm_client)
        
        # Mock level result with some failures
        from contracts.models.generation import LevelCriticResult, CriticResult, CriticPassResult
        
        level_result = LevelCriticResult(
            run_id="test-run",
            level=0,
            total_files=2,
        )
        
        # Passing file
        pass_result = CriticResult(
            job_id="job1",
            file_path="passing.py",
            level=0,
            pass1_result=CriticPassResult.PASS,
            pass2_result=CriticPassResult.PASS,
            pass3_result=CriticPassResult.PASS,
            pass4_result=CriticPassResult.PASS,
            overall_result=CriticPassResult.PASS,
        )
        
        # Failing file
        fail_result = CriticResult(
            job_id="job2",
            file_path="failing.py",
            level=0,
            pass1_result=CriticPassResult.FAIL,
            overall_result=CriticPassResult.FAIL,
        )
        
        level_result.file_results = [pass_result, fail_result]
        level_result.passed_files = 1
        level_result.failed_files = 1
        
        failing = engine.get_failing_files(level_result)
        
        assert len(failing) == 1
        assert "failing.py" in failing
