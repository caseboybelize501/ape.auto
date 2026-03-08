"""
APE - Autonomous Production Engineer
Requirements API

Endpoints for requirement submission and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/requirements", tags=["requirements"])

# In-memory storage (replace with database)
_requirements_store = {}
_specs_store = {}


class SubmitRequirementRequest(BaseModel):
    text: str
    repo_id: str
    priority: Optional[str] = "medium"
    source: Optional[str] = "manual"
    source_id: Optional[str] = None


class SubmitRequirementResponse(BaseModel):
    req_id: str
    spec: dict
    ambiguities: list


@router.post("", response_model=SubmitRequirementResponse)
async def submit_requirement(request: SubmitRequirementRequest):
    """
    Submit a new requirement.
    
    Extracts structured requirements from raw text using LLM.
    Returns RequirementSpec with FRs, NFRs, acceptance criteria,
    and any ambiguities that need human resolution.
    """
    from engine.llm_client import LLMClient
    from engine.req_extractor import RequirementsExtractor
    from engine.codebase_graph import CodebaseGraphBuilder
    
    # Generate requirement ID
    req_id = f"req-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Initialize extractor
    llm = LLMClient()
    extractor = RequirementsExtractor(llm)
    
    # Build codebase graph (simplified - would be cached)
    # graph_builder = CodebaseGraphBuilder("/path/to/repo")
    # graph = graph_builder.build()
    
    # Mock graph for now
    from contracts.models.graph import DependencyGraph
    graph = DependencyGraph(
        id="mock-graph",
        repo_id=request.repo_id,
        nodes=[],
        edges=[],
        cycle_free=True,
        generated_at=datetime.utcnow(),
    )
    
    # Extract requirements
    spec = extractor.extract(
        raw_text=request.text,
        repo_id=request.repo_id,
        codebase_graph=graph,
        source=request.source,
        source_id=request.source_id,
    )
    
    # Store
    _requirements_store[req_id] = spec
    _specs_store[spec.id] = spec
    
    return SubmitRequirementResponse(
        req_id=req_id,
        spec=spec.dict(),
        ambiguities=[q.dict() for q in spec.ambiguities],
    )


@router.get("", response_model=list)
async def list_requirements(
    repo_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
):
    """List requirements with optional filters."""
    results = list(_specs_store.values())
    
    if repo_id:
        results = [r for r in results if r.repo_id == repo_id]
    if status:
        results = [r for r in results if r.status.value == status]
    
    return [r.dict() for r in results[-limit:]]


@router.get("/{req_id}")
async def get_requirement(req_id: str):
    """Get requirement details by ID."""
    if req_id not in _specs_store:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    return _specs_store[req_id].dict()


class ResolveAmbiguityRequest(BaseModel):
    answer: str


@router.patch("/{req_id}/ambiguity")
async def resolve_ambiguity(
    req_id: str,
    question_id: str,
    request: ResolveAmbiguityRequest
):
    """Resolve an ambiguity in a requirement."""
    from engine.llm_client import LLMClient
    from engine.req_extractor import RequirementsExtractor
    
    if req_id not in _specs_store:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    spec = _specs_store[req_id]
    llm = LLMClient()
    extractor = RequirementsExtractor(llm)
    
    updated_spec = extractor.resolve_ambiguity(
        spec=spec,
        question_id=question_id,
        answer=request.answer,
        resolved_by="api-user",
    )
    
    _specs_store[req_id] = updated_spec
    
    return updated_spec.dict()
