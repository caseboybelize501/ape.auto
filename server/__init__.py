"""
APE - Autonomous Production Engineer
Server Package

FastAPI application with:
- REST API endpoints
- Celery workers
- WebSocket support for real-time updates
"""

from server.main import app, app_config

__all__ = ["app", "app_config"]
