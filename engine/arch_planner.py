"""
APE - Autonomous Production Engineer
Architecture Planner

Generates architecture plan from requirement spec and codebase graph:
- Module modifications vs creations
- Data flow design
- Persistence changes
- Async boundaries
- Risk assessment
"""

from datetime import datetime
from typing import Optional

from contracts.models.requirement import RequirementSpec
from contracts.models.architecture import (
    ArchitecturePlan,
    ModuleChange,
    ModuleSpec,
    DataFlowDiagram,
    DataFlowNode,
    DataFlowEdge,
    SchemaChange,
    AsyncSpec,
    Risk,
    RiskCategory,
    RiskLevel,
    ChangeType,
)
from contracts.models.graph import DependencyGraph

from engine.llm_client import LLMClient


class ArchitecturePlanner:
    """
    Generates architecture plans from requirements.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize architecture planner.
        
        Args:
            llm_client: LLM client for planning
        """
        self.llm = llm_client
    
    def create_plan(
        self,
        requirement_spec: RequirementSpec,
        codebase_graph: DependencyGraph
    ) -> ArchitecturePlan:
        """
        Create architecture plan from requirement spec.
        
        Args:
            requirement_spec: Requirement spec
            codebase_graph: Current codebase graph
        
        Returns:
            Complete ArchitecturePlan
        """
        # Extract codebase patterns
        existing_patterns = self._extract_codebase_patterns(codebase_graph)
        
        # Generate module changes
        modified_modules = self._plan_module_modifications(
            requirement_spec, codebase_graph
        )
        
        # Generate new module specs
        new_modules = self._plan_new_modules(
            requirement_spec, codebase_graph
        )
        
        # Design data flow
        data_flow = self._design_data_flow(
            requirement_spec, modified_modules, new_modules
        )
        
        # Plan persistence changes
        persistence_changes = self._plan_persistence_changes(
            requirement_spec, data_flow
        )
        
        # Identify async boundaries
        async_boundaries = self._identify_async_boundaries(
            requirement_spec, data_flow
        )
        
        # Assess risks
        risk_flags = self._assess_risks(
            requirement_spec, modified_modules, new_modules, data_flow
        )
        
        return ArchitecturePlan(
            id=f"arch-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            requirement_spec_id=requirement_spec.id,
            repo_id=requirement_spec.repo_id,
            modified_modules=modified_modules,
            new_modules=new_modules,
            data_flow=data_flow,
            persistence_changes=persistence_changes,
            async_boundaries=async_boundaries,
            risk_flags=risk_flags,
            existing_patterns=existing_patterns,
            test_patterns=self._extract_test_patterns(codebase_graph),
            naming_conventions=self._extract_naming_conventions(codebase_graph),
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    def _extract_codebase_patterns(
        self,
        graph: DependencyGraph
    ) -> dict:
        """Extract existing patterns from codebase."""
        patterns = {
            "orm_style": "sqlalchemy",  # Default, could be detected
            "error_handling": "try_except",
            "logging_style": "structlog",
            "api_style": "rest",
            "test_framework": "pytest",
        }
        
        # Analyze imports to detect patterns
        for node in graph.nodes:
            if "fastapi" in node.imports:
                patterns["api_style"] = "fastapi"
            if "flask" in node.imports:
                patterns["api_style"] = "flask"
            if "django" in node.imports:
                patterns["orm_style"] = "django_orm"
                patterns["api_style"] = "django_rest"
            if "logging" in node.imports:
                patterns["logging_style"] = "logging"
        
        return patterns
    
    def _extract_test_patterns(self, graph: DependencyGraph) -> dict:
        """Extract test patterns from codebase."""
        return {
            "framework": "pytest",
            "fixture_style": "function_scope",
            "mock_library": "unittest.mock",
            "coverage_target": 80,
        }
    
    def _extract_naming_conventions(self, graph: DependencyGraph) -> dict:
        """Extract naming conventions from codebase."""
        return {
            "modules": "snake_case",
            "classes": "PascalCase",
            "functions": "snake_case",
            "constants": "UPPER_SNAKE_CASE",
            "tests": "test_<function>_<scenario>",
        }
    
    def _plan_module_modifications(
        self,
        spec: RequirementSpec,
        graph: DependencyGraph
    ) -> list[ModuleChange]:
        """Plan modifications to existing modules."""
        # Build module info for context
        module_info = []
        for node in graph.nodes:
            if node.id in spec.affected_modules:
                module_info.append({
                    "path": node.id,
                    "exports": node.exports,
                    "complexity": node.estimated_complexity,
                })
        
        prompt = f"""
Plan modifications to existing modules for this requirement.

Existing modules to modify:
{module_info}

Requirement functional specs:
{[(f.id, f.title, f.verb, f.noun) for f in spec.functional]}

For each module, specify:
- What functions will be modified
- What new functions will be added
- Change type (modify, extend, refactor)
- Estimated complexity

Return JSON array:
[
    {{
        "path": "path/to/module.py",
        "change_type": "modify|extend|refactor",
        "description": "What is being changed",
        "affected_functions": ["func1", "func2"],
        "new_functions": ["new_func"],
        "estimated_complexity": "low|medium|high"
    }}
]

Return ONLY valid JSON array.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        changes = self.llm.parse_json(response, [])
        
        result = []
        for c in changes:
            result.append(ModuleChange(
                path=c.get("path", ""),
                change_type=ChangeType(c.get("change_type", "modify")),
                description=c.get("description", ""),
                affected_functions=c.get("affected_functions", []),
                new_functions=c.get("new_functions", []),
                estimated_complexity=c.get("estimated_complexity", "medium"),
            ))
        
        return result
    
    def _plan_new_modules(
        self,
        spec: RequirementSpec,
        graph: DependencyGraph
    ) -> list[ModuleSpec]:
        """Plan new modules to create."""
        if not spec.new_modules:
            return []
        
        prompt = f"""
Define specifications for new modules to create.

New modules needed:
{spec.new_modules}

Requirement context:
{spec.raw_text[:500]}

For each module, specify:
- Module name and path
- Responsibility/description
- Public exports (functions, classes)
- Dependencies on other modules

Return JSON array:
[
    {{
        "name": "module_name",
        "path": "path/to/module.py",
        "description": "Module responsibility",
        "exports": ["def function1", "class ClassName"],
        "dependencies": ["other.module"],
        "estimated_complexity": "low|medium|high"
    }}
]

Return ONLY valid JSON array.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        specs = self.llm.parse_json(response, [])
        
        result = []
        for s in specs:
            result.append(ModuleSpec(
                name=s.get("name", ""),
                path=s.get("path", ""),
                description=s.get("description", ""),
                exports=s.get("exports", []),
                dependencies=s.get("dependencies", []),
                estimated_complexity=s.get("estimated_complexity", "medium"),
            ))
        
        return result
    
    def _design_data_flow(
        self,
        spec: RequirementSpec,
        modified: list[ModuleChange],
        new: list[ModuleSpec]
    ) -> Optional[DataFlowDiagram]:
        """Design data flow for the requirement."""
        prompt = f"""
Design the data flow for this requirement implementation.

Modules involved:
Modified: {[m.path for m in modified]}
New: {[n.path for n in new]}

Requirement:
{spec.raw_text[:500]}

Identify:
- Entry points (where data enters)
- Exit points (where data exits)
- Processing nodes (services, functions)
- Data stores (databases, caches)
- Communication protocols between nodes

Return JSON:
{{
    "nodes": [
        {{"id": "node1", "type": "api|service|database|cache|queue", "name": "Name", "description": "..."}}
    ],
    "edges": [
        {{"source": "node1", "target": "node2", "protocol": "http|grpc|async|sql", "data_types": ["Type1"]}}
    ],
    "entry_points": ["node_id"],
    "exit_points": ["node_id"]
}}

Return ONLY valid JSON.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        data = self.llm.parse_json(response, {})
        
        if not data:
            return None
        
        nodes = [
            DataFlowNode(
                id=n.get("id", ""),
                type=n.get("type", "service"),
                name=n.get("name", ""),
                description=n.get("description"),
            )
            for n in data.get("nodes", [])
        ]
        
        edges = [
            DataFlowEdge(
                source=e.get("source", ""),
                target=e.get("target", ""),
                protocol=e.get("protocol", "http"),
                description=None,
                data_types=e.get("data_types", []),
            )
            for e in data.get("edges", [])
        ]
        
        return DataFlowDiagram(
            nodes=nodes,
            edges=edges,
            entry_points=data.get("entry_points", []),
            exit_points=data.get("exit_points", []),
        )
    
    def _plan_persistence_changes(
        self,
        spec: RequirementSpec,
        data_flow: Optional[DataFlowDiagram]
    ) -> list[SchemaChange]:
        """Plan database/cache schema changes."""
        # Check if data flow includes databases
        if not data_flow:
            return []
        
        db_nodes = [n for n in data_flow.nodes if n.type == "database"]
        if not db_nodes:
            return []
        
        prompt = f"""
Plan database schema changes for this requirement.

Database nodes in data flow:
{[(n.id, n.name) for n in db_nodes]}

Requirement:
{spec.raw_text[:500]}

Specify schema changes:
- Tables/collections affected
- New/modified columns/fields
- Index changes
- Migration requirements

Return JSON array:
[
    {{
        "table_or_collection": "table_name",
        "change_type": "create|modify|delete",
        "columns_or_fields": [{{"name": "col", "type": "type"}}],
        "indexes": [{{"name": "idx", "columns": ["col"]}}],
        "migration_required": true,
        "rollback_possible": true
    }}
]

Return ONLY valid JSON array.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        changes = self.llm.parse_json(response, [])
        
        result = []
        for c in changes:
            result.append(SchemaChange(
                table_or_collection=c.get("table_or_collection", ""),
                change_type=ChangeType(c.get("change_type", "modify")),
                columns_or_fields=c.get("columns_or_fields", []),
                indexes=c.get("indexes", []),
                migration_required=c.get("migration_required", True),
                rollback_possible=c.get("rollback_possible", True),
            ))
        
        return result
    
    def _identify_async_boundaries(
        self,
        spec: RequirementSpec,
        data_flow: Optional[DataFlowDiagram]
    ) -> list[AsyncSpec]:
        """Identify async communication boundaries."""
        if not data_flow:
            return []
        
        # Find queue nodes
        queue_nodes = [n for n in data_flow.nodes if n.type == "queue"]
        if not queue_nodes:
            return []
        
        prompt = f"""
Define async communication specifications for queue-based interactions.

Queue nodes:
{[(n.id, n.name) for n in queue_nodes]}

Data flow edges:
{[(e.source, e.target, e.protocol) for e in data_flow.edges if e.protocol == "async"]}

For each async boundary, specify:
- Source and target modules
- Message/event schema
- Delivery guarantee
- Retry policy

Return JSON array:
[
    {{
        "boundary_id": "async-001",
        "source_module": "module.path",
        "target_module": "module.path",
        "mechanism": "queue|event_bus|webhook",
        "message_schema": {{"field": "type"}},
        "delivery_guarantee": "at-least-once",
        "retry_policy": {{"max_retries": 3, "backoff": "exponential"}}
    }}
]

Return ONLY valid JSON array.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        specs = self.llm.parse_json(response, [])
        
        result = []
        for s in specs:
            result.append(AsyncSpec(
                boundary_id=s.get("boundary_id", ""),
                source_module=s.get("source_module", ""),
                target_module=s.get("target_module", ""),
                mechanism=s.get("mechanism", "queue"),
                message_schema=s.get("message_schema", {}),
                delivery_guarantee=s.get("delivery_guarantee", "at-least-once"),
                retry_policy=s.get("retry_policy"),
            ))
        
        return result
    
    def _assess_risks(
        self,
        spec: RequirementSpec,
        modified: list[ModuleChange],
        new: list[ModuleSpec],
        data_flow: Optional[DataFlowDiagram]
    ) -> list[Risk]:
        """Assess risks in the architecture."""
        prompt = f"""
Assess risks in this architecture plan.

Modified modules:
{[(m.path, m.change_type) for m in modified]}

New modules:
{[(n.path, n.description) for n in new]}

Data flow entry/exit points:
Entry: {data_flow.entry_points if data_flow else []}
Exit: {data_flow.exit_points if data_flow else []}

Requirement (check for security/compliance implications):
{spec.raw_text[:500]}

Identify risks in categories:
- security: auth, data exposure, injection
- data_integrity: data loss, corruption
- performance: latency, throughput
- availability: downtime, single points of failure
- compliance: regulatory requirements
- technical_debt: shortcuts, complexity

Return JSON array:
[
    {{
        "id": "RISK-001",
        "category": "security|data_integrity|performance|availability|compliance|technical_debt",
        "level": "low|medium|high|critical",
        "description": "Risk description",
        "mitigation": "Proposed mitigation",
        "affected_areas": ["area1", "area2"]
    }}
]

Return ONLY valid JSON array.
"""
        
        response = self.llm.generate(prompt, temperature=0.1)
        risks = self.llm.parse_json(response, [])
        
        result = []
        for i, r in enumerate(risks, 1):
            result.append(Risk(
                id=r.get("id", f"RISK-{i:03d}"),
                category=RiskCategory(r.get("category", "technical_debt")),
                level=RiskLevel(r.get("level", "medium")),
                description=r.get("description", ""),
                mitigation=r.get("mitigation"),
                affected_areas=r.get("affected_areas", []),
            ))
        
        return result
    
    def validate_plan(self, plan: ArchitecturePlan) -> tuple[bool, list[str]]:
        """
        Validate architecture plan for completeness.
        
        Args:
            plan: Plan to validate
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check for at least one module change or new module
        if not plan.modified_modules and not plan.new_modules:
            issues.append("No module changes specified")
        
        # Check for critical risks without mitigation
        for risk in plan.risk_flags:
            if risk.level == RiskLevel.CRITICAL and not risk.mitigation:
                issues.append(f"Critical risk {risk.id} has no mitigation")
        
        # Check data flow completeness
        if plan.data_flow:
            if not plan.data_flow.entry_points:
                issues.append("Data flow has no entry points")
            if not plan.data_flow.exit_points:
                issues.append("Data flow has no exit points")
        
        return len(issues) == 0, issues
