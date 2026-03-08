"""
APE - Autonomous Production Engineer
Prometheus Metrics

Custom metrics for APE pipeline monitoring.
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from prometheus_client.multiprocess import MultiProcessCollector
import time
from typing import Optional, Dict
from datetime import datetime


# ===========================================
# Registry
# ===========================================

registry = CollectorRegistry()


# ===========================================
# Generation Metrics
# ===========================================

generation_runs_total = Counter(
    'ape_generation_runs_total',
    'Total number of generation runs',
    ['status', 'repo_id'],
    registry=registry,
)

generation_duration = Histogram(
    'ape_generation_duration_seconds',
    'Generation run duration in seconds',
    ['status'],
    buckets=(60, 300, 600, 1200, 1800, 3600, float('inf')),
    registry=registry,
)

generation_files_total = Counter(
    'ape_generation_files_total',
    'Total files generated',
    ['status', 'level'],
    registry=registry,
)

generation_level_duration = Histogram(
    'ape_generation_level_duration_seconds',
    'Generation level duration in seconds',
    ['level'],
    buckets=(10, 30, 60, 120, 300, float('inf')),
    registry=registry,
)


# ===========================================
# Critic Metrics
# ===========================================

critic_passes_total = Counter(
    'ape_critic_passes_total',
    'Total critic pass executions',
    ['pass_number', 'result'],
    registry=registry,
)

critic_repairs_total = Counter(
    'ape_critic_repairs_total',
    'Total repair attempts',
    ['result'],
    registry=registry,
)

critic_halts_total = Counter(
    'ape_critic_halts_total',
    'Total generation halts (GATE-4)',
    ['level'],
    registry=registry,
)

critic_duration = Summary(
    'ape_critic_duration_seconds',
    'Critic execution duration',
    ['pass_number'],
    registry=registry,
)


# ===========================================
# Test Metrics
# ===========================================

test_runs_total = Counter(
    'ape_test_runs_total',
    'Total test runs',
    ['type', 'result'],
    registry=registry,
)

test_coverage = Gauge(
    'ape_test_coverage_percent',
    'Test coverage percentage',
    ['type'],
    registry=registry,
)


# ===========================================
# Deployment Metrics
# ===========================================

deployments_total = Counter(
    'ape_deployments_total',
    'Total deployments',
    ['environment', 'status'],
    registry=registry,
)

deployment_duration = Histogram(
    'ape_deployment_duration_seconds',
    'Deployment duration',
    ['environment'],
    buckets=(30, 60, 120, 300, 600, float('inf')),
    registry=registry,
)

production_health = Gauge(
    'ape_production_health',
    'Production health status (1=healthy, 0=unhealthy)',
    ['deployment_id'],
    registry=registry,
)

regressions_total = Counter(
    'ape_regressions_total',
    'Total production regressions',
    ['severity', 'action'],
    registry=registry,
)

rollbacks_total = Counter(
    'ape_rollbacks_total',
    'Total rollbacks',
    ['reason'],
    registry=registry,
)


# ===========================================
# API Metrics
# ===========================================

api_requests_total = Counter(
    'ape_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=registry,
)

api_request_duration = Histogram(
    'ape_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 5, 10, float('inf')),
    registry=registry,
)

websocket_connections = Gauge(
    'ape_websocket_connections',
    'Active WebSocket connections',
    registry=registry,
)


# ===========================================
# Metrics Collector Class
# ===========================================

class MetricsCollector:
    """
    Centralized metrics collection for APE.
    """
    
    def __init__(self):
        self.registry = registry
    
    # Generation
    def record_generation_start(self, repo_id: str) -> None:
        """Record generation run start."""
        pass  # Tracked by duration timer
    
    def record_generation_complete(
        self,
        repo_id: str,
        status: str,
        duration_seconds: float,
        files_generated: int
    ) -> None:
        """Record generation run completion."""
        generation_runs_total.labels(status=status, repo_id=repo_id).inc()
        generation_duration.labels(status=status).observe(duration_seconds)
        generation_files_total.labels(status=status, level='all').inc(files_generated)
    
    def record_level_complete(
        self,
        level: int,
        duration_seconds: float
    ) -> None:
        """Record level completion."""
        generation_level_duration.labels(level=str(level)).observe(duration_seconds)
    
    # Critic
    def record_critic_pass(
        self,
        pass_number: int,
        result: str,
        duration_seconds: float
    ) -> None:
        """Record critic pass execution."""
        critic_passes_total.labels(pass_number=str(pass_number), result=result).inc()
        critic_duration.labels(pass_number=str(pass_number)).observe(duration_seconds)
    
    def record_repair(self, result: str) -> None:
        """Record repair attempt."""
        critic_repairs_total.labels(result=result).inc()
    
    def record_halt(self, level: int) -> None:
        """Record generation halt."""
        critic_halts_total.labels(level=str(level)).inc()
    
    # Tests
    def record_test_run(self, test_type: str, result: str) -> None:
        """Record test run."""
        test_runs_total.labels(type=test_type, result=result).inc()
    
    def record_coverage(self, test_type: str, coverage_percent: float) -> None:
        """Record test coverage."""
        test_coverage.labels(type=test_type).set(coverage_percent)
    
    # Deployment
    def record_deployment(
        self,
        environment: str,
        status: str,
        duration_seconds: float
    ) -> None:
        """Record deployment."""
        deployments_total.labels(environment=environment, status=status).inc()
        deployment_duration.labels(environment=environment).observe(duration_seconds)
    
    def record_production_health(
        self,
        deployment_id: str,
        healthy: bool
    ) -> None:
        """Record production health status."""
        production_health.labels(deployment_id=deployment_id).set(1 if healthy else 0)
    
    def record_regression(
        self,
        severity: str,
        action: str
    ) -> None:
        """Record production regression."""
        regressions_total.labels(severity=severity, action=action).inc()
    
    def record_rollback(self, reason: str) -> None:
        """Record rollback."""
        rollbacks_total.labels(reason=reason).inc()
    
    # API
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration_seconds: float
    ) -> None:
        """Record API request."""
        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration_seconds)
    
    # WebSocket
    def record_websocket_connections(self, count: int) -> None:
        """Record active WebSocket connections."""
        websocket_connections.set(count)
    
    # Metrics endpoint
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format."""
        return generate_latest(self.registry)


# Global metrics collector
metrics = MetricsCollector()


# ===========================================
# Context Managers for Timing
# ===========================================

class GenerationTimer:
    """Context manager for timing generation runs."""
    
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = 'failed' if exc_type else 'completed'
        metrics.record_generation_complete(self.repo_id, status, duration, 0)


class CriticPassTimer:
    """Context manager for timing critic passes."""
    
    def __init__(self, pass_number: int):
        self.pass_number = pass_number
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        result = 'fail' if exc_type else 'pass'
        metrics.record_critic_pass(self.pass_number, result, duration)
