"""
APE - Autonomous Production Engineer
Repositories API

Endpoints for repository management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/repos", tags=["repos"])

# In-memory storage
_repos_store = {}


class ConnectRepoRequest(BaseModel):
    platform: str  # github, gitlab
    owner: str
    name: str
    ci_platform: Optional[str] = None


class Repo(BaseModel):
    id: str
    platform: str
    owner: str
    name: str
    full_name: str
    connection_status: str
    codebase_graph_built: bool


@router.get("", response_model=List[Repo])
async def list_repos():
    """List connected repositories."""
    return list(_repos_store.values())


@router.post("", response_model=Repo)
async def connect_repo(request: ConnectRepoRequest):
    """Connect a new repository."""
    from connectors.github import GitHubConnector
    from connectors.gitlab import GitLabConnector
    
    repo_id = f"{request.platform}:{request.owner}/{request.name}"
    
    if repo_id in _repos_store:
        raise HTTPException(status_code=400, detail="Repository already connected")
    
    # Test connection
    if request.platform == "github":
        connector = GitHubConnector(token="mock-token")
        success, message = connector.test_connection()
    elif request.platform == "gitlab":
        connector = GitLabConnector(token="mock-token")
        success, message = connector.test_connection()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {request.platform}")
    
    repo = Repo(
        id=repo_id,
        platform=request.platform,
        owner=request.owner,
        name=request.name,
        full_name=f"{request.owner}/{request.name}",
        connection_status="connected" if success else "error",
        codebase_graph_built=False,
    )
    
    _repos_store[repo_id] = repo.dict()
    
    return repo


@router.get("/{repo_id}")
async def get_repo(repo_id: str):
    """Get repository details."""
    if repo_id not in _repos_store:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return _repos_store[repo_id]


@router.post("/{repo_id}/scan")
async def scan_repo(repo_id: str):
    """Trigger codebase graph build for repository."""
    from engine.codebase_graph import CodebaseGraphBuilder
    
    if repo_id not in _repos_store:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo = _repos_store[repo_id]
    
    # Mock scan
    # In production, this would:
    # 1. Clone repository
    # 2. Build codebase graph
    # 3. Store graph
    
    repo["codebase_graph_built"] = True
    repo["last_scan"] = "now"
    
    return {
        "status": "scanning",
        "repo_id": repo_id,
        "estimated_time_seconds": 300,  # 5 minutes for average repo
    }


@router.delete("/{repo_id}")
async def disconnect_repo(repo_id: str):
    """Disconnect a repository."""
    if repo_id not in _repos_store:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    del _repos_store[repo_id]
    
    return {"status": "disconnected", "repo_id": repo_id}
