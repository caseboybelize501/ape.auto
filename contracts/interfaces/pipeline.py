"""
APE - Autonomous Production Engineer
Contract: Pipeline Interfaces

Immutable interface definitions for all cross-module function signatures.
These are the ground truth contracts that critic Pass 2 validates against.
"""

from typing import Optional, Any
from contracts.models.requirement import RequirementSpec
from contracts.models.architecture import ArchitecturePlan
from contracts.models.graph import DependencyGraph, BuildPlan
from contracts.models.generation import GenerationRun, LevelCriticResult
from contracts.models.test import TestPlan, TestSuiteResult
from contracts.models.deploy import PullRequest, Deployment


# ===========================================
# CODEBASE GRAPH MODULE
# ===========================================

def build_codebase_graph(
    repo_id: str,
    repo_path: str,
    branch: str = "main"
) -> DependencyGraph:
    """
    Scan repository and build complete codebase graph.
    
    Args:
        repo_id: Repository identifier
        repo_path: Local path to repository
        branch: Branch to scan
    
    Returns:
        Complete DependencyGraph with all modules, imports, call graph
    """
    ...


def update_codebase_graph(
    graph_id: str,
    incremental_changes: dict
) -> DependencyGraph:
    """
    Update existing graph with incremental changes.
    
    Args:
        graph_id: Existing graph ID
        incremental_changes: Dict of added/modified/removed files
    
    Returns:
        Updated DependencyGraph
    """
    ...


def get_module_coverage(
    graph: DependencyGraph,
    module_path: str
) -> float:
    """
    Get test coverage percentage for a module.
    
    Args:
        graph: Codebase graph
        module_path: Path to module
    
    Returns:
        Coverage percentage (0-100)
    """
    ...


# ===========================================
# REQUIREMENTS EXTRACTION MODULE
# ===========================================

def extract_requirements(
    raw_text: str,
    repo_id: str,
    codebase_graph: DependencyGraph,
    source: str = "manual",
    source_id: Optional[str] = None
) -> RequirementSpec:
    """
    Extract structured requirements from raw text.
    
    Args:
        raw_text: Raw requirement text (ticket, PRD, voice)
        repo_id: Target repository ID
        codebase_graph: Current codebase graph
        source: Source type (ticket, PRD, voice, manual)
        source_id: Original ticket/PRD ID if applicable
    
    Returns:
        Complete RequirementSpec with FRs, NFRs, acceptance criteria
    """
    ...


def resolve_ambiguity(
    spec_id: str,
    question_id: str,
    answer: str,
    resolved_by: str
) -> RequirementSpec:
    """
    Resolve an ambiguity in a requirement spec.
    
    Args:
        spec_id: Requirement spec ID
        question_id: Question ID to resolve
        answer: Human-provided answer
        resolved_by: User who resolved
    
    Returns:
        Updated RequirementSpec
    """
    ...


def validate_requirement_completeness(
    spec: RequirementSpec
) -> tuple[bool, list[str]]:
    """
    Validate that requirement has no unresolved ambiguities.
    
    Args:
        spec: Requirement spec to validate
    
    Returns:
        Tuple of (is_complete, list of blocking issues)
    """
    ...


# ===========================================
# ARCHITECTURE PLANNING MODULE
# ===========================================

def create_architecture_plan(
    requirement_spec: RequirementSpec,
    codebase_graph: DependencyGraph
) -> ArchitecturePlan:
    """
    Generate architecture plan from requirement spec.
    
    Args:
        requirement_spec: Approved requirement spec
        codebase_graph: Current codebase graph
    
    Returns:
        Complete ArchitecturePlan
    """
    ...


