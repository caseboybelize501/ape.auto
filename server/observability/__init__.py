"""
APE - Autonomous Production Engineer
Observability Package

Metrics, logging, tracing, and monitoring.
"""

from server.observability.metrics import (
    MetricsCollector,
    metrics,
    GenerationMetrics,
    CriticMetrics,
    DeploymentMetrics,
)

from server.observability.logging_config import (
    setup_logging,
    get_logger,
    structlog_logger,
)

from server.observability.tracing import (
    setup_tracing,
    get_tracer,
    trace_request,
)

__all__ = [
    "MetricsCollector",
    "metrics",
    "GenerationMetrics",
    "CriticMetrics",
    "DeploymentMetrics",
    "setup_logging",
    "get_logger",
    "structlog_logger",
    "setup_tracing",
    "get_tracer",
    "trace_request",
]
