"""
APE - Autonomous Production Engineer
Critic API

Endpoints for critic results and halt reports.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/critic", tags=["critic"])

# In-memory storage for critic logs and halt reports
_critic_logs = {}
_halt_reports = {}


@router.get("/{run_id}/level/{level}")
async def get_critic_results(run_id: str, level: int):
    """Get critic results for a level."""
    key = f"{run_id}-level{level}"
    
    if key not in _critic_logs:
        raise HTTPException(status_code=404, detail="Critic results not found")
    
    return _critic_logs[key]


@router.get("/{run_id}/halt")
async def get_halt_report(run_id: str):
    """Get halt report if run is blocked."""
    if run_id not in _halt_reports:
        raise HTTPException(status_code=404, detail="No halt report found")
    
    return _halt_reports[run_id]


@router.post("/{run_id}/level/{level}/retry")
async def retry_level(run_id: str, level: int):
    """Retry a failed level after manual fix."""
    # This would trigger a retry of the level
    return {"status": "retry_initiated", "run_id": run_id, "level": level}
