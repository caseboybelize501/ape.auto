"""
APE - Autonomous Production Engineer
WebSocket Package

Real-time updates for generation progress, critic results, and notifications.
"""

from server.websocket.manager import (
    ConnectionManager,
    manager,
)

from server.websocket.handlers import (
    GenerationProgressHandler,
    CriticResultHandler,
    NotificationHandler,
)

__all__ = [
    "ConnectionManager",
    "manager",
    "GenerationProgressHandler",
    "CriticResultHandler",
    "NotificationHandler",
]
