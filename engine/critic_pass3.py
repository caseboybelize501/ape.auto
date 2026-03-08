"""
APE - Autonomous Production Engineer
Critic Pass 3: Completeness Check

LLM-judged completeness validation:
- Checks for pass/placeholder/TODO in logic
- Verifies all FR-required functions are implemented
- Scores: complete | partial | stub
"""

from typing import Optional

from engine.llm_client import LLMClient


class CompletenessCritic:
    """
    Pass 3: Completeness check using LLM judge.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize completeness critic.
        
        Args:
            llm_client: LLM client for judgment
        """
        self.llm = llm_client
    
    def check(
        self,
        content: str,
        fr_refs: list[str]
    ) -> tuple[bool, str, str]:
        """
        Check completeness of implementation.
        
        Args:
            content: File content
            fr_refs: Functional requirements this file satisfies
        
        Returns:
            Tuple of (passed, score, reasoning)
        """
        prompt = f"""Analyze this code for completeness.

Functional requirements this file should satisfy:
{chr(10).join(fr_refs)}

Code to analyze:
```python
{content}
```

Check for:
1. Any pass statements in non-trivial functions
2. Any raise NotImplementedError
3. Any TODO or FIXME comments in core logic
4. Any functions that are declared but have empty/trivial bodies
5. Incomplete implementations of FR-specified behavior

Score as:
- "complete": All functions fully implemented, no placeholders
- "partial": Some functions have placeholders or incomplete logic
- "stub": Most or all functions are stubs/placeholders

Return JSON:
{{
    "score": "complete|partial|stub",
    "reasoning": "Detailed explanation",
    "issues": [
        {{
            "type": "pass_statement|not_implemented|todo|empty_body",
            "location": "function_name or line",
            "description": "What's incomplete"
        }}
    ]
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {
            "score": "uncertain",
            "reasoning": "Failed to parse evaluation",
            "issues": []
        })
        
        score = result.get("score", "uncertain")
        reasoning = result.get("reasoning", "")
        
        # Pass only if complete
        passed = score == "complete"
        
        return passed, score, reasoning
    
    def check_specific_functions(
        self,
        content: str,
        required_functions: list[str]
    ) -> tuple[bool, list[str]]:
        """
        Check if specific required functions are implemented.
        
        Args:
            content: File content
            required_functions: List of function names that must be implemented
        
        Returns:
            Tuple of (all_implemented, list of missing/incomplete)
        """
        import ast
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return False, ["Syntax error prevents analysis"]
        
        # Find all function definitions
        defined_functions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function body is trivial
                is_trivial = self._is_trivial_body(node)
                defined_functions[node.name] = not is_trivial
        
        # Check required functions
        missing_or_incomplete = []
        for func_name in required_functions:
            if func_name not in defined_functions:
                missing_or_incomplete.append(f"{func_name} (not defined)")
            elif not defined_functions[func_name]:
                missing_or_incomplete.append(f"{func_name} (trivial body)")
        
        return len(missing_or_incomplete) == 0, missing_or_incomplete
    
    def _is_trivial_body(self, node: ast.FunctionDef) -> bool:
        """Check if function body is trivial (pass, ellipsis, etc.)."""
        body = node.body
        
        if not body:
            return True
        
        if len(body) == 1:
            stmt = body[0]
            
            # Just 'pass'
            if isinstance(stmt, ast.Pass):
                return True
            
            # Just '...'
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant):
                    if stmt.value.value is Ellipsis:
                        return True
                # Just docstring
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    return True
            
            # Just 'raise NotImplementedError'
            if isinstance(stmt, ast.Raise):
                if stmt.exc:
                    if isinstance(stmt.exc, ast.Call):
                        if isinstance(stmt.exc.func, ast.Name):
                            if "NotImplemented" in stmt.exc.func.id:
                                return True
        
        return False
