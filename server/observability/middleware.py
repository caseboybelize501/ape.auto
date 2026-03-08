"""
APE - Autonomous Production Engineer
API Metrics Middleware

Prometheus metrics for API requests.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable

from server.observability.metrics import metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect API request metrics.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        metrics.record_api_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration_seconds=duration,
        )
        
        return response


def setup_metrics_middleware(app) -> None:
    """
    Add metrics middleware to FastAPI app.
    
    Args:
        app: FastAPI application
    """
    app.add_middleware(MetricsMiddleware)


# Metrics endpoint for Prometheus
def create_metrics_endpoint(app) -> None:
    """
    Add Prometheus metrics endpoint.
    
    Args:
        app: FastAPI application
    """
    from fastapi.responses import PlainTextResponse
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return PlainTextResponse(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
