"""
APE - Autonomous Production Engineer
Incidents API

Endpoints for production incident management (GATE-4).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/incidents", tags=["incidents"])

# In-memory storage
_incidents_store = {}


class Gate4ResponseRequest(BaseModel):
    response_type: str  # modify_architecture, modify_requirement, manual_fix, skip_file, rollback
    notes: Optional[str] = None


class Gate4Response(BaseModel):
    incident_id: str
    response_recorded: bool
    next_action: str


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get incident details."""
    if incident_id not in _incidents_store:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return _incidents_store[incident_id]


@router.post("/{incident_id}/respond", response_model=Gate4Response)
async def respond_to_gate4(incident_id: str, request: Gate4ResponseRequest):
    """
    Respond to GATE-4 halt.
    
    Human provides response to critic or repair halt.
    Options:
    - modify_architecture: Update architecture plan and restart
    - modify_requirement: Clarify requirement and restart
    - manual_fix: Human will fix manually, continue pipeline
    - skip_file: Skip the failing file
    - rollback: Rollback deployment
    """
    if incident_id not in _incidents_store:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = _incidents_store[incident_id]
    
    # Record response
    incident["human_response"] = request.response_type
    incident["human_notes"] = request.notes
    incident["response_recorded_at"] = "now"
    
    # Determine next action
    next_actions = {
        "modify_architecture": "Restarting from architecture planning phase",
        "modify_requirement": "Restarting from requirements extraction",
        "manual_fix": "Waiting for manual fix, then resuming pipeline",
        "skip_file": "Skipping file and continuing with remaining files",
        "rollback": "Initiating rollback to previous deployment",
    }
    
    return Gate4Response(
        incident_id=incident_id,
        response_recorded=True,
        next_action=next_actions.get(request.response_type, "Processing response"),
    )


@router.get("/production/{deployment_id}")
async def get_production_status(deployment_id: str):
    """Get production monitoring status for a deployment."""
    from engine.prod_monitor import ProductionMonitor
    
    # Mock monitor
    monitor = ProductionMonitor(observability_connector=None)
    
    # Mock deployment
    from contracts.models.deploy import Deployment, DeployEnvironment
    deployment = Deployment(
        id=deployment_id,
        environment=DeployEnvironment.PRODUCTION,
    )
    
    result = monitor.monitor_deployment(deployment)
    
    return {
        "signals": result.get("health", {}),
        "regressions": [result["regression"]] if result.get("regression") else [],
        "repairs": [],
        "status": result.get("status", "unknown"),
    }
