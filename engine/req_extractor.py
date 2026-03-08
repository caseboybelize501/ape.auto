"""
APE - Autonomous Production Engineer
Requirements Extractor

Extracts structured requirements from raw text using LLM:
- Functional requirements (FR-N)
- Non-functional requirements (NFR-N)
- Affected modules
- New modules required
- Acceptance criteria
- Ambiguity detection
"""

from datetime import datetime
from typing import Optional
import hashlib

from contracts.models.requirement import (
    RequirementSpec,
    FunctionalRequirement,
    NonFunctionalRequirement,
    Criterion,
    Question,
    Priority,
    RequirementStatus,
)
from contracts.models.graph import DependencyGraph

from engine.llm_client import LLMClient


class RequirementsExtractor:
    """
    Extracts structured requirements from raw text.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize requirements extractor.
        
        Args:
            llm_client: LLM client for extraction
        """
        self.llm = llm_client
    
    def extract(
        self,
        raw_text: str,
        repo_id: str,
        codebase_graph: DependencyGraph,
        source: str = "manual",
        source_id: Optional[str] = None
    ) -> RequirementSpec:
        """
        Extract structured requirements from raw text.
        
        Args:
            raw_text: Raw requirement text
            repo_id: Target repository ID
            codebase_graph: Current codebase graph
            source: Source type (ticket, PRD, voice, manual)
            source_id: Original ticket/PRD ID
        
        Returns:
            Complete RequirementSpec
        """
        # Compute requirement hash for deduplication
        req_hash = RequirementSpec.compute_hash(raw_text, repo_id)
        
        # Extract functional requirements
        functional = self._extract_functional(raw_text)
        
        # Extract non-functional requirements
        non_functional = self._extract_non_functional(raw_text)
        
        # Identify affected modules from codebase graph
        affected_modules = self._identify_affected_modules(
            raw_text, codebase_graph
        )
        
        # Identify new modules needed
        new_modules = self._identify_new_modules(raw_text, affected_modules)
        
        # Extract acceptance criteria
        acceptance_criteria = self._extract_acceptance_criteria(raw_text, functional)
        
        # Detect ambiguities
        ambiguities = self._detect_ambiguities(raw_text, functional, affected_modules)
        
        # Determine priority
        priority = self._determine_priority(raw_text, non_functional)
        
        # Determine initial status
        status = RequirementStatus.SUBMITTED
        if ambiguities:
            status = RequirementStatus.AMBIGUOUS
        
        return RequirementSpec(
            id=f"req-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{req_hash[:8]}",
            repo_id=repo_id,
            raw_text=raw_text,
            source=source,
            source_id=source_id,
            functional=functional,
            non_functional=non_functional,
            affected_modules=affected_modules,
            new_modules=new_modules,
            acceptance_criteria=acceptance_criteria,
            ambiguities=ambiguities,
            priority=priority,
            status=status,
            requirement_hash=req_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    def _extract_functional(self, raw_text: str) -> list[FunctionalRequirement]:
        """Extract functional requirements from text."""
        prompt = f"""
Extract functional requirements from the following requirement text.

Each functional requirement should:
- Have a clear verb + noun structure (e.g., "create user session", "validate input")
- Be testable with binary pass/fail criteria
- Be atomic (one behavior per requirement)

Return the result as a JSON array with this structure:
[
    {{
        "id": "FR-001",
        "title": "Short title",
        "description": "Full description",
        "verb": "action verb",
        "noun": "target entity",
        "acceptance_criteria": ["criterion 1", "criterion 2"],
        "priority": "medium"
    }}
]

Requirement text:
{raw_text}

Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        frs = self.llm.parse_json(response, [])
        
        result = []
        for i, fr in enumerate(frs, 1):
            result.append(FunctionalRequirement(
                id=fr.get("id", f"FR-{i:03d}"),
                title=fr.get("title", f"FR-{i:03d}"),
                description=fr.get("description", ""),
                verb=fr.get("verb", "implement"),
                noun=fr.get("noun", "feature"),
                acceptance_criteria=fr.get("acceptance_criteria", []),
                priority=Priority(fr.get("priority", "medium")),
            ))
        
        return result
    
    def _extract_non_functional(self, raw_text: str) -> list[NonFunctionalRequirement]:
        """Extract non-functional requirements from text."""
        prompt = f"""
Extract non-functional requirements from the following requirement text.

Non-functional requirements include:
- Performance (latency, throughput)
- Security (authentication, authorization, encryption)
- Scalability (concurrent users, data volume)
- Reliability (uptime, error handling)
- Compliance (regulatory requirements)

Return the result as a JSON array with this structure:
[
    {{
        "id": "NFR-001",
        "category": "performance|security|scalability|reliability|compliance",
        "description": "Full description",
        "metric": "measurable metric",
        "threshold": "acceptable threshold"
    }}
]

Requirement text:
{raw_text}

Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        nfrs = self.llm.parse_json(response, [])
        
        result = []
        for i, nfr in enumerate(nfrs, 1):
            result.append(NonFunctionalRequirement(
                id=nfr.get("id", f"NFR-{i:03d}"),
                category=nfr.get("category", "performance"),
                description=nfr.get("description", ""),
                metric=nfr.get("metric"),
                threshold=nfr.get("threshold"),
            ))
        
        return result
    
    def _identify_affected_modules(
        self,
        raw_text: str,
        codebase_graph: DependencyGraph
    ) -> list[str]:
        """Identify existing modules that will be affected."""
        # Get all module names from graph
        modules = [n.module for n in codebase_graph.nodes]
        module_paths = [n.id for n in codebase_graph.nodes]
        
        prompt = f"""
Given the following requirement and existing codebase modules,
identify which existing modules will be affected by this requirement.

Existing modules:
{", ".join(modules[:50])}  # Limit to first 50 for context

Requirement:
{raw_text}

Return a JSON array of module paths that will be MODIFIED (not new modules):
["path/to/module1.py", "path/to/module2.py"]

Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        affected = self.llm.parse_json(response, [])
        
        # Filter to only valid module paths
        valid_paths = set(module_paths)
        return [p for p in affected if p in valid_paths]
    
    def _identify_new_modules(
        self,
        raw_text: str,
        affected_modules: list[str]
    ) -> list[str]:
        """Identify new modules that need to be created."""
        prompt = f"""
Given the following requirement and already affected modules,
identify any NEW modules that need to be CREATED.

Affected existing modules:
{", ".join(affected_modules)}

Requirement:
{raw_text}

Return a JSON array of new module paths to CREATE:
["path/to/new_module.py", "path/to/new_service.py"]

Return empty array if no new modules needed.
Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        return self.llm.parse_json(response, [])
    
    def _extract_acceptance_criteria(
        self,
        raw_text: str,
        functional: list[FunctionalRequirement]
    ) -> list[Criterion]:
        """Extract acceptance criteria from text."""
        prompt = f"""
Extract acceptance criteria from the following requirement text.

Each acceptance criterion must be:
- Binary (pass/fail)
- Testable
- Unambiguous

Return the result as a JSON array with this structure:
[
    {{
        "id": "AC-001",
        "description": "Clear, testable criterion",
        "testable": true,
        "automated": true
    }}
]

Requirement text:
{raw_text}

Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        criteria = self.llm.parse_json(response, [])
        
        result = []
        for i, c in enumerate(criteria, 1):
            result.append(Criterion(
                id=c.get("id", f"AC-{i:03d}"),
                description=c.get("description", ""),
                testable=c.get("testable", True),
                automated=c.get("automated", True),
            ))
        
        return result
    
    def _detect_ambiguities(
        self,
        raw_text: str,
        functional: list[FunctionalRequirement],
        affected_modules: list[str]
    ) -> list[Question]:
        """Detect ambiguities that need human clarification."""
        prompt = f"""
Analyze the following requirement for ambiguities that need human clarification.

An ambiguity is something that:
- Is unclear or vague
- Has multiple possible interpretations
- Requires domain knowledge to resolve
- Could lead to incorrect implementation if guessed

Functional requirements extracted:
{[(f.title, f.description) for f in functional]}

Affected modules:
{affected_modules}

Requirement text:
{raw_text}

Return a JSON array with this structure:
[
    {{
        "id": "Q-001",
        "question": "Clear question to human",
        "context": "Why this matters / what's ambiguous",
        "suggested_answer": "AI's best guess (optional)"
    }}
]

Return empty array if no ambiguities found.
Return ONLY valid JSON array, no other text.
"""
        
        response = self.llm.generate(prompt, temperature=0.2)
        questions = self.llm.parse_json(response, [])
        
        result = []
        for i, q in enumerate(questions, 1):
            result.append(Question(
                id=q.get("id", f"Q-{i:03d}"),
                question=q.get("question", ""),
                context=q.get("context", ""),
                suggested_answer=q.get("suggested_answer"),
                resolved=False,
            ))
        
        return result
    
    def _determine_priority(
        self,
        raw_text: str,
        non_functional: list[NonFunctionalRequirement]
    ) -> Priority:
        """Determine requirement priority."""
        # Check for priority indicators in text
        text_lower = raw_text.lower()
        
        if any(w in text_lower for w in ["critical", "urgent", "emergency", "blocker"]):
            return Priority.CRITICAL
        if any(w in text_lower for w in ["high priority", "important", "asap"]):
            return Priority.HIGH
        if any(w in text_lower for w in ["low priority", "nice to have", "optional"]):
            return Priority.LOW
        
        # Check NFRs for security/compliance (usually high priority)
        for nfr in non_functional:
            if nfr.category in ("security", "compliance"):
                return Priority.HIGH
        
        return Priority.MEDIUM
    
    def resolve_ambiguity(
        self,
        spec: RequirementSpec,
        question_id: str,
        answer: str,
        resolved_by: str
    ) -> RequirementSpec:
        """
        Resolve an ambiguity in a requirement spec.
        
        Args:
            spec: Requirement spec to update
            question_id: Question ID to resolve
            answer: Human-provided answer
            resolved_by: User who resolved
        
        Returns:
            Updated RequirementSpec
        """
        updated_ambiguities = []
        
        for q in spec.ambiguities:
            if q.id == question_id:
                q.resolved = True
                q.resolved_at = datetime.utcnow()
                q.resolved_by = resolved_by
                # Store answer in context for downstream use
            updated_ambiguities.append(q)
        
        # Update status if all ambiguities resolved
        has_unresolved = any(not q.resolved for q in updated_ambiguities)
        new_status = RequirementStatus.APPROVED if not has_unresolved else RequirementStatus.AMBIGUOUS
        
        return RequirementSpec(
            **spec.dict(),
            ambiguities=updated_ambiguities,
            status=new_status,
            updated_at=datetime.utcnow(),
        )
