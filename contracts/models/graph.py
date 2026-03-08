"""
APE - Autonomous Production Engineer
Contract: Dependency Graph Models

Immutable Pydantic schemas for codebase dependency graph,
topological sort results, and build plans.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    NEW = "new"
    MODIFIED = "modified"
    UNTOUCHED = "untouched"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EdgeType(str, Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    DEPENDS_ON = "depends_on"
    TESTS = "tests"


class Node(BaseModel):
    """
    A node in the dependency graph representing a file/module.
    """
    id: str = Field(..., description="File path as unique identifier")
    type: NodeType = Field(..., description="Node type: new, modified, or untouched")
    module: str = Field(..., description="Module name")
    language: str = Field("python", description="File language")
    
    # Interface contracts
    exports: list[str] = Field(default_factory=list, description="Exported symbols from contracts/interfaces/")
    imports: list[str] = Field(default_factory=list, description="Declared dependencies")
    
    # Traceability
    test_file: Optional[str] = Field(None, description="Associated test file path")
    fr_refs: list[str] = Field(default_factory=list, description="Which FRs this file satisfies")
    
    # Metadata
    estimated_complexity: Complexity = Complexity.MEDIUM
    test_coverage: Optional[float] = Field(None, description="Existing test coverage percentage")
    change_frequency: Optional[str] = Field(None, description="How often this file changes: low, medium, high")
    cve_exposure: list[str] = Field(default_factory=list, description="Known CVEs in dependencies")
    
    # Generation metadata
    generated_content: Optional[str] = None
    generation_timestamp: Optional[datetime] = None
    
    class Config:
        frozen = False  # Allow content updates during generation


class Edge(BaseModel):
    """
    A directed edge in the dependency graph.
    A -> B means "A imports/depends on B"
    """
    source: str = Field(..., description="Source node ID (the dependent)")
    target: str = Field(..., description="Target node ID (the dependency)")
    type: EdgeType = Field(EdgeType.IMPORTS, description="Edge type")
    weight: float = Field(1.0, description="Edge weight for critical path calculation")
    
    class Config:
        frozen = True


class CycleInfo(BaseModel):
    """
    Information about a detected cycle.
    """
    cycle_path: list[str] = Field(..., description="The circular dependency chain")
    edges: list[tuple[str, str]] = Field(..., description="Edges forming the cycle")
    suggested_break: str = Field(..., description="Where to introduce abstraction to break cycle")
    severity: str = Field("high", enum=["low", "medium", "high"])


class DependencyGraph(BaseModel):
    """
    Complete dependency graph for the codebase + planned changes.
    """
    id: str = Field(..., description="Unique graph ID")
    repo_id: str = Field(..., description="Repository ID")
    requirement_hash: Optional[str] = Field(None, description="Associated requirement hash")
    
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    
    # Cycle detection results
    cycle_free: bool = Field(True, description="True if no cycles detected")
    cycles: list[CycleInfo] = Field(default_factory=list)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    codebase_snapshot_hash: Optional[str] = None
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_dependencies(self, node_id: str) -> list[str]:
        """Get all dependencies of a node."""
        deps = []
        for edge in self.edges:
            if edge.source == node_id:
                deps.append(edge.target)
        return deps
    
    def get_dependents(self, node_id: str) -> list[str]:
        """Get all nodes that depend on this node."""
        dependents = []
        for edge in self.edges:
            if edge.target == node_id:
                dependents.append(edge.source)
        return dependents
    
    def get_nodes_by_type(self, node_type: NodeType) -> list[Node]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes if n.type == node_type]


class Level(BaseModel):
    """
    A level in the topological sort - files that can be generated in parallel.
    """
    level: int = Field(..., description="Level number (0 = no dependencies)")
    files: list[str] = Field(..., description="File paths in this level")
    parallel: bool = Field(True, description="Always true - same level = parallel safe")
    estimated_duration_seconds: Optional[int] = None
    actual_duration_seconds: Optional[int] = None
    status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed", "blocked"])
    
    class Config:
        frozen = False


class ChordTask(BaseModel):
    """
    Celery chord task specification.
    """
    group_tasks: list[str] = Field(..., description="Parallel tasks in the group")
    callback_task: str = Field(..., description="Callback after all group tasks complete")
    level: int = Field(..., description="Associated build level")


class ChainTask(BaseModel):
    """
    Celery chain task specification.
    """
    tasks: list[str] = Field(..., description="Sequential tasks")
    description: str


class BuildPlan(BaseModel):
    """
    Complete build plan derived from topological sort.
    This defines the exact execution order for code generation.
    """
    id: str = Field(..., description="Unique build plan ID")
    requirement_spec_id: str = Field(..., description="Reference to RequirementSpec")
    architecture_plan_id: str = Field(..., description="Reference to ArchitecturePlan")
    dependency_graph_id: str = Field(..., description="Reference to DependencyGraph")
    
    levels: list[Level] = Field(..., description="Topologically sorted levels")
    celery_chord_plan: list[ChordTask] = Field(default_factory=list)
    celery_chain_plan: list[ChainTask] = Field(default_factory=list)
    
    test_plan: list["TestLevel"] = Field(default_factory=list)  # Forward reference
    
    total_files: int = Field(..., description="Total files to generate")
    total_new_files: int = Field(..., description="New files to create")
    total_modified_files: int = Field(..., description="Existing files to modify")
    
    critical_path: list[str] = Field(default_factory=list, description="Longest chain through graph")
    estimated_duration_seconds: Optional[int] = None
    actual_duration_seconds: Optional[int] = None
    
    status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed", "blocked"])
    current_level: int = Field(0, description="Current level being processed")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def get_level(self, level_num: int) -> Optional[Level]:
        """Get level by number."""
        for level in self.levels:
            if level.level == level_num:
                return level
        return None
    
    def get_pending_levels(self) -> list[Level]:
        """Get all levels not yet completed."""
        return [l for l in self.levels if l.status == "pending"]
    
    def get_current_level_files(self) -> list[str]:
        """Get files in current level."""
        level = self.get_level(self.current_level)
        return level.files if level else []


class TestLevel(BaseModel):
    """
    Test generation level - mirrors code levels.
    """
    level: int = Field(..., description="Associated code level")
    code_files: list[str] = Field(..., description="Code files being tested")
    test_files: list[str] = Field(default_factory=list, description="Test files to generate")
    test_types: list[str] = Field(default_factory=list, description="Types: contract, acceptance, regression")
    status: str = Field("pending", enum=["pending", "in_progress", "completed", "failed"])
    
    class Config:
        frozen = False
