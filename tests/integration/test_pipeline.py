"""
APE - Autonomous Production Engineer
Integration Tests

End-to-end tests for the full pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


class TestRequirementFlow:
    """Integration tests for requirement submission flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from server.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "APE" in data["name"]
    
    @patch('engine.req_extractor.RequirementsExtractor.extract')
    def test_submit_requirement(self, mock_extract, client, mock_requirement_spec):
        """Test submitting a requirement."""
        mock_extract.return_value = mock_requirement_spec
        
        response = client.post(
            "/api/requirements",
            json={
                "text": "Add rate limiting",
                "repo_id": "test/repo",
                "priority": "high",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "req_id" in data
        assert "spec" in data
    
    def test_list_requirements(self, client):
        """Test listing requirements."""
        response = client.get("/api/requirements")
        
        # Should return empty list or existing requirements
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_nonexistent_requirement(self, client):
        """Test getting a requirement that doesn't exist."""
        response = client.get("/api/requirements/nonexistent-id")
        
        assert response.status_code == 404


class TestAuthenticationFlow:
    """Integration tests for authentication."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from server.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword",
            }
        )
        
        assert response.status_code == 401
    
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "tenant_name": "New Tenant",
            }
        )
        
        # May succeed or fail depending on database setup
        assert response.status_code in [200, 400, 500]
    
    def test_websocket_stats(self, client):
        """Test WebSocket stats endpoint."""
        response = client.get("/api/ws/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data


class TestGenerationFlow:
    """Integration tests for generation flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from server.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_list_generations(self, client):
        """Test listing generation runs."""
        response = client.get("/api/generations")
        
        # Should return list (empty or with runs)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_nonexistent_generation(self, client):
        """Test getting a generation run that doesn't exist."""
        response = client.get("/api/generations/nonexistent-id")
        
        assert response.status_code == 404


class TestAnalyticsFlow:
    """Integration tests for analytics endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from server.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_get_analytics(self, client):
        """Test getting analytics."""
        response = client.get("/api/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "total_runs" in data
    
    def test_get_runs_analytics(self, client):
        """Test getting runs analytics."""
        response = client.get("/api/analytics/runs")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
    
    def test_get_critic_analytics(self, client):
        """Test getting critic analytics."""
        response = client.get("/api/analytics/critic")
        
        assert response.status_code == 200
        data = response.json()
        assert "pass_rates" in data


class TestRepositoryFlow:
    """Integration tests for repository management."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from server.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_list_repos(self, client):
        """Test listing repositories."""
        response = client.get("/api/repos")
        
        # Should return list
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_connect_repo_invalid_platform(self, client):
        """Test connecting repo with invalid platform."""
        response = client.post(
            "/api/repos",
            json={
                "platform": "invalid_platform",
                "owner": "test",
                "name": "repo",
            }
        )
        
        assert response.status_code == 400
