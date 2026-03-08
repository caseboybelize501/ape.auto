"""
APE - Autonomous Production Engineer
Distributed Tracing

OpenTelemetry integration for distributed tracing.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.semconv.trace import SpanAttributes
from contextlib import contextmanager
from typing import Optional, Generator
import os


# ===========================================
# Configuration
# ===========================================

JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "localhost:4317")
TRACE_SAMPLE_RATE = float(os.getenv("TRACE_SAMPLE_RATE", "1.0"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "ape-auto")


# ===========================================
# Setup Functions
# ===========================================

def setup_tracing(
    exporter: str = "console",
    sample_rate: float = TRACE_SAMPLE_RATE
) -> None:
    """
    Configure OpenTelemetry tracing.
    
    Args:
        exporter: Exporter type (console, jaeger, otlp)
        sample_rate: Sampling rate (0.0-1.0)
    """
    # Set up tracer provider with sampling
    provider = TracerProvider(
        sampler=trace.TraceIdRatioBased(sample_rate)
    )
    trace.set_tracer_provider(provider)
    
    # Configure exporter
    if exporter == "jaeger":
        jaeger_exporter = JaegerExporter(
            collector_endpoint=JAEGER_ENDPOINT,
        )
        provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
    elif exporter == "otlp":
        otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
        provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    else:  # console
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(
        # app will be passed when creating the app
    )
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name
    
    Returns:
        Configured tracer
    """
    return trace.get_tracer(f"ape.{name}")


# ===========================================
# Decorators and Context Managers
# ===========================================

@contextmanager
def trace_request(
    span_name: str,
    attributes: Optional[dict] = None
) -> Generator[trace.Span, None, None]:
    """
    Context manager for tracing a request.
    
    Args:
        span_name: Span name
        attributes: Optional span attributes
    
    Yields:
        Active span
    """
    tracer = get_tracer("request")
    
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        yield span


def trace_generation_run(run_id: str):
    """
    Decorator for tracing a generation run.
    
    Args:
        run_id: Generation run ID
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer("generation")
            
            with tracer.start_as_current_span("generation_run") as span:
                span.set_attribute("generation.run_id", run_id)
                span.set_attribute(SpanAttributes.CODE_FUNCTION, func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("generation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("generation.status", "failed")
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_critic_pass(pass_number: int, file_path: str):
    """
    Decorator for tracing a critic pass.
    
    Args:
        pass_number: Pass number (1-4)
        file_path: File being critiqued
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer("critic")
            
            with tracer.start_as_current_span("critic_pass") as span:
                span.set_attribute("critic.pass_number", pass_number)
                span.set_attribute("critic.file_path", file_path)
                span.set_attribute(SpanAttributes.CODE_FUNCTION, func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("critic.result", "pass")
                    return result
                except Exception as e:
                    span.set_attribute("critic.result", "fail")
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_deployment(deployment_id: str, environment: str):
    """
    Decorator for tracing a deployment.
    
    Args:
        deployment_id: Deployment ID
        environment: Environment name
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer("deployment")
            
            with tracer.start_as_current_span("deployment") as span:
                span.set_attribute("deployment.id", deployment_id)
                span.set_attribute("deployment.environment", environment)
                span.set_attribute(SpanAttributes.CODE_FUNCTION, func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("deployment.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("deployment.status", "failed")
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


# ===========================================
# Custom Span Attributes
# ===========================================

class APEAttributes:
    """Custom span attribute keys for APE."""
    
    # Generation
    GENERATION_RUN_ID = "ape.generation.run_id"
    GENERATION_LEVEL = "ape.generation.level"
    GENERATION_FILE_PATH = "ape.generation.file_path"
    GENERATION_STATUS = "ape.generation.status"
    
    # Critic
    CRITIC_PASS_NUMBER = "ape.critic.pass_number"
    CRITIC_RESULT = "ape.critic.result"
    CRITIC_REPAIR_COUNT = "ape.critic.repair_count"
    
    # Deployment
    DEPLOYMENT_ID = "ape.deployment.id"
    DEPLOYMENT_ENVIRONMENT = "ape.deployment.environment"
    DEPLOYMENT_STATUS = "ape.deployment.status"
    
    # Gates
    GATE_NUMBER = "ape.gate.number"
    GATE_DECISION = "ape.gate.decision"
    GATE_APPROVER = "ape.gate.approver"
