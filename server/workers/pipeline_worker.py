"""
APE - Autonomous Production Engineer
Pipeline Worker

Celery tasks for the main generation pipeline:
- File generation
- Critic validation
- Repair loop
- Test generation
"""

from celery import group, chord, chain
from datetime import datetime

from server.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def generate_file(
    self,
    run_id: str,
    file_path: str,
    level: int,
    node_spec: dict,
    contracts: list,
    fr_refs: list,
    codebase_patterns: dict,
    dependency_outputs: dict
):
    """
    Generate a single file using LLM.
    
    This is a Celery task that runs in parallel with other
    files at the same topological level.
    """
    from engine.gen_worker import GenerationWorker
    
    worker = GenerationWorker()
    
    try:
        result = worker.generate(
            run_id=run_id,
            file_path=file_path,
            level=level,
            node_spec=node_spec,
            contracts=contracts,
            fr_refs=fr_refs,
            codebase_patterns=codebase_patterns,
            dependency_outputs=dependency_outputs,
        )
        
        return {
            "success": True,
            "file_path": file_path,
            "content": result.get("content"),
            "job": result.get("job"),
        }
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def critic_level(
    run_id: str,
    level: int,
    generation_results: list,
    contracts: list,
    fr_refs_map: dict
):
    """
    Run 4-pass critic on all files in a level.
    
    This is the callback after all files in a level are generated.
    No level advances until all files pass all 4 passes.
    """
    from engine.critic_engine import CriticEngine
    
    engine = CriticEngine()
    
    # Extract file contents from generation results
    files = []
    for result in generation_results:
        if result.get("success") and result.get("content"):
            files.append((result["file_path"], result["content"]))
    
    # Run critic
    level_result = engine.critique_level(
        run_id=run_id,
        level=level,
        files=files,
        contracts=contracts,
        fr_refs_map=fr_refs_map,
    )
    
    return {
        "success": level_result.level_result == "pass",
        "level_result": level_result.dict(),
        "failing_files": engine.get_failing_files(level_result),
    }


@celery_app.task(bind=True, max_retries=3)
def repair_file(
    self,
    run_id: str,
    file_path: str,
    content: str,
    critic_result: dict,
    contract: str,
    fr_refs: list,
    attempt_number: int
):
    """
    Attempt to repair a failing file.
    
    Maximum 3 attempts per file before HALT.
    """
    from engine.repair_engine import RepairEngine
    from contracts.models.generation import CriticResult
    
    engine = RepairEngine()
    
    # Convert critic_result dict to CriticResult
    # (simplified - would need full deserialization)
    
    try:
        result = engine.attempt_repair(
            file_path=file_path,
            content=content,
            critic_result=None,  # Would be proper CriticResult
            contract=contract,
            fr_refs=fr_refs,
            prior_attempts=[],
            attempt_number=attempt_number,
        )
        
        return {
            "success": result.repaired_content is not None,
            "content": result.repaired_content,
            "changes_summary": result.changes_summary,
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def generate_tests(
    run_id: str,
    requirement_spec: dict,
    code_files: list,
    contracts: list,
    existing_coverage: dict
):
    """
    Generate all test types for generated code.
    """
    from engine.test_generator import TestGenerator
    
    generator = TestGenerator()
    
    # Convert requirement_spec dict to object
    from contracts.models.requirement import RequirementSpec
    spec = RequirementSpec(**requirement_spec)
    
    # Generate tests
    test_plan = generator.generate_all(
        requirement_spec=spec,
        code_files=code_files,
        contracts=contracts,
        existing_coverage=existing_coverage,
    )
    
    # Generate actual test code
    generated_tests = []
    for test_spec in (
        test_plan.contract_tests +
        test_plan.acceptance_tests +
        test_plan.regression_tests
    ):
        generated_test = generator.generate_test_code(test_spec)
        generated_tests.append({
            "spec": test_spec.dict(),
            "test": generated_test.dict(),
        })
    
    return {
        "success": True,
        "test_plan": test_plan.dict(),
        "generated_tests": generated_tests,
    }


@celery_app.task
def run_tests(
    run_id: str,
    test_plan: dict,
    repo_path: str
):
    """
    Execute all tests in topological order.
    """
    from engine.test_runner import TestRunner
    
    runner = TestRunner(repo_path=repo_path)
    
    # Convert test_plan dict to object
    from contracts.models.test import TestPlan
    plan = TestPlan(**test_plan)
    
    # Run tests
    results = runner.run_all(plan)
    
    # Check for failures
    all_passed = all(r.success for r in results)
    
    return {
        "success": all_passed,
        "results": [r.dict() for r in results],
        "regression_detected": not all_passed,
    }


@celery_app.task
def create_pr(
    run_id: str,
    repo_id: str,
    branch_name: str,
    title: str,
    description: str,
    files_changed: list
):
    """
    Create pull request for human review.
    """
    from engine.deploy_manager import DeployManager
    from connectors.github import GitHubConnector
    
    repo_connector = GitHubConnector(token="mock-token")
    deploy_manager = DeployManager(repo_connector=repo_connector)
    
    pr = deploy_manager.create_pr(
        run_id=run_id,
        repo_id=repo_id,
        branch_name=branch_name,
        title=title,
        description=description,
        files_changed=files_changed,
    )
    
    # Store PR
    from server.api.prs import _prs_store
    _prs_store[pr.id] = pr.dict()
    
    return {
        "success": True,
        "pr": pr.dict(),
        "pr_url": pr.pr_url,
    }


@celery_app.task
def execute_pipeline(
    requirement_spec_id: str,
    build_plan: dict
):
    """
    Execute complete generation pipeline.
    
    This orchestrates the full chain of:
    1. Generate files level by level
    2. Critic validation per level
    3. Repair loop for failures
    4. Test generation
    5. Test execution
    6. PR creation
    """
    from contracts.models.graph import BuildPlan
    
    plan = BuildPlan(**build_plan)
    
    # Build Celery chain
    # This is a simplified version - full implementation would
    # dynamically build the chain based on build_plan
    
    pipeline_chain = []
    
    for level in plan.levels:
        # Generate all files in level (parallel)
        generate_group = group(
            generate_file.s(
                run_id=f"run-{requirement_spec_id}",
                file_path=f,
                level=level.level,
                node_spec={},
                contracts=[],
                fr_refs=[],
                codebase_patterns={},
                dependency_outputs={},
            )
            for f in level.files
        )
        
        # Critic after all files generated
        critic_callback = critic_level.s(
            level=level.level,
            contracts=[],
            fr_refs_map={},
        )
        
        pipeline_chain.append(chord(generate_group)(critic_callback))
    
    # Add test generation and execution
    pipeline_chain.append(
        generate_tests.s(
            requirement_spec_id=requirement_spec_id,
            code_files=[],
            contracts=[],
            existing_coverage={},
        )
    )
    
    pipeline_chain.append(
        run_tests.s(
            repo_path="/tmp/repo",
        )
    )
    
    pipeline_chain.append(
        create_pr.s(
            repo_id="mock/repo",
            branch_name=f"ape/{requirement_spec_id}",
            title=f"APE: Implementation for {requirement_spec_id}",
            description="Auto-generated by APE",
            files_changed=[],
        )
    )
    
    # Execute chain
    result = chain(*pipeline_chain)()
    
    return {
        "success": True,
        "chain_id": result.id,
        "status": "pipeline_started",
    }
