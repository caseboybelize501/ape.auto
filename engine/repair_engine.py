"""
APE - Autonomous Production Engineer
Repair Engine

Micro-repair loop for fixing critic failures:
- Targets single files
- Maximum 3 attempts per file
- HALT on 3rd failure with report
"""

from datetime import datetime
from typing import Optional

from contracts.models.generation import (
    CriticResult,
    RepairAttempt,
    HaltReport,
    CriticPassType,
)
from contracts.models.repair import RepairContext, RepairResult, MicroRepairConfig

from engine.llm_client import LLMClient


class RepairEngine:
    """
    Micro-repair engine for fixing critic failures.
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        config: Optional[MicroRepairConfig] = None
    ):
        """
        Initialize repair engine.
        
        Args:
            llm_client: LLM client for repairs
            config: Repair configuration
        """
        self.llm = llm_client or LLMClient()
        self.config = config or MicroRepairConfig()
    
    def attempt_repair(
        self,
        file_path: str,
        content: str,
        critic_result: CriticResult,
        contract: Optional[str],
        fr_refs: list[str],
        prior_attempts: list[dict],
        attempt_number: int
    ) -> RepairResult:
        """
        Attempt to repair a failing file.
        
        Args:
            file_path: File path
            content: Current content
            critic_result: Critic result with failures
            contract: Relevant contract
            fr_refs: Functional requirements
            prior_attempts: Previous repair attempts
            attempt_number: Current attempt number
        
        Returns:
            RepairResult
        """
        repair_id = f"repair-{file_path.replace('/', '-')}-{attempt_number}"
        
        # Build repair context
        repair_context = RepairContext(
            repair_id=repair_id,
            file_path=file_path,
            current_content=content,
            language="python",
            failing_passes=[p.value for p in critic_result.get_failing_passes()],
            error_details=self._extract_error_details(critic_result),
            contract=contract,
            fr_refs=fr_refs,
            prior_attempts=prior_attempts,
        )
        
        # Build repair prompt
        prompt = self._build_repair_prompt(repair_context)
        
        # Generate repair
        try:
            repaired_content = self.llm.generate_code(
                prompt,
                language="python",
                contracts=[contract] if contract else []
            )
            
            # Create repair result
            result = RepairResult(
                repair_id=repair_id,
                attempt_number=attempt_number,
                original_content=content,
                repair_context=repair_context,
                repaired_content=repaired_content,
                changes_summary=self._summarize_changes(content, repaired_content),
                created_at=datetime.utcnow(),
            )
            
            return result
            
        except Exception as e:
            return RepairResult(
                repair_id=repair_id,
                attempt_number=attempt_number,
                original_content=content,
                repair_context=repair_context,
                repaired_content=None,
                failure_reason=str(e),
                created_at=datetime.utcnow(),
            )
    
    def _build_repair_prompt(self, context: RepairContext) -> str:
        """Build repair prompt for LLM."""
        parts = []
        
        # Header
        parts.append(f"""You are repairing code that failed critic validation.

File: {context.file_path}
Attempt: {context.attempt_number if hasattr(context, 'attempt_number') else 1} of {self.config.max_attempts}

IMPORTANT RULES:
1. Fix ONLY the failing issues - do not modify working code
2. NEVER modify function signatures or return types
3. NEVER modify imports beyond what's needed for the fix
4. Contracts are IMMUTABLE - fix the implementation, not the spec
5. Return the COMPLETE corrected file, not just the changes
""")
        
        # Failing passes
        parts.append(f"""
## Failing Critic Passes

{context.failing_passes}
""")
        
        # Error details
        if context.error_details:
            parts.append("## Error Details\n")
            for pass_type, details in context.error_details.items():
                parts.append(f"### {pass_type}")
                if isinstance(details, list):
                    for d in details:
                        parts.append(f"- {d}")
                else:
                    parts.append(f"{details}")
            parts.append("")
        
        # Prior attempts
        if context.prior_attempts:
            parts.append("## Prior Failed Attempts\n")
            for i, attempt in enumerate(context.prior_attempts[-2:], 1):  # Last 2 attempts
                parts.append(f"Attempt {i} failed because: {attempt.get('failure_reason', 'unknown')}")
            parts.append("")
        
        # Contract
        if context.contract:
            parts.append(f"""## Contract (IMMUTABLE - must adhere to this)

