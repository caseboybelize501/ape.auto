"""
APE - Autonomous Production Engineer
Generations API

Endpoints for monitoring code generation progress.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/generations", tags=["generations"])

# In-memory storage
_runs_store = {}


@router.get("")
async def list_generations(
    req_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List generation runs."""
    results = list(_runs_store.values())
    
    if req_id:
        results = [r for r in results if r.requirement_spec_id == req_id]
    if status:
        results = [r for r in results if r.status.value == status]
    
    return [r.dict() for r in results]


@router.get("/{run_id}")
async def get_generation(run_id: str):
    """Get generation run details."""
    if run_id not in _runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = _runs_store[run_id]
    
    return {
        **run.dict(),
        "progress": {
            "current_level": run.current_level,
            "total_levels": run.total_levels,
            "files_generated": run.total_files_generated,
            "files_passed": run.total_files_passed,
        }
    }


@router.get("/{run_id}/levels/{level}")
async def get_generation_level(run_id: str, level: int):
    """Get generation results for a specific level."""
    if run_id not in _runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = _runs_store[run_id]
    
    # Find level results
    level_results = [
        lr for lr in run.level_results
        if lr.level == level
    ]
    
    if not level_results:
        raise HTTPException(status_code=404, detail="Level results not found")
    
    return {
        "run_id": run_id,
        "level": level,
        "results": [lr.dict() for lr in level_results],
    }
