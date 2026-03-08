"""
APE - Autonomous Production Engineer
Build Orchestrator

Creates Celery chord/chain execution plan from BuildPlan:
- Parallel generation within levels
- Sequential progression between levels
- Critic callback after each level
- Test execution after generation
"""

from datetime import datetime
from typing import Optional

from contracts.models.graph import BuildPlan, Level
from contracts.models.generation import GenerationRun, GenerationStatus


class BuildOrchestrator:
    """
    Orchestrates build execution using Celery.
    """
    
    def __init__(self):
        """Initialize build orchestrator."""
        pass
    
    def create_execution_plan(self, build_plan: BuildPlan) -> dict:
        """
        Create Celery execution plan from BuildPlan.
        
        Args:
            build_plan: Build plan from topo sort
        
        Returns:
            Celery execution plan dict
        """
        # Build chain of chords
        # Each level: chord(group(generate_files), critic_callback)
        # Chain: level_0 -> level_1 -> ... -> tests -> deploy
        
        chain_tasks = []
        
        # Generation levels
        for level in build_plan.levels:
            chain_tasks.append({
                "type": "chord",
                "level": level.level,
                "group": {
                    "task": "engine.gen_worker.generate_file",
                    "args": [[{"file_path": f, "level": level.level} for f in level.files]]
                },
                "callback": {
                    "task": "engine.critic_engine.critic_level",
                    "args": [level.level]
                }
            })
        
        # Test generation
        chain_tasks.append({
            "type": "chord",
            "stage": "test_generation",
            "group": {
                "task": "engine.test_generator.generate_tests",
                "args": [build_plan.test_plan]
            },
            "callback": {
                "task": "engine.test_generator.test_critic",
                "args": []
            }
        })
        
        # Test execution
        chain_tasks.append({
            "type": "task",
            "stage": "test_execution",
            "task": "engine.test_runner.run_tests",
            "args": [build_plan.test_plan]
        })
        
        # PR creation
        chain_tasks.append({
            "type": "task",
            "stage": "pr_creation",
            "task": "engine.deploy_manager.create_pr",
            "args": []
        })
        
        return {
            "chain": chain_tasks,
            "build_plan_id": build_plan.id,
            "total_tasks": sum(
                len(level.files) for level in build_plan.levels
            ) + len(build_plan.levels) + 3,  # +3 for test gen, test run, PR
            "estimated_parallelism": max(
                len(level.files) for level in build_plan.levels
            ) if build_plan.levels else 0,
        }
    
    def start_generation_run(
        self,
        build_plan: BuildPlan,
        requirement_spec_id: str,
        architecture_plan_id: str,
        repo_id: str
    ) -> GenerationRun:
        """
        Start generation run.
        
        Args:
            build_plan: Build plan
            requirement_spec_id: Requirement spec ID
            architecture_plan_id: Architecture plan ID
            repo_id: Repository ID
        
        Returns:
            GenerationRun record
        """
        # Create dedup key
        dedup_key = f"{repo_id}:{requirement_spec_id}:{build_plan.id}"
        
        return GenerationRun(
            id=f"run-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            requirement_spec_id=requirement_spec_id,
            architecture_plan_id=architecture_plan_id,
            build_plan_id=build_plan.id,
            repo_id=repo_id,
            dedup_key=dedup_key,
            status=GenerationStatus.PENDING,
            current_level=0,
            total_levels=len(build_plan.levels),
            created_at=datetime.utcnow(),
        )
    
    def advance_level(
        self,
        run: GenerationRun,
        level_result: dict
    ) -> tuple[bool, Optional[int]]:
        """
        Advance to next level after current level completes.
        
        Args:
            run: Current generation run
            level_result: Result of current level critic
        
        Returns:
            Tuple of (can_advance, next_level_number)
        """
        if level_result.get("level_result") != "pass":
            # Level failed
            if level_result.get("level_result") == "halt":
                run.status = GenerationStatus.BLOCKED
            else:
                run.status = GenerationStatus.FAILED
            return False, None
        
        # Advance to next level
        run.current_level += 1
        
        if run.current_level >= run.total_levels:
            # All levels complete
            run.status = GenerationStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            return False, None
        
        return True, run.current_level
    
    def get_progress(self, run: GenerationRun) -> dict:
        """
        Get generation progress.
        
        Args:
            run: Generation run
        
        Returns:
            Progress dict
        """
        completed_levels = sum(
            1 for lr in run.level_results
            if lr.level_result == "pass"
        )
        
        return {
            "run_id": run.id,
            "status": run.status.value,
            "current_level": run.current_level,
            "total_levels": run.total_levels,
            "completed_levels": completed_levels,
            "progress_percent": (completed_levels / run.total_levels * 100) if run.total_levels > 0 else 0,
            "files_generated": run.total_files_generated,
            "files_passed": run.total_files_passed,
            "repairs": run.total_repairs,
            "halts": run.total_halts,
        }
    
    def create_celery_signature(self, build_plan: BuildPlan) -> str:
        """
        Create Celery signature string for execution.
        
        Args:
            build_plan: Build plan
        
        Returns:
            Celery signature (for documentation/logging)
        """
        signatures = []
        
        for level in build_plan.levels:
            files = level.files
            sig = f"chord(group([generate_file('{f}') for f in {files}]) -> critic_level({level.level}))"
            signatures.append(sig)
        
        signatures.append("chord(group([generate_tests()]) -> test_critic())")
        signatures.append("run_tests()")
        signatures.append("create_pr()")
        
        return " -> ".join(signatures)
