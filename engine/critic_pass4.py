"""
APE - Autonomous Production Engineer
Critic Pass 4: Logic Correctness

LLM-judged logic validation:
- Verifies implementation satisfies requirements
- Checks for logical errors
- Scores: correct | incorrect | uncertain
"""

from typing import Optional

from engine.llm_client import LLMClient


class LogicCritic:
    """
    Pass 4: Logic correctness using LLM judge.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize logic critic.
        
        Args:
            llm_client: LLM client for judgment
        """
        self.llm = llm_client
    
    def check(
        self,
        content: str,
        fr_refs: list[str],
        contracts: list[str]
    ) -> tuple[bool, str, str, list[str]]:
        """
        Check logic correctness of implementation.
        
        Args:
            content: File content
            fr_refs: Functional requirements
            contracts: Contract specifications
        
        Returns:
            Tuple of (passed, score, reasoning, errors)
        """
        prompt = f"""Analyze this code for logical correctness.

Functional requirements:
{chr(10).join(fr_refs)}

Contracts (interface specifications):
{chr(10).join(contracts[:2]) if contracts else "None provided"}

Code to analyze:
```python
{content}
```

Check for:
1. Does the implementation correctly satisfy the requirements?
2. Are there any logical errors in the implementation?
3. Does it handle edge cases appropriately?
4. Does it follow the contract specifications?
5. Are there any potential bugs or issues?

Score as:
- "correct": Implementation is logically sound and satisfies requirements
- "incorrect": Implementation has logical errors or doesn't satisfy requirements
- "uncertain": Cannot determine correctness with confidence

Return JSON:
{{
    "score": "correct|incorrect|uncertain",
    "reasoning": "Detailed explanation of the analysis",
    "errors": [
        "List of specific logical errors found (if any)"
    ],
    "suggestions": [
        "List of improvement suggestions (if any)"
    ]
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {
            "score": "uncertain",
            "reasoning": "Failed to parse evaluation",
            "errors": [],
            "suggestions": []
        })
        
        score = result.get("score", "uncertain")
        reasoning = result.get("reasoning", "")
        errors = result.get("errors", [])
        
        # Pass only if correct
        passed = score == "correct"
        
        return passed, score, reasoning, errors
    
    def check_edge_cases(
        self,
        content: str,
        function_name: str,
        input_examples: list[dict]
    ) -> tuple[bool, list[str]]:
        """
        Check if function handles edge cases correctly.
        
        Args:
            content: File content
            function_name: Function to check
            input_examples: List of test input examples
        
        Returns:
            Tuple of (handles_all, list of unhandled cases)
        """
        prompt = f"""Analyze if this function handles the given edge cases.

Function code:
```python
{content}
```

Function name: {function_name}

Edge cases to check:
{input_examples}

For each edge case, determine if the function:
1. Explicitly handles it
2. Would handle it correctly based on the implementation
3. Would fail or behave incorrectly

Return JSON:
{{
    "handles_all": true/false,
    "unhandled_cases": [
        {{
            "case": "description of edge case",
            "reason": "why it's not handled"
        }}
    ]
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {
            "handles_all": False,
            "unhandled_cases": []
        })
        
        return result.get("handles_all", False), result.get("unhandled_cases", [])
    
    def check_error_handling(
        self,
        content: str
    ) -> tuple[bool, list[str]]:
        """
        Check if code has appropriate error handling.
        
        Args:
            content: File content
        
        Returns:
            Tuple of (has_error_handling, list of missing handlers)
        """
        prompt = f"""Analyze error handling in this code.

Code:
```python
{content}
```

Check for:
1. Try/except blocks around operations that can fail
2. Validation of inputs
3. Handling of None/null values
4. Handling of empty collections
5. Timeout handling for I/O operations
6. Proper error messages

Return JSON:
{{
    "has_error_handling": true/false,
    "missing_handlers": [
        "Description of missing error handling"
    ],
    "quality": "good|adequate|poor"
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        result = self.llm.parse_json(response, {
            "has_error_handling": False,
            "missing_handlers": [],
            "quality": "poor"
        })
        
        return result.get("has_error_handling", False), result.get("missing_handlers", [])
