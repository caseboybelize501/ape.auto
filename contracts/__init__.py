"""
APE - Autonomous Production Engineer
Contracts Package

This package contains all immutable contracts (Pydantic models,
interface definitions, and API specs) that serve as the ground
truth for the entire APE system.

Contracts are generated in STEP 0 before any implementation.
They are NEVER modified by the critic or repair loop.
"""

from contracts.models.requirement import (
    Priority,
    RequirementStatus,
    FunctionalRequirement,
    NonFunctionalRequirement,
    Criterion,
    Question,
    RequirementSpec,
)

from contracts.models.architecture import (
    ChangeType,
    RiskLevel,
    RiskCategory,
    ModuleSpec,
    ModuleChange,
    DataFlowNode,
    DataFlowEdge,
    DataFlowDiagram,
    SchemaChange,
    AsyncSpec,
    Risk,
    ArchitecturePlan,
)

from contracts.models.graph import (
    NodeType,
    Complexity,
    EdgeType,
    Node,
    Edge,
    CycleInfo,
    DependencyGraph,
    Level,
    ChordTask,
    ChainTask,
    BuildPlan,
    TestLevel,
)

from contracts.models.generation import (
    GenerationStatus,
    CriticPassResult,
    CriticPassType,
    GenerationJob,
    SyntaxErrorDetail,
    ContractViolationDetail,
    CriticResult,
    LevelCriticResult,
    RepairAttempt,
    HaltReport,
    GenerationRun,
)

from contracts.models.repair import (
    RepairStatus,
    RepairTrigger,
    RepairScope,
    RepairContext,
    RepairInstruction,
    RepairResult,
    MicroRepairConfig,
    ProductionRegressionSignal,
    SelfRepairSession,
)

from contracts.models.test import (
    TestType,
    TestStatus,
    TestResult,
    TestSpec,
    GeneratedTest,
    TestExecutionResult,
    TestSuiteResult,
    CoverageReport,
    TestPlan,
    TestLevel as TestLevelModel,
    TestCriticResult,
)

from contracts.models.deploy import (
    DeployStatus,
    DeployEnvironment,
    DeployStrategy,
    HealthStatus,
    PRStatus,
    PullRequest,
    Deployment,
    DeploymentMetrics,
    RollbackInfo,
    SmokeTest,
    DeployApproval,
)

from contracts.models.tenant import (
    TenantStatus,
    SubscriptionTier,
    RepoPlatform,
    ConnectionStatus,
    Tenant,
    User,
    Repo,
    SourceProfile,
    Subscription,
    AuditLog,
)

__all__ = [
    # Requirement models
    "Priority",
    "RequirementStatus",
    "FunctionalRequirement",
    "NonFunctionalRequirement",
    "Criterion",
    "Question",
    "RequirementSpec",
    # Architecture models
    "ChangeType",
    "RiskLevel",
    "RiskCategory",
    "ModuleSpec",
    "ModuleChange",
    "DataFlowNode",
    "DataFlowEdge",
    "DataFlowDiagram",
    "SchemaChange",
    "AsyncSpec",
    "Risk",
    "ArchitecturePlan",
    # Graph models
    "NodeType",
    "Complexity",
    "EdgeType",
    "Node",
    "Edge",
    "CycleInfo",
    "DependencyGraph",
    "Level",
    "ChordTask",
    "ChainTask",
    "BuildPlan",
    "TestLevel",
    # Generation models
    "GenerationStatus",
    "CriticPassResult",
    "CriticPassType",
    "GenerationJob",
    "SyntaxErrorDetail",
    "ContractViolationDetail",
    "CriticResult",
    "LevelCriticResult",
    "RepairAttempt",
    "HaltReport",
    "GenerationRun",
    # Repair models
    "RepairStatus",
    "RepairTrigger",
    "RepairScope",
    "RepairContext",
    "RepairInstruction",
    "RepairResult",
    "MicroRepairConfig",
    "ProductionRegressionSignal",
    "SelfRepairSession",
    # Test models
    "TestType",
    "TestStatus",
    "TestResult",
    "TestSpec",
    "GeneratedTest",
    "TestExecutionResult",
    "TestSuiteResult",
    "CoverageReport",
    "TestPlan",
    "TestLevelModel",
    "TestCriticResult",
    # Deploy models
    "DeployStatus",
    "DeployEnvironment",
    "DeployStrategy",
    "HealthStatus",
    "PRStatus",
    "PullRequest",
    "Deployment",
    "DeploymentMetrics",
    "RollbackInfo",
    "SmokeTest",
    "DeployApproval",
    # Tenant models
    "TenantStatus",
    "SubscriptionTier",
    "RepoPlatform",
    "ConnectionStatus",
    "Tenant",
    "User",
    "Repo",
    "SourceProfile",
    "Subscription",
    "AuditLog",
]
