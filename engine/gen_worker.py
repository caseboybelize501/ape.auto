"""
APE - Autonomous Production Engineer
Generation Worker

Celery task for LLM-based code generation:
- Generates complete file content
- Adheres to contracts
- References functional requirements
- Follows codebase patterns
"""

from datetime import datetime
from typing import Optional
import os

from contracts.models.generation import GenerationJob, GenerationStatus
from contracts.interfaces.pipeline import generate_file as generate_file_interface

from engine.llm_client import LLMClient


class GenerationWorker:
    """
    Worker for generating code files using LLM.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize generation worker.
        
        Args:
            llm_client: LLM client for generation
        """
        self.llm = llm_client or LLMClient(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    
    def generate(
        self,
        run_id: str,
        file_path: str,
        level: int,
        node_spec: dict,
        contracts: list[str],
        fr_refs: list[str],
        codebase_patterns: dict,
        dependency_outputs: dict
    ) -> dict:
        """
        Generate a single file.
        
        Args:
            run_id: Generation run ID
            file_path: Target file path
            level: Topological level
            node_spec: Node specification
            contracts: Contract file contents
            fr_refs: Functional requirement references
            codebase_patterns: Patterns from codebase
            dependency_outputs: Outputs from dependencies
        
        Returns:
            Generation result dict
        """
        job = GenerationJob(
            id=f"job-{file_path.replace('/', '-')}-{datetime.utcnow().strftime('%H%M%S')}",
            run_id=run_id,
            level=level,
            file_path=file_path,
            file_type=self._determine_file_type(file_path),
            language="python",
            node_spec=node_spec,
            relevant_contracts=[],
            fr_refs=fr_refs,
            codebase_patterns=codebase_patterns,
            dependency_outputs=dependency_outputs,
            status=GenerationStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        
        try:
            # Build generation prompt
            prompt = self._build_generation_prompt(
                file_path, node_spec, contracts, fr_refs,
                codebase_patterns, dependency_outputs
            )
            
            # Generate code
            content = self.llm.generate_code(
                prompt,
                language="python",
                contracts=contracts
            )
            
            # Validate generated content
            is_valid, error = self._validate_content(content, job.language)
            if not is_valid:
                job.status = GenerationStatus.FAILED
                job.error_message = error
                job.completed_at = datetime.utcnow()
                return job.dict()
            
            # Success
            job.generated_content = content
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            return {
                "success": True,
                "job": job.dict(),
                "content": content,
                "file_path": file_path,
            }
            
        except Exception as e:
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            return {
                "success": False,
                "job": job.dict(),
                "error": str(e),
            }
    
    def _build_generation_prompt(
        self,
        file_path: str,
        node_spec: dict,
        contracts: list[str],
        fr_refs: list[str],
        codebase_patterns: dict,
        dependency_outputs: dict
    ) -> str:
        """Build comprehensive generation prompt."""
        parts = []
        
        # File context
        parts.append(f"Generate the complete implementation for: {file_path}")
        parts.append("")
        
        # Module specification
        if node_spec.get("exports"):
            parts.append("## Required Exports")
            parts.append("This file must export:")
            for export in node_spec["exports"]:
                parts.append(f"- {export}")
            parts.append("")
        
        # Functional requirements
        if fr_refs:
            parts.append("## Functional Requirements to Satisfy")
            for fr in fr_refs:
                parts.append(f"- {fr}")
            parts.append("")
        
        # Contracts
        if contracts:
            parts.append("## Contracts (MUST adhere to these exactly)")
            for i, contract in enumerate(contracts, 1):
                parts.append(f"### Contract {i}")
                parts.append(contract)
                parts.append("")
        
        # Codebase patterns
        if codebase_patterns:
            parts.append("## Codebase Patterns to Follow")
            if "orm_style" in codebase_patterns:
                parts.append(f"- ORM style: {codebase_patterns['orm_style']}")
            if "error_handling" in codebase_patterns:
                parts.append(f"- Error handling: {codebase_patterns['error_handling']}")
            if "logging_style" in codebase_patterns:
                parts.append(f"- Logging: {codebase_patterns['logging_style']}")
            parts.append("")
        
        # Dependency outputs
        if dependency_outputs:
            parts.append("## Available Dependencies (outputs from previous levels)")
            for dep_path, output in dependency_outputs.items():
                parts.append(f"- {dep_path}: {output.get('exports', [])}")
            parts.append("")
        
        # Generation instructions
        parts.append("## Generation Instructions")
        parts.append("""
Generate COMPLETE, PRODUCTION-READY code:
1. No placeholders, TODOs, or stubs in core logic
2. Include proper error handling
3. Add type hints for all functions
4. Include docstrings for public functions
5. Follow the contracts exactly - function signatures must match
6. Import from contracts/models/ for Pydantic schemas
7. Use existing patterns from the codebase

Return ONLY the code, no explanations.
""")
        
        return "\n".join(parts)
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type from path."""
        if "/test" in file_path or file_path.startswith("test_"):
            return "test"
        elif file_path.endswith(".py"):
            return "source"
        elif file_path.endswith((".yaml", ".yml")):
            return "config"
        elif file_path.endswith(".md"):
            return "docs"
        return "other"
    
    def _validate_content(
        self,
        content: str,
        language: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate generated content.
        
        Args:
            content: Generated content
            language: File language
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not content.strip():
            return False, "Empty content generated"
        
        # Check for common placeholder patterns
        placeholders = [
            "TODO",
            "FIXME",
            "pass  # TODO",
            "raise NotImplementedError",
            "...  # TODO",
            "placeholder",
            "implement this",
        ]
        
        content_lower = content.lower()
        for placeholder in placeholders:
            if placeholder.lower() in content_lower:
                # Allow TODOs in comments, but not in actual code logic
                lines = content.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue  # Allow in comments
                    if placeholder.lower() in line.lower():
                        return False, f"Placeholder found: {placeholder}"
        
        # Language-specific validation
        if language == "python":
            import ast
            try:
                ast.parse(content)
            except SyntaxError as e:
                return False, f"Syntax error: {e}"
        
        return True, None
    
    def regenerate_with_context(
        self,
        original_content: str,
        error_message: str,
        contracts: list[str],
        fr_refs: list[str]
    ) -> dict:
        """
        Regenerate code with error context.
        
        Args:
            original_content: Original generated content
            error_message: Error that occurred
            contracts: Contracts to adhere to
            fr_refs: Functional requirements
        
        Returns:
            Regeneration result
        """
        prompt = f"""The following code has an error and needs to be fixed.

Original code:
```python
{original_content}
```

Error:
{error_message}

Contracts (must still adhere to these):
{contracts[:2]}  # First 2 contracts for context

Requirements:
{fr_refs}

Fix the error while maintaining all functionality and contract compliance.
Return the complete corrected code.
"""
        
        content = self.llm.generate_code(prompt, contracts=contracts)
        
        is_valid, error = self._validate_content(content, "python")
        
        return {
            "success": is_valid,
            "content": content,
            "error": error,
        }


# Celery task wrapper
def generate_file_task(
    run_id: str,
    file_path: str,
    level: int,
    node_spec: dict,
    contracts: list[str],
    fr_refs: list[str],
    codebase_patterns: dict,
    dependency_outputs: dict
) -> dict:
    """
    Celery task for file generation.
    
    This is the entry point for Celery workers.
    """
    worker = GenerationWorker()
    return worker.generate(
        run_id=run_id,
        file_path=file_path,
        level=level,
        node_spec=node_spec,
        contracts=contracts,
        fr_refs=fr_refs,
        codebase_patterns=codebase_patterns,
        dependency_outputs=dependency_outputs,
    )
