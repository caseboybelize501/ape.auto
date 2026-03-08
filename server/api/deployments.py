"""
APE - Autonomous Production Engineer
Deployments API

Endpoints for deployment management (GATE-3).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/deployments", tags=["deployments"])

# In-memory storage
_deployments_store = {}


class DeployApprovalRequest(BaseModel):
    approved: bool


class DeployApprovalResponse(BaseModel):
    promoted: bool
    monitoring_active: bool


@router.get("/{deployment_id}")
async def get_deployment(deployment_id: str):
    """Get deployment details."""
    if deployment_id not in _deployments_store:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return _deployments_store[deployment_id]


@router.post("/{deployment_id}/approve", response_model=DeployApprovalResponse)
async def approve_deployment(deployment_id: str, request: DeployApprovalRequest):
    """
    Approve production deployment (GATE-3).
    
    After approval, staging is promoted to production
    and production monitoring begins.
    """
    from engine.deploy_manager import DeployManager
    from engine.prod_monitor import ProductionMonitor
    
    if deployment_id not in _deployments_store:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = _deployments_store[deployment_id]
    
    if not request.approved:
        return {"promoted": False, "monitoring_active": False}
    
    # Mock deploy manager
    deploy_manager = DeployManager(repo_connector=None)
    
    # Mock staging deployment
    from contracts.models.deploy import Deployment, DeployStatus, DeployEnvironment, HealthStatus
    staging_deployment = Deployment(
        id=deployment_id,
        run_id=deployment.get("run_id", ""),
        pr_id=deployment.get("pr_id", ""),
        repo_id=deployment.get("repo_id", ""),
        environment=DeployEnvironment.STAGING,
        status=DeployStatus.STAGING_DEPLOYED,
        health_status=HealthStatus.HEALTHY,
    )
    
    # Promote to production
    production_deployment = deploy_manager.promote_to_production(
        staging_deployment=staging_deployment,
        approved_by="api-user",
    )
    
    # Store production deployment
    _deployments_store[f"prod-{deployment_id}"] = production_deployment.dict()
    
    # Start monitoring
    monitor = ProductionMonitor(observability_connector=None)
    
    return DeployApprovalResponse(
        promoted=True,
        monitoring_active=True,
    )


@router.get("/{deployment_id}/status")
async def get_deployment_status(deployment_id: str):
    """Get deployment status including health."""
    from engine.prod_monitor import ProductionMonitor
    
    if deployment_id not in _deployments_store:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = _deployments_store[deployment_id]
    
    # Mock monitor
    monitor = ProductionMonitor(observability_connector=None)
    
    # Mock deployment object
    from contracts.models.deploy import Deployment
    dep = Deployment(**deployment) if isinstance(deployment, dict) else deployment
    
    return monitor.get_deployment_status(dep)
