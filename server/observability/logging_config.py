"""
APE - Autonomous Production Engineer
Structured Logging Configuration

Logging setup with structlog for structured, contextual logs.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.types import Processor


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    environment: str = "development"
) -> None:
    """
    Configure structured logging for APE.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json, console)
        environment: Environment name (development, staging, production)
    """
    
    # Configure log level
    logging.basicConfig(
        format='%(message)s',
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog processors
    processors: list[Processor] = [
        # Contextvars for async context
        structlog.contextvars.merge_contextvars,
        
        # Add process info
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Stack info
        structlog.processors.CallerFrameAdder(),
        structlog.processors.StackInfoRenderer(),
        
        # Unicode handling
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add format-specific processors
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Global logger instance
structlog_logger = get_logger("ape")


# ===========================================
# Logging Context Managers
# ===========================================

class LogContext:
    """Context manager for adding structured context to logs."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.clear_contextvars()


def log_generation_event(
    run_id: str,
    event: str,
    **kwargs
) -> None:
    """
    Log a generation event with structured context.
    
    Args:
        run_id: Generation run ID
        event: Event name
        **kwargs: Additional context
    """
    logger = get_logger("generation")
    with LogContext(run_id=run_id, event=event):
        logger.info(event, **kwargs)


def log_critic_event(
    run_id: str,
    level: int,
    file_path: str,
    pass_number: int,
    result: str,
    **kwargs
) -> None:
    """
    Log a critic event.
    
    Args:
        run_id: Generation run ID
        level: Critic level
        file_path: File being critiqued
        pass_number: Pass number (1-4)
        result: Pass/fail result
        **kwargs: Additional context
    """
    logger = get_logger("critic")
    with LogContext(
        run_id=run_id,
        level=level,
        file_path=file_path,
        pass_number=pass_number
    ):
        logger.info(
            "critic_pass",
            result=result,
            **kwargs
        )


def log_deployment_event(
    deployment_id: str,
    environment: str,
    event: str,
    **kwargs
) -> None:
    """
    Log a deployment event.
    
    Args:
        deployment_id: Deployment ID
        environment: Environment name
        event: Event name
        **kwargs: Additional context
    """
    logger = get_logger("deployment")
    with LogContext(
        deployment_id=deployment_id,
        environment=environment,
        event=event
    ):
        logger.info(event, **kwargs)


def log_error(
    logger_name: str,
    error: Exception,
    **kwargs
) -> None:
    """
    Log an error with exception details.
    
    Args:
        logger_name: Logger name
        error: Exception instance
        **kwargs: Additional context
    """
    logger = get_logger(logger_name)
    logger.error(
        "error",
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs
    )
