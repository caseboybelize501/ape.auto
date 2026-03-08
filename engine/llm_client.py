"""
APE - Autonomous Production Engineer
LLM Client

Unified LLM client supporting multiple providers:
- OpenAI (GPT-4)
- Anthropic (Claude)
- Local models (via OpenAI-compatible API)

Provides:
- Text generation
- JSON parsing
- Multi-turn conversations
- Token counting
"""

import json
from typing import Optional, Any
from datetime import datetime

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class LLMClient:
    """
    Unified LLM client for code generation and analysis.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider name (openai, anthropic, local)
            model: Model name
            api_key: API key
            api_base: API base URL (for local models)
            temperature: Generation temperature
            max_tokens: Max tokens in response
        """
        self.provider = provider
        self.model = model or self._default_model(provider)
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Set provider-specific config
        self._configure_provider()
    
    def _default_model(self, provider: str) -> str:
        """Get default model for provider."""
        if provider == "openai":
            return "gpt-4-turbo-preview"
        elif provider == "anthropic":
            return "claude-3-opus-20240229"
        elif provider == "local":
            return "local-model"
        return "gpt-4-turbo-preview"
    
    def _configure_provider(self) -> None:
        """Configure provider-specific settings."""
        if self.provider == "openai":
            if self.api_key:
                import os
                os.environ["OPENAI_API_KEY"] = self.api_key
        
        elif self.provider == "anthropic":
            if self.api_key:
                import os
                os.environ["ANTHROPIC_API_KEY"] = self.api_key
        
        elif self.provider == "local":
            if self.api_base:
                import os
                os.environ["OPENAI_API_BASE"] = self.api_base
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens
        
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            if LITELLM_AVAILABLE:
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    **kwargs
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback to basic OpenAI client
                return self._generate_openai(messages, temperature, max_tokens)
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _generate_openai(
        self,
        messages: list[dict],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Fallback OpenAI generation without litellm."""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            return response.choices[0].message.content.strip()
        except ImportError:
            raise ImportError("Please install openai or litellm package")
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")
    
    def generate_json(
        self,
        prompt: str,
        schema_description: str,
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        Generate JSON response.
        
        Args:
            prompt: User prompt
            schema_description: Description of expected JSON schema
            system_prompt: Optional system prompt
        
        Returns:
            Parsed JSON dict
        """
        default_system = """You are a JSON generation assistant.
Always respond with valid JSON only. No markdown, no explanations.
Ensure JSON is properly formatted and matches the requested schema."""

        full_system = f"{default_system}\n\nExpected schema: {schema_description}"
        if system_prompt:
            full_system = f"{system_prompt}\n\n{full_system}"
        
        response = self.generate(
            prompt,
            system_prompt=full_system,
            temperature=0.1  # Low temp for deterministic JSON
        )
        
        return self.parse_json(response, {})
    
    def parse_json(self, text: str, default: Any = None) -> Any:
        """
        Parse JSON from text response.
        
        Args:
            text: Text containing JSON
            default: Default value if parsing fails
        
        Returns:
            Parsed JSON or default
        """
        if not text:
            return default
        
        # Try to extract JSON from markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in text
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except:
                pass
            
            # Try array
            try:
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except:
                pass
            
            return default
    
    def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        contracts: Optional[list[str]] = None
    ) -> str:
        """
        Generate code with context and contracts.
        
        Args:
            prompt: Code generation prompt
            language: Programming language
            context: Additional context
            contracts: Contract files to reference
        
        Returns:
            Generated code
        """
        system_prompt = f"""You are an expert {language} developer.
Generate complete, production-ready code.
- No placeholders or TODOs in core logic
- Follow best practices for {language}
- Include proper error handling
- Add type hints (for Python)
- Follow existing code patterns"""

        full_prompt = []
        
        if context:
            full_prompt.append(f"Context:\n{context}\n")
        
        if contracts:
            full_prompt.append("Contracts (must adhere to these):\n")
            for contract in contracts:
                full_prompt.append(f"```{language}\n{contract}\n```\n")
        
        full_prompt.append(f"Task:\n{prompt}")
        
        return self.generate(
            "\n".join(full_prompt),
            system_prompt=system_prompt,
            temperature=0.2  # Low temp for code
        )
    
    def judge_code(
        self,
        code: str,
        criteria: str,
        context: Optional[str] = None
    ) -> dict:
        """
        Judge code quality based on criteria.
        
        Args:
            code: Code to judge
            criteria: Evaluation criteria
            context: Additional context
        
        Returns:
            Judgment dict with score and reasoning
        """
        prompt = f"""Evaluate the following code based on these criteria:

Criteria:
{criteria}

Code:
```python
{code}
```

Provide evaluation as JSON:
{{
    "score": "pass|fail|uncertain",
    "reasoning": "Detailed explanation",
    "issues": ["list of specific issues if any"]
}}"""

        if context:
            prompt = f"Context:\n{context}\n\n{prompt}"
        
        response = self.generate(
            prompt,
            system_prompt="You are a code review expert. Provide objective, detailed evaluations.",
            temperature=0.1
        )
        
        return self.parse_json(response, {
            "score": "uncertain",
            "reasoning": "Failed to parse evaluation",
            "issues": []
        })
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
        
        Returns:
            Token count
        """
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except ImportError:
            # Rough estimate: 4 chars per token
            return len(text) // 4
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for generation.
        
        Args:
            prompt_tokens: Input token count
            completion_tokens: Output token count
        
        Returns:
            Estimated cost in USD
        """
        # Approximate pricing (update as needed)
        pricing = {
            "gpt-4-turbo-preview": {"prompt": 0.00001, "completion": 0.00003},
            "gpt-4": {"prompt": 0.00003, "completion": 0.00006},
            "claude-3-opus-20240229": {"prompt": 0.000015, "completion": 0.000075},
        }
        
        rates = pricing.get(self.model, {"prompt": 0.00001, "completion": 0.00003})
        
        return (prompt_tokens * rates["prompt"]) + (completion_tokens * rates["completion"])
