"""
APE - Autonomous Production Engineer
Contract: Architecture Models

Immutable Pydantic schemas for architecture planning.
These models define how requirements map to codebase changes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"
    MOVE = "move"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    SECURITY = "security"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    TECHNICAL_DEBT = "technical_debt"


class ModuleSpec(BaseModel):
    """
    Specification for a new module to be created.
    """
    name: str = Field(..., description="Module name, e.g., 'user_service'")
    path: str = Field(..., description="Filesystem path relative to repo root")
    description: str = Field(..., description="Module responsibility")
    exports: list[str] = Field(default_factory=list, description="Public API exports")
    dependencies: list[str] = Field(default_factory=list, description="Module dependencies")
    estimated_complexity: str = Field("medium", enum=["low", "medium", "high"])
    
    class Config:
        frozen = True


class ModuleChange(BaseModel):
    """
    Specification for modifying an existing module.
    """
    path: str = Field(..., description="Existing module path")
    change_type: ChangeType = Field(..., description="Type of change")
    description: str = Field(..., description="What is being changed and why")
    affected_functions: list[str] = Field(default_factory=list)
    new_functions: list[str] = Field(default_factory=list)
    removed_functions: list[str] = Field(default_factory=list)
    estimated_complexity: str = Field("medium", enum=["low", "medium", "high"])
    
    class Config:
        frozen = True


class DataFlowNode(BaseModel):
    """
    A node in the data flow diagram.
    """
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Type: api, service, database, cache, queue, external")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None


class DataFlowEdge(BaseModel):
    """
    An edge in the data flow diagram.
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    protocol: str = Field(..., description="Communication protocol: http, grpc, async, sql")
    description: Optional[str] = None
    data_types: list[str] = Field(default_factory=list)


class DataFlowDiagram(BaseModel):
    """
    Complete data flow for the requirement implementation.
    """
    nodes: list[DataFlowNode] = Field(default_factory=list)
    edges: list[DataFlowEdge] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list, description="Where data enters the system")
    exit_points: list[str] = Field(default_factory=list, description="Where data exits the system")


class SchemaChange(BaseModel):
    """
    Database/cache schema modification.
    """
    table_or_collection: str = Field(..., description="Target table/collection name")
    change_type: ChangeType = Field(..., description="Type of schema change")
    columns_or_fields: list[dict] = Field(default_factory=list)
    indexes: list[dict] = Field(default_factory=list)
    migration_required: bool = Field(True, description="Whether DB migration is needed")
    rollback_possible: bool = Field(True, description="Whether rollback is safe")
    
    class Config:
        frozen = True


class AsyncSpec(BaseModel):
    """
    Asynchronous boundary specification.
    """
    boundary_id: str = Field(..., description="Unique identifier")
    source_module: str = Field(..., description="Module producing events/messages")
    target_module: str = Field(..., description="Module consuming events/messages")
    mechanism: str = Field(..., description="Queue, event bus, webhook, etc.")
    message_schema: dict = Field(..., description="Message/event schema")
    delivery_guarantee: str = Field("at-least-once", enum=["at-most-once", "at-least-once", "exactly-once"])
    retry_policy: Optional[dict] = None
    
    class Config:
        frozen = True


class Risk(BaseModel):
    """
    Identified risk in the architecture.
    """
    id: str = Field(..., description="Unique identifier, e.g., RISK-001")
    category: RiskCategory = Field(..., description="Risk category")
    level: RiskLevel = Field(..., description="Risk severity")
    description: str = Field(..., description="Risk description")
    mitigation: Optional[str] = Field(None, description="Proposed mitigation strategy")
    affected_areas: list[str] = Field(default_factory=list)
    
    class Config:
        frozen = True


class ArchitecturePlan(BaseModel):
    """
    Complete architecture plan for implementing a requirement.
    This is generated from RequirementSpec + CodebaseGraph.
    """
    id: str = Field(..., description="Unique architecture plan ID")
    requirement_spec_id: str = Field(..., description="Reference to RequirementSpec")
    repo_id: str = Field(..., description="Target repository ID")
    
    modified_modules: list[ModuleChange] = Field(default_factory=list)
    new_modules: list[ModuleSpec] = Field(default_factory=list)
    data_flow: Optional[DataFlowDiagram] = None
    persistence_changes: list[SchemaChange] = Field(default_factory=list)
    async_boundaries: list[AsyncSpec] = Field(default_factory=list)
    risk_flags: list[Risk] = Field(default_factory=list)
    
    # Codebase patterns to follow
    existing_patterns: dict = Field(default_factory=dict, description="Extracted patterns from codebase")
    test_patterns: dict = Field(default_factory=dict, description="Test patterns from codebase")
    naming_conventions: dict = Field(default_factory=dict, description="Naming conventions to follow")
    
    # Approval tracking
    status: str = Field("draft", enum=["draft", "pending_approval", "approved", "rejected", "revised"])
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def get_all_affected_paths(self) -> list[str]:
        """Return all file paths that will be touched."""
        paths = []
        for mod in self.modified_modules:
            paths.append(mod.path)
        for mod in self.new_modules:
            paths.append(mod.path)
        return paths
    
    def has_critical_risks(self) -> bool:
        """Check if any critical risks are flagged."""
        return any(r.level == RiskLevel.CRITICAL for r in self.risk_flags)
