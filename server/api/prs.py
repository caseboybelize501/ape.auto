"""
APE - Autonomous Production Engineer
PRs API

Endpoints for pull request management (GATE-2).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/prs", tags=["prs"])

# In-memory storage
_prs_store = {}


class PRApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class PRApprovalResponse(BaseModel):
    deploy_id: str
    staging_url: str


@router.get("/{run_id}")
async def get_pr(run_id: str):
    """Get PR for a generation run."""
    # Find PR by run_id
    for pr in _prs_store.values():
        if pr.get("run_id") == run_id:
            return pr
    
    raise HTTPException(status_code=404, detail="PR not found")


@router.post("/{run_id}/approve", response_model=PRApprovalResponse)
async def approve_pr(run_id: str, request: PRApprovalRequest):
    """
    Approve PR (GATE-2).
    
    After approval, the PR is merged and deployed to staging.
    """
    from engine.deploy_manager import DeployManager
    from connectors.github import GitHubConnector
    
    # Find PR
    pr_data = None
    for pr_id, pr in _prs_store.items():
        if pr.get("run_id") == run_id:
            pr_data = pr
            break
    
    if not pr_data:
        raise HTTPException(status_code=404, detail="PR not found")
    
    if not request.approved:
        return {"error": "PR rejected", "notes": request.notes}
    
    # Create deploy manager
    # In production, these would be properly initialized
    repo_connector = GitHubConnector(token="mock-token")
    deploy_manager = DeployManager(repo_connector=repo_connector)
    
    # Mock PR object
    from contracts.models.deploy import PullRequest, PRStatus
    pr = PullRequest(
        id=pr_data.get("id"),
        run_id=run_id,
        repo_id=pr_data.get("repo_id", "mock/repo"),
        platform="github",
        pr_number=pr_data.get("pr_number", 1),
        status=PRStatus.APPROVED,
    )
    
    # Deploy to staging
    deployment = deploy_manager.deploy_to_staging(pr)
    
    return PRApprovalResponse(
        deploy_id=deployment.id,
        staging_url=deployment.environment_url or "https://staging.example.com",
    )
