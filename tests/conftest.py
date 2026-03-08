"""
APE - Autonomous Production Engineer
Pytest Configuration and Fixtures

Shared fixtures for all tests.
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"


@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "database_url": "postgresql://test:test@localhost:5432/test_db",
        "secret_key": "test-secret-key-for-testing-only-min-32-chars",
        "test_token": "test-access-token",
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock = MagicMock()
    mock.generate.return_value = '{"test": "response"}'
    mock.generate_json.return_value = {"test": "response"}
    mock.parse_json.return_value = {"test": "response"}
    mock.generate_code.return_value = "def test_function():\n    pass"
    mock.judge_code.return_value = {
        "score": "pass",
        "reasoning": "Test passed",
        "issues": []
    }
    mock.count_tokens.return_value = 100
    return mock


@pytest.fixture
def mock_github_connector():
    """Mock GitHub connector for testing."""
    mock = MagicMock()
    mock.test_connection.return_value = (True, "Connected")
    mock.get_repository.return_value = MagicMock()
    mock.clone_repository.return_value = (True, None)
    mock.create_pull_request.return_value = MagicMock(
        id="gh-123",
        pr_number=42,
        pr_url="https://github.com/test/repo/pull/42",
    )
    return mock


@pytest.fixture
def mock_codebase_graph():
    """Mock CodebaseGraph for testing."""
    from contracts.models.graph import DependencyGraph, Node, Edge
    
    graph = DependencyGraph(
        id="test-graph",
        repo_id="test/repo",
        nodes=[
            Node(
                id="src/main.py",
                module="src.main",
                type="untouched",
                exports=["def main", "def run"],
                imports=["fastapi"],
            ),
            Node(
                id="src/api/users.py",
                module="src.api.users",
                type="untouched",
                exports=["def get_user", "def create_user"],
                imports=["src.main"],
            ),
        ],
        edges=[],
        cycle_free=True,
        generated_at=datetime.utcnow(),
    )
    
    return graph


@pytest.fixture
def mock_requirement_spec():
    """Mock RequirementSpec for testing."""
    from contracts.models.requirement import (
        RequirementSpec,
        FunctionalRequirement,
        NonFunctionalRequirement,
        Criterion,
        Priority,
        RequirementStatus,
    )
    
    return RequirementSpec(
        id="test-req-001",
        repo_id="test/repo",
        raw_text="Add rate limiting to /api/users endpoint",
        source="manual",
        functional=[
            FunctionalRequirement(
                id="FR-001",
                title="Implement rate limiting",
                description="Limit requests to 100 per minute per IP",
                verb="limit",
                noun="requests",
                acceptance_criteria=["Max 100 requests per minute", "Return 429 when exceeded"],
                priority=Priority.HIGH,
            ),
        ],
        non_functional=[
            NonFunctionalRequirement(
                id="NFR-001",
                category="performance",
                description="Handle 1000 concurrent requests",
                metric="concurrent_requests",
                threshold="1000",
            ),
        ],
        affected_modules=["src/api/users.py"],
        new_modules=["src/middleware/rate_limiter.py"],
        acceptance_criteria=[
            Criterion(
                id="AC-001",
                description="Rate limit is enforced",
                testable=True,
                automated=True,
            ),
        ],
        ambiguities=[],
        priority=Priority.HIGH,
        status=RequirementStatus.APPROVED,
        requirement_hash="test-hash-123",
    )


@pytest.fixture
def mock_architecture_plan():
    """Mock ArchitecturePlan for testing."""
    from contracts.models.architecture import (
        ArchitecturePlan,
        ModuleChange,
        ModuleSpec,
        ChangeType,
    )
    
    return ArchitecturePlan(
        id="test-arch-001",
        requirement_spec_id="test-req-001",
        repo_id="test/repo",
        modified_modules=[
            ModuleChange(
                path="src/api/users.py",
                change_type=ChangeType.MODIFY,
                description="Add rate limiting middleware",
                affected_functions=["get_user", "create_user"],
                new_functions=["check_rate_limit"],
            ),
        ],
        new_modules=[
            ModuleSpec(
                name="rate_limiter",
                path="src/middleware/rate_limiter.py",
                description="Rate limiting middleware",
                exports=["def check_rate_limit", "class RateLimiter"],
                dependencies=["redis"],
            ),
        ],
        status="approved",
    )


@pytest.fixture
def mock_build_plan():
    """Mock BuildPlan for testing."""
    from contracts.models.graph import BuildPlan, Level
    
    return BuildPlan(
        id="test-build-001",
        requirement_spec_id="test-req-001",
        architecture_plan_id="test-arch-001",
        dependency_graph_id="test-graph",
        levels=[
            Level(level=0, files=["src/middleware/rate_limiter.py"], parallel=True),
            Level(level=1, files=["src/api/users.py"], parallel=True),
        ],
        total_files=2,
        total_new_files=1,
        total_modified_files=1,
        critical_path=["src/middleware/rate_limiter.py", "src/api/users.py"],
    )


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def test_user():
    """Create a test user model."""
    from server.database.models.tenant import UserModel, TenantModel
    
    tenant = TenantModel(
        id="test-tenant",
        name="Test Tenant",
        admin_email="test@example.com",
        status="active",
    )
    
    user = UserModel(
        id="test-user",
        tenant_id=tenant.id,
        email="test@example.com",
        name="Test User",
        role="admin",
        password_hash="hashed-password",
    )
    
    return user


@pytest.fixture
def mock_fastapi_app():
    """Create a test FastAPI app."""
    from fastapi.testclient import TestClient
    from server.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    return app, client


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}")
def get_user(user_id: int) -> User:
    """Get user by ID."""
    return User(id=user_id, name="Test", email="test@example.com")

@app.post("/users")
def create_user(user: User) -> User:
    """Create a new user."""
    return user
'''


@pytest.fixture
def sample_invalid_code():
    """Sample invalid Python code for testing."""
    return '''
def invalid_function(
    # Missing closing parenthesis and body
    arg1: str,
    arg2: int
'''


@pytest.fixture
def sample_contract():
    """Sample contract for testing."""
    return '''
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

def get_user(user_id: int) -> UserResponse:
    """Get user by ID."""
    ...

def create_user(user: UserCreate) -> UserResponse:
    """Create a new user."""
    ...
'''