{context.contract[:2000]}  # Truncate if too long
""")
        
        # Current content
        parts.append(f"""## Current Code (needs repair)

```python
{context.current_content}
```
""")
        
        # Final instruction
        parts.append("""## Task

Fix the failing critic passes while:
- Preserving all working functionality
- Keeping function signatures unchanged
- Adhering to the contract exactly
- Following codebase patterns

Return ONLY the complete corrected code, no explanations.
""")
        
        return "\n".join(parts)
    
    def _extract_error_details(self, critic_result: CriticResult) -> dict:
        """Extract error details from critic result."""
        details = {}
        
        if critic_result.pass1_result.value == "fail":
            details["syntax_errors"] = [
                f"Line {e.line}: {e.message}"
                for e in critic_result.pass1_errors
            ]
        
        if critic_result.pass2_result.value == "fail":
            details["contract_violations"] = [
                f"{v.violation_type}: expected {v.expected}, got {v.actual}"
                for v in critic_result.pass2_violations
            ]
        
        if critic_result.pass3_result.value == "fail":
            details["completeness"] = {
                "score": critic_result.pass3_score,
                "reasoning": critic_result.pass3_reasoning,
            }
        
        if critic_result.pass4_result.value == "fail":
            details["logic_errors"] = critic_result.pass4_errors
        
        return details
    
    def _summarize_changes(
        self,
        original: str,
        repaired: str
    ) -> str:
        """Summarize changes between original and repaired."""
        # Simple diff summary
        original_lines = set(original.split("\n"))
        repaired_lines = set(repaired.split("\n"))
        
        added = len(repaired_lines - original_lines)
        removed = len(original_lines - repaired_lines)
        
        return f"Added {added} lines, removed {removed} lines"
    
    def create_halt_report(
        self,
        run_id: str,
        level: int,
        file_path: str,
        critic_result: CriticResult,
        attempts: list[RepairResult]
    ) -> HaltReport:
        """
        Create halt report after max repair attempts.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_path: Failing file path
            critic_result: Original critic result
            attempts: All repair attempts
        
        Returns:
            HaltReport for GATE-4
        """
        # Generate recommended action using LLM
        recommended_action = self._generate_recommendation(
            file_path, critic_result, attempts
        )
        
        return HaltReport(
            id=f"halt-{run_id}-level{level}-{file_path.replace('/', '-')}",
            run_id=run_id,
            level=level,
            file_path=file_path,
            failing_passes=critic_result.get_failing_passes(),
            attempts=[
                {
                    "attempt_number": a.attempt_number,
                    "failure_reason": a.failure_reason or "Post-repair critic failed",
                    "changes_summary": a.changes_summary,
                }
                for a in attempts
            ],
            recommended_action=recommended_action,
            created_at=datetime.utcnow(),
        )
    
    def _generate_recommendation(
        self,
        file_path: str,
        critic_result: CriticResult,
        attempts: list[RepairResult]
    ) -> str:
        """Generate recommended action for human."""
        prompt = f"""Analyze this repair failure and recommend action.

File: {file_path}

Failing passes: {[p.value for p in critic_result.get_failing_passes()]}

Repair attempts: {len(attempts)}

Error details:
{self._extract_error_details(critic_result)}

Based on the persistent failures, recommend one of:
1. "modify_architecture" - The architecture plan needs changes
2. "modify_requirement" - The requirement is unclear or impossible
3. "manual_fix" - A human should manually fix this file
4. "skip_file" - Skip this file and continue (if non-critical)

Return JSON:
{{
    "recommended_action": "one of the above",
    "reasoning": "Why this action is recommended",
    "alternative_approaches": ["Other options to consider"]
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {
            "recommended_action": "manual_fix",
            "reasoning": "Unable to determine best action",
            "alternative_approaches": []
        })
        
        return result.get("reasoning", "Manual intervention required")
    
    def should_halt(
        self,
        attempt_number: int,
        success: bool
    ) -> bool:
        """
        Determine if repair loop should halt.
        
        Args:
            attempt_number: Current attempt number
            success: Whether repair was successful
        
        Returns:
            True if should halt
        """
        if success:
            return False
        
        return attempt_number >= self.config.max_attempts
