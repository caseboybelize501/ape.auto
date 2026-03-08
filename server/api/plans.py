"""
APE - Autonomous Production Engineer
Plans API

Endpoints for architecture plan review and approval (GATE-1).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/plans", tags=["plans"])

# In-memory storage
_plans_store = {}


class PlanApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class PlanApprovalResponse(BaseModel):
    run_id: str
    build_plan: dict


@router.get("/{req_id}")
async def get_plan(req_id: str):
    """Get architecture plan for a requirement."""
    from engine.llm_client import LLMClient
    from engine.arch_planner import ArchitecturePlanner
    from engine.codebase_graph import CodebaseGraphBuilder
    from contracts.models.graph import DependencyGraph
    
    # Get requirement spec
    from server.api.requirements import _specs_store
    if req_id not in _specs_store:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    spec = _specs_store[req_id]
    
    # Check if plan already exists
    if req_id in _plans_store:
        return _plans_store[req_id].dict()
    
    # Create plan
    llm = LLMClient()
    planner = ArchitecturePlanner(llm)
    
    # Mock graph
    graph = DependencyGraph(
        id="mock-graph",
        repo_id=spec.repo_id,
        nodes=[],
        edges=[],
        cycle_free=True,
        generated_at=datetime.utcnow(),
    )
    
    plan = planner.create_plan(
        requirement_spec=spec,
        codebase_graph=graph,
    )
    
    _plans_store[req_id] = plan
    
    return plan.dict()


@router.post("/{req_id}/approve", response_model=PlanApprovalResponse)
async def approve_plan(req_id: str, request: PlanApprovalRequest):
    """
    Approve architecture plan (GATE-1).
    
    After approval, code generation begins using the
    dependency-aware, topologically-sorted pipeline.
    """
    from engine.build_orchestrator import BuildOrchestrator
    from engine.dep_graph_builder import DependencyGraphBuilder
    from engine.cycle_detector import CycleDetector
    from engine.topo_sorter import TopologicalSorter
    
    if req_id not in _plans_store:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan = _plans_store[req_id]
    
    if not request.approved:
        plan.status = "rejected"
        plan.rejection_reason = request.notes
        raise HTTPException(
            status_code=400,
            detail=f"Plan rejected: {request.notes or 'No reason provided'}"
        )
    
    # Approve plan
    plan.status = "approved"
    plan.approved_at = datetime.utcnow()
    plan.approved_by = "api-user"
    
    # Build dependency graph
    graph_builder = DependencyGraphBuilder()
    dep_graph = graph_builder.build(
        architecture_plan=plan,
        existing_graph=DependencyGraph(
            id="mock-graph",
            repo_id=plan.repo_id,
            nodes=[],
            edges=[],
            cycle_free=True,
            generated_at=datetime.utcnow(),
        )
    )
    
    # Detect cycles
    cycle_detector = CycleDetector()
    cycle_free, cycles = cycle_detector.detect(dep_graph)
    
    if not cycle_free:
        # Return cycle info for human review
        return {
            "error": "cycles_detected",
            "cycles": [c.dict() for c in cycles],
            "report": cycle_detector.format_cycle_report(dep_graph),
        }
    
    # Topological sort
    topo_sorter = TopologicalSorter()
    build_plan = topo_sorter.sort(dep_graph)
    
    # Update plan references
    build_plan.requirement_spec_id = req_id
    build_plan.architecture_plan_id = plan.id
    
    # Start generation run
    orchestrator = BuildOrchestrator()
    run = orchestrator.start_generation_run(
        build_plan=build_plan,
        requirement_spec_id=req_id,
        architecture_plan_id=plan.id,
        repo_id=plan.repo_id,
    )
    
    # Store run (would be in database)
    from server.api.generations import _runs_store
    _runs_store[run.id] = run
    
    return PlanApprovalResponse(
        run_id=run.id,
        build_plan=build_plan.dict(),
    )
