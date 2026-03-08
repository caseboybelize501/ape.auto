"""
APE - Autonomous Production Engineer
API Package

REST API endpoints for all APE operations.
"""

from server.api.requirements import router as requirements_router
from server.api.plans import router as plans_router
from server.api.generations import router as generations_router
from server.api.critic import router as critic_router
from server.api.prs import router as prs_router
from server.api.deployments import router as deployments_router
from server.api.incidents import router as incidents_router
from server.api.repos import router as repos_router
from server.api.analytics import router as analytics_router
from server.api.auth import router as auth_router

__all__ = [
    "requirements_router",
    "plans_router",
    "generations_router",
    "critic_router",
    "prs_router",
    "deployments_router",
    "incidents_router",
    "repos_router",
    "analytics_router",
    "auth_router",
]
