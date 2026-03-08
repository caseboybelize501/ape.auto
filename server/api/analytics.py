"""
APE - Autonomous Production Engineer
Analytics API

Endpoints for usage analytics and metrics.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(period: str = "month"):
    """Get usage analytics."""
    # Mock analytics data
    # In production, this would query database
    
    now = datetime.utcnow()
    
    if period == "day":
        start = now - timedelta(days=1)
    elif period == "week":
        start = now - timedelta(weeks=1)
    elif period == "year":
        start = now - timedelta(days=365)
    else:  # month
        start = now - timedelta(days=30)
    
    return {
        "period": period,
        "start": start.isoformat(),
        "end": now.isoformat(),
        "total_runs": 42,
        "successful_runs": 38,
        "failed_runs": 4,
        "average_cycle_time_minutes": 12.5,
        "critic_pass_rates": {
            "pass1_syntax": 0.95,
            "pass2_contract": 0.88,
            "pass3_completeness": 0.82,
            "pass4_logic": 0.79,
        },
        "deployments": 15,
        "rollbacks": 1,
        "self_repairs": 3,
        "top_affected_modules": [
            {"path": "src/api/users.py", "changes": 12},
            {"path": "src/services/auth.py", "changes": 8},
            {"path": "src/models/user.py", "changes": 6},
        ],
        "requirements_by_source": {
            "manual": 20,
            "ticket": 15,
            "prd": 5,
            "voice": 2,
        },
    }


@router.get("/runs")
async def get_runs_analytics():
    """Get generation runs analytics."""
    return {
        "total": 42,
        "by_status": {
            "completed": 38,
            "failed": 3,
            "blocked": 1,
        },
        "average_duration_minutes": 12.5,
        "by_level": {
            "0": {"files": 5, "avg_time": 2.1},
            "1": {"files": 8, "avg_time": 3.2},
            "2": {"files": 12, "avg_time": 4.5},
            "3": {"files": 6, "avg_time": 2.7},
        },
    }


@router.get("/critic")
async def get_critic_analytics():
    """Get critic pass analytics."""
    return {
        "pass_rates": {
            "pass1_syntax": {
                "first_try": 0.85,
                "after_repair": 0.98,
            },
            "pass2_contract": {
                "first_try": 0.72,
                "after_repair": 0.92,
            },
            "pass3_completeness": {
                "first_try": 0.68,
                "after_repair": 0.88,
            },
            "pass4_logic": {
                "first_try": 0.65,
                "after_repair": 0.85,
            },
        },
        "average_repairs_per_file": 1.2,
        "halt_rate": 0.05,
    }


@router.get("/deployments")
async def get_deployments_analytics():
    """Get deployment analytics."""
    return {
        "total": 15,
        "successful": 14,
        "rollbacks": 1,
        "success_rate": 0.93,
        "average_time_to_prod_minutes": 25,
        "regressions_detected": 2,
        "self_repairs_successful": 1,
    }
