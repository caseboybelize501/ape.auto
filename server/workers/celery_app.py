"""
APE - Autonomous Production Engineer
Celery Application

Celery configuration for async task execution.
"""

import os
from celery import Celery
from celery.schedules import crontab


def make_celery(app=None):
    """Create Celery app with FastAPI integration."""
    
    celery = Celery(
        "ape",
        broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        include=[
            "server.workers.pipeline_worker",
            "server.workers.monitor_worker",
            "server.workers.graph_worker",
        ]
    )
    
    # Celery configuration
    celery.conf.update(
        # Task serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        
        # Timezone
        timezone="UTC",
        enable_utc=True,
        
        # Task settings
        task_track_started=True,
        task_time_limit=1800,  # 30 minutes
        task_soft_time_limit=1500,
        
        # Worker settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        
        # Result settings
        result_expires=3600,
        result_persistent=True,
        
        # Queue configuration
        task_default_queue="default",
        task_queues={
            "critical": {
                "exchange": "critical",
                "routing_key": "critical",
            },
            "high": {
                "exchange": "high",
                "routing_key": "high",
            },
            "default": {
                "exchange": "default",
                "routing_key": "default",
            },
            "low": {
                "exchange": "low",
                "routing_key": "low",
            },
        },
        task_default_exchange="default",
        task_default_exchange_type="direct",
        
        # Beat schedule
        beat_schedule={
            # Production monitoring every 5 minutes
            "monitor-production": {
                "task": "server.workers.monitor_worker.monitor_production",
                "schedule": crontab(minute="*/5"),
            },
            # Codebase graph refresh every hour
            "refresh-codebase-graph": {
                "task": "server.workers.graph_worker.refresh_graph",
                "schedule": crontab(minute=0),
            },
            # Dependency audit daily
            "dependency-audit": {
                "task": "server.workers.graph_worker.dependency_audit",
                "schedule": crontab(hour=2, minute=0),
            },
        },
    )
    
    return celery


# Create Celery app
celery_app = make_celery()


# Task routing
task_routes = {
    # Critical tasks (gate alerts, rollbacks)
    "server.workers.monitor_worker.trigger_rollback": {"queue": "critical"},
    "server.workers.monitor_worker.page_human": {"queue": "critical"},
    
    # High priority (critic, repair)
    "server.workers.pipeline_worker.critic_level": {"queue": "high"},
    "server.workers.pipeline_worker.repair_file": {"queue": "high"},
    
    # Default (generation, test)
    "server.workers.pipeline_worker.generate_file": {"queue": "default"},
    "server.workers.pipeline_worker.generate_tests": {"queue": "default"},
    
    # Low priority (graph refresh, analytics)
    "server.workers.graph_worker.refresh_graph": {"queue": "low"},
    "server.workers.graph_worker.dependency_audit": {"queue": "low"},
}

celery_app.conf.task_routes = task_routes
