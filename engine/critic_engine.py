"""
APE - Autonomous Production Engineer
Critic Engine

4-pass critic validation for generated code:
- Pass 1: Syntax validation (deterministic)
- Pass 2: Contract compliance (deterministic)
- Pass 3: Completeness check (LLM-judged)
- Pass 4: Logic correctness (LLM-judged)

No level advances until all files pass all 4 passes.
"""

import time
from datetime import datetime
from typing import Optional
import ast

from contracts.models.generation import (
    CriticResult,
    LevelCriticResult,
    CriticPassResult,
    SyntaxErrorDetail,
    ContractViolationDetail,
)

from engine.critic_pass1 import SyntaxCritic
from engine.critic_pass2 import ContractCritic
from engine.critic_pass3 import CompletenessCritic
from engine.critic_pass4 import LogicCritic
from engine.llm_client import LLMClient


class CriticEngine:
    """
    4-pass critic engine for code validation.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize critic engine.
        
        Args:
            llm_client: LLM client for LLM-judged passes
        """
        self.llm = llm_client or LLMClient()
        self.syntax_critic = SyntaxCritic()
        self.contract_critic = ContractCritic()
        self.completeness_critic = CompletenessCritic(self.llm)
        self.logic_critic = LogicCritic(self.llm)
    
    def critique_file(
        self,
        file_path: str,
        content: str,
        level: int,
        contracts: list[str],
        fr_refs: list[str]
    ) -> CriticResult:
        """
        Run all 4 critic passes on a single file.
        
        Args:
            file_path: File path
            content: File content
            level: Topological level
            contracts: Contract files
            fr_refs: Functional requirements
        
        Returns:
            CriticResult with all pass results
        """
        result = CriticResult(
            job_id="",  # Will be set by caller
            file_path=file_path,
            level=level,
        )
        
        total_start = time.time()
        
        # Pass 1: Syntax
        pass1_start = time.time()
        passed1, errors1 = self.syntax_critic.check(file_path, content)
        result.pass1_duration_ms = int((time.time() - pass1_start) * 1000)
        
        if passed1:
            result.pass1_result = CriticPassResult.PASS
        else:
            result.pass1_result = CriticPassResult.FAIL
            result.pass1_errors = [
                SyntaxErrorDetail(
                    line=e.get("line", 0),
                    column=e.get("column", 0),
                    message=e.get("message", ""),
                    error_type=e.get("type", "syntax"),
                )
                for e in errors1
            ]
        
        # Pass 2: Contract
        pass2_start = time.time()
        passed2, violations2 = self.contract_critic.check(file_path, content, contracts)
        result.pass2_duration_ms = int((time.time() - pass2_start) * 1000)
        
        if passed2:
            result.pass2_result = CriticPassResult.PASS
        else:
            result.pass2_result = CriticPassResult.FAIL
            result.pass2_violations = [
                ContractViolationDetail(
                    contract_file=v.get("contract_file", ""),
                    violation_type=v.get("type", "mismatch"),
                    expected=v.get("expected", ""),
                    actual=v.get("actual", ""),
                    line=v.get("line"),
                )
                for v in violations2
            ]
        
        # Pass 3: Completeness
        pass3_start = time.time()
        passed3, score3, reasoning3 = self.completeness_critic.check(
            content, fr_refs
        )
        result.pass3_duration_ms = int((time.time() - pass3_start) * 1000)
        
        if passed3:
            result.pass3_result = CriticPassResult.PASS
        else:
            result.pass3_result = CriticPassResult.FAIL
        result.pass3_score = score3
        result.pass3_reasoning = reasoning3
        
        # Pass 4: Logic
        pass4_start = time.time()
        passed4, score4, reasoning4, errors4 = self.logic_critic.check(
            content, fr_refs, contracts
        )
        result.pass4_duration_ms = int((time.time() - pass4_start) * 1000)
        
        if passed4:
            result.pass4_result = CriticPassResult.PASS
        else:
            result.pass4_result = CriticPassResult.FAIL
        result.pass4_score = score4
        result.pass4_reasoning = reasoning4
        result.pass4_errors = errors4
        
        # Overall result
        result.duration_ms = int((time.time() - total_start) * 1000)
        
        if result.all_passes_passed():
            result.overall_result = CriticPassResult.PASS
        elif result.pass1_result == CriticPassResult.FAIL or \
             result.pass2_result == CriticPassResult.FAIL:
            result.overall_result = CriticPassResult.FAIL
        else:
            result.overall_result = CriticPassResult.FAIL
        
        return result
    
    def critique_level(
        self,
        run_id: str,
        level: int,
        files: list[tuple[str, str]],
        contracts: list[str],
        fr_refs_map: dict[str, list[str]]
    ) -> LevelCriticResult:
        """
        Run critic on all files in a level.
        
        Args:
            run_id: Generation run ID
            level: Level number
            files: List of (file_path, content) tuples
            contracts: Contract files
            fr_refs_map: Map of file_path -> fr_refs
        
        Returns:
            LevelCriticResult with aggregated results
        """
        level_result = LevelCriticResult(
            run_id=run_id,
            level=level,
            total_files=len(files),
        )
        
        total_start = time.time()
        
        for file_path, content in files:
            file_result = self.critique_file(
                file_path=file_path,
                content=content,
                level=level,
                contracts=contracts,
                fr_refs=fr_refs_map.get(file_path, []),
            )
            file_result.job_id = f"{run_id}-{file_path.replace('/', '-')}"
            
            level_result.file_results.append(file_result)
            
            if file_result.all_passes_passed():
                level_result.passed_files += 1
            else:
                level_result.failed_files += 1
        
        # Determine level result
        if level_result.failed_files == 0:
            level_result.level_result = "pass"
        else:
            level_result.level_result = "fail"
        
        level_result.completed_at = datetime.utcnow()
        level_result.duration_ms = int((time.time() - total_start) * 1000)
        
        return level_result
    
    def get_failing_files(self, level_result: LevelCriticResult) -> list[str]:
        """
        Get list of files that failed any pass.
        
        Args:
            level_result: Level critic result
        
        Returns:
            List of failing file paths
        """
        return [
            r.file_path for r in level_result.file_results
            if not r.all_passes_passed()
        ]
    
    def get_repair_context(
        self,
        file_result: CriticResult
    ) -> dict:
        """
        Build repair context for a failing file.
        
        Args:
            file_result: Critic result for failing file
        
        Returns:
            Repair context dict
        """
        failing_passes = file_result.get_failing_passes()
        
        error_details = {}
        
        if "syntax" in failing_passes:
            error_details["syntax_errors"] = [
                {"line": e.line, "message": e.message}
                for e in file_result.pass1_errors
            ]
        
        if "contract" in failing_passes:
            error_details["contract_violations"] = [
                {
                    "type": v.violation_type,
                    "expected": v.expected,
                    "actual": v.actual,
                }
                for v in file_result.pass2_violations
            ]
        
        if "completeness" in failing_passes:
            error_details["completeness"] = {
                "score": file_result.pass3_score,
                "reasoning": file_result.pass3_reasoning,
            }
        
        if "logic" in failing_passes:
            error_details["logic"] = {
                "score": file_result.pass4_score,
                "reasoning": file_result.pass4_reasoning,
                "errors": file_result.pass4_errors,
            }
        
        return {
            "file_path": file_result.file_path,
            "failing_passes": [p.value for p in failing_passes],
            "error_details": error_details,
        }


# Celery task wrapper
def critic_level_task(
    run_id: str,
    level: int,
    files: list[tuple[str, str]],
    contracts: list[str],
    fr_refs_map: dict[str, list[str]]
) -> dict:
    """
    Celery task for level critic.
    
    This is the callback after all files in a level are generated.
    """
    engine = CriticEngine()
    result = engine.critique_level(
        run_id=run_id,
        level=level,
        files=files,
        contracts=contracts,
        fr_refs_map=fr_refs_map,
    )
    
    return {
        "success": result.level_result == "pass",
        "level_result": result.dict(),
        "failing_files": engine.get_failing_files(result),
    }