def validate_architecture_plan(
    plan: ArchitecturePlan
) -> tuple[bool, list[str]]:
    """
    Validate architecture plan for completeness and consistency.
    
    Args:
        plan: Architecture plan to validate
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    ...


def get_affected_modules(
    plan: ArchitecturePlan
) -> list[str]:
    """
    Get all modules affected by architecture plan.
    
    Args:
        plan: Architecture plan
    
    Returns:
        List of module paths
    """
    ...


# ===========================================
# DEPENDENCY GRAPH MODULE
# ===========================================

def build_dependency_graph(
    architecture_plan: ArchitecturePlan,
    existing_graph: DependencyGraph
) -> DependencyGraph:
    """
    Build merged dependency graph including planned changes.
    
    Args:
        architecture_plan: Approved architecture plan
        existing_graph: Existing codebase graph
    
    Returns:
        Merged DependencyGraph
    """
    ...


def detect_cycles(
    graph: DependencyGraph
) -> tuple[bool, list[dict]]:
    """
    Detect cycles in dependency graph.
    
    Args:
        graph: Dependency graph to check
    
    Returns:
        Tuple of (cycle_free, list of cycle info dicts)
    """
    ...


def suggest_cycle_break(
    cycle_path: list[str]
) -> str:
    """
    Suggest where to break a cycle.
    
    Args:
        cycle_path: List of nodes in cycle
    
    Returns:
        Suggested break point with explanation
    """
    ...


# ===========================================
# TOPOLOGICAL SORT MODULE
# ===========================================

def topological_sort(
    graph: DependencyGraph
) -> BuildPlan:
    """
    Perform topological sort using Kahn's algorithm.
    
    Args:
        graph: Cycle-free dependency graph
    
    Returns:
        BuildPlan with levels for parallel generation
    """
    ...


def compute_critical_path(
    graph: DependencyGraph
) -> list[str]:
    """
    Compute critical path through dependency graph.
    
    Args:
        graph: Dependency graph
    
    Returns:
        List of nodes on critical path
    """
    ...


def estimate_level_duration(
    level_files: list[str],
    complexity_scores: dict
) -> int:
    """
    Estimate duration for a generation level.
    
    Args:
        level_files: Files in level
        complexity_scores: Complexity per file
    
    Returns:
        Estimated duration in seconds
    """
    ...


# ===========================================
# BUILD ORCHESTRATION MODULE
# ===========================================

def create_celery_chord_plan(
    build_plan: BuildPlan
) -> list[dict]:
    """
    Create Celery chord/chain execution plan.
    
    Args:
        build_plan: Build plan from topo sort
    
    Returns:
        List of chord task specifications
    """
    ...


def orchestrate_level_generation(
    run_id: str,
    level: int,
    files: list[str]
) -> dict:
    """
    Orchestrate parallel generation for a level.
    
    Args:
        run_id: Generation run ID
        level: Level number
        files: Files to generate
    
    Returns:
        Generation status dict
    """
    ...


def advance_to_next_level(
    run_id: str,
    current_level_result: LevelCriticResult
) -> Optional[int]:
    """
    Advance generation to next level if current passed.
    
    Args:
        run_id: Generation run ID
        current_level_result: Result of current level
    
    Returns:
        Next level number or None if blocked
    """
    ...


# ===========================================
# CODE GENERATION MODULE
# ===========================================

def generate_file(
    run_id: str,
    file_path: str,
    node_spec: dict,
    contracts: list[str],
    fr_refs: list[str],
    codebase_patterns: dict,
    dependency_outputs: dict
) -> str:
    """
    Generate complete file content using LLM.
    
    Args:
        run_id: Generation run ID
        file_path: Target file path
        node_spec: Node specification
        contracts: Relevant contract files
        fr_refs: Functional requirements to satisfy
        codebase_patterns: Patterns from codebase
        dependency_outputs: Outputs from dependencies
    
    Returns:
        Complete file content
    """
    ...


def validate_generated_content(
    content: str,
    language: str
) -> tuple[bool, Optional[str]]:
    """
    Validate generated content has no placeholders.
    
    Args:
        content: Generated content
        language: File language
    
    Returns:
        Tuple of (is_valid, error message if invalid)
    """
    ...


# ===========================================
# CRITIC ENGINE MODULE
# ===========================================

def run_critic_pass1_syntax(
    file_path: str,
    content: str,
    language: str
) -> tuple[bool, list[dict]]:
    """
    Pass 1: Syntax validation.
    
    Args:
        file_path: File path
        content: File content
        language: File language
    
    Returns:
        Tuple of (passed, list of syntax errors)
    """
    ...


def run_critic_pass2_contract(
    file_path: str,
    content: str,
    contract_files: list[str]
) -> tuple[bool, list[dict]]:
    """
    Pass 2: Contract compliance validation.
    
    Args:
        file_path: File path
        content: File content
        contract_files: Contract files to validate against
    
    Returns:
        Tuple of (passed, list of contract violations)
    """
    ...


def run_critic_pass3_completeness(
    content: str,
    fr_refs: list[str],
    llm_model: str
) -> tuple[bool, str, str]:
    """
    Pass 3: Completeness check using LLM judge.
    
    Args:
        content: File content
        fr_refs: Functional requirements to check against
        llm_model: LLM model to use
    
    Returns:
        Tuple of (passed, score, reasoning)
    """
    ...


def run_critic_pass4_logic(
    content: str,
    fr_refs: list[str],
    contract: str,
    llm_model: str
) -> tuple[bool, str, list[str]]:
    """
    Pass 4: Logic correctness using LLM judge.
    
    Args:
        content: File content
        fr_refs: Functional requirements
        contract: Interface contract
        llm_model: LLM model to use
    
    Returns:
        Tuple of (passed, score, list of errors)
    """
    ...


def run_full_critic_level(
    run_id: str,
    level: int,
    files: list[tuple[str, str]]
) -> LevelCriticResult:
    """
    Run 4-pass critic on all files in a level.
    
    Args:
        run_id: Generation run ID
        level: Level number
        files: List of (file_path, content) tuples
    
    Returns:
        Aggregated LevelCriticResult
    """
    ...


# ===========================================
# REPAIR ENGINE MODULE
# ===========================================

def attempt_micro_repair(
    file_path: str,
    content: str,
    failing_passes: list[str],
    error_details: dict,
    contract: Optional[str],
    fr_refs: list[str],
    prior_attempts: list[dict],
    attempt_number: int
) -> tuple[str, str]:
    """
    Attempt to repair a failing file.
    
    Args:
        file_path: File path
        content: Current content
        failing_passes: Which critic passes failed
        error_details: Detailed error information
        contract: Relevant contract
        fr_refs: Functional requirements
        prior_attempts: Previous repair attempts
        attempt_number: Current attempt number
    
    Returns:
        Tuple of (repaired_content, changes_summary)
    """
    ...


def create_halt_report(
    run_id: str,
    level: int,
    file_path: str,
    failing_passes: list[str],
    attempts: list[dict]
) -> dict:
    """
    Create halt report after 3 failed repair attempts.
    
    Args:
        run_id: Generation run ID
        level: Blocked level
        file_path: Blocked file path
        failing_passes: Failing critic passes
        attempts: All repair attempts
    
    Returns:
        Halt report dict for GATE-4
    """
    ...


# ===========================================
# TEST GENERATION MODULE
# ===========================================

def generate_contract_tests(
    contract_files: list[str],
    target_modules: list[str]
) -> list[dict]:
    """
    Generate contract tests from contract files.
    
    Args:
        contract_files: Contract file paths
        target_modules: Modules to test
    
    Returns:
        List of test specifications
    """
    ...


def generate_acceptance_tests(
    requirement_spec: RequirementSpec,
    target_modules: list[str]
) -> list[dict]:
    """
    Generate acceptance tests from requirements.
    
    Args:
        requirement_spec: Requirement spec
        target_modules: Modules to test
    
    Returns:
        List of test specifications
    """
    ...


def generate_regression_tests(
    modified_files: list[str],
    existing_coverage: dict
) -> list[dict]:
    """
    Generate regression guard tests.
    
    Args:
        modified_files: Files modified by APE
        existing_coverage: Existing test coverage
    
    Returns:
        List of test specifications
    """
    ...


def run_test_critic(
    test_level: int,
    test_files: list[tuple[str, str]]
) -> dict:
    """
    Run 4-pass critic on generated tests.
    
    Args:
        test_level: Test level number
        test_files: List of (file_path, content) tuples
    
    Returns:
        Test critic result dict
    """
    ...


# ===========================================
# TEST EXECUTION MODULE
# ===========================================

def execute_test_suite(
    test_files: list[str],
    suite_type: str,
    timeout_seconds: int
) -> dict:
    """
    Execute a test suite.
    
    Args:
        test_files: Test files to run
        suite_type: Type: regression, contract, acceptance
        timeout_seconds: Timeout for suite
    
    Returns:
        Test suite result dict
    """
    ...


def run_tests_in_topo_order(
    test_plan: TestPlan
) -> list[dict]:
    """
    Run tests in topological order.
    
    Args:
        test_plan: Test plan
    
    Returns:
        List of test level results
    """
    ...


# ===========================================
# DEPLOYMENT MODULE
# ===========================================

def create_pull_request(
    run_id: str,
    repo_id: str,
    files_changed: list[str],
    architecture_plan: ArchitecturePlan
) -> PullRequest:
    """
    Create pull request for human review.
    
    Args:
        run_id: Generation run ID
        repo_id: Repository ID
        files_changed: Changed file paths
        architecture_plan: Architecture plan for context
    
    Returns:
        Created PullRequest
    """
    ...


def deploy_to_staging(
    pr_id: str,
    environment: str
) -> Deployment:
    """
    Deploy approved PR to staging.
    
    Args:
        pr_id: Pull request ID
        environment: Staging environment name
    
    Returns:
        Deployment record
    """
    ...


def promote_to_production(
    deployment_id: str,
    approved_by: str
) -> Deployment:
    """
    Promote staging deployment to production.
    
    Args:
        deployment_id: Staging deployment ID
        approved_by: User approving
    
    Returns:
        Updated Deployment record
    """
    ...


def trigger_rollback(
    deployment_id: str,
    reason: str
) -> dict:
    """
    Trigger rollback for a deployment.
    
    Args:
        deployment_id: Deployment to roll back
        reason: Reason for rollback
    
    Returns:
        Rollback status dict
    """
    ...


# ===========================================
# PRODUCTION MONITORING MODULE
# ===========================================

def monitor_deployment(
    deployment_id: str,
    window_minutes: int
) -> dict:
    """
    Monitor deployment for regressions.
    
    Args:
        deployment_id: Deployment to monitor
        window_minutes: Monitoring window
    
    Returns:
        Monitoring results dict
    """
    ...


def detect_regression(
    deployment_id: str,
    signals: dict
) -> Optional[dict]:
    """
    Detect production regression from signals.
    
    Args:
        deployment_id: Deployment ID
        signals: Metrics from observability stack
    
    Returns:
        Regression signal dict or None
    """
    ...


def localize_production_error(
    error_traceback: str,
    generated_files: list[str]
) -> tuple[Optional[str], Optional[int]]:
    """
    Localize production error to specific file and line.
    
    Args:
        error_traceback: Production error traceback
        generated_files: Files generated by APE
    
    Returns:
        Tuple of (file_path, line_number) or (None, None)
    """
    ...


def execute_self_repair(
    deployment_id: str,
    localized_file: str,
    error_context: dict
) -> dict:
    """
    Execute self-repair for production regression.
    
    Args:
        deployment_id: Deployment with regression
        localized_file: File causing error
        error_context: Full error context
    
    Returns:
        Self-repair result dict
    """
    ...
