"""
APE - Autonomous Production Engineer
Dependency Graph Builder

Builds merged dependency graph including planned changes:
- Overlays new/modified nodes onto existing graph
- Computes import relationships
- Validates graph consistency
"""

from datetime import datetime
from typing import Optional

from contracts.models.architecture import ArchitecturePlan, ModuleChange, ModuleSpec
from contracts.models.graph import (
    DependencyGraph,
    Node,
    Edge,
    EdgeType,
    NodeType,
)


class DependencyGraphBuilder:
    """
    Builds dependency graph from architecture plan.
    """
    
    def __init__(self):
        """Initialize dependency graph builder."""
        pass
    
    def build(
        self,
        architecture_plan: ArchitecturePlan,
        existing_graph: DependencyGraph
    ) -> DependencyGraph:
        """
        Build merged dependency graph.
        
        Args:
            architecture_plan: Approved architecture plan
            existing_graph: Existing codebase graph
        
        Returns:
            Merged DependencyGraph with planned changes
        """
        # Start with existing nodes
        nodes = list(existing_graph.nodes)
        edges = list(existing_graph.edges)
        
        # Create node lookup
        node_lookup = {n.id: n for n in nodes}
        
        # Add/modify nodes from architecture plan
        for mod in architecture_plan.modified_modules:
            if mod.path in node_lookup:
                # Update existing node
                node = node_lookup[mod.path]
                node = Node(
                    id=node.id,
                    type=NodeType.MODIFIED,
                    module=node.module,
                    language=node.language,
                    exports=node.exports + [f"new: {f}" for f in mod.new_functions],
                    imports=node.imports,
                    test_file=node.test_file,
                    fr_refs=[],  # Will be populated later
                    estimated_complexity=self._map_complexity(mod.estimated_complexity),
                    test_coverage=node.test_coverage,
                    change_frequency=node.change_frequency,
                    cve_exposure=node.cve_exposure,
                )
                node_lookup[mod.path] = node
            else:
                # Add as modified (should exist)
                new_node = Node(
                    id=mod.path,
                    type=NodeType.MODIFIED,
                    module=self._path_to_module(mod.path),
                    language="python",
                    exports=[f"new: {f}" for f in mod.new_functions],
                    imports=[],
                    estimated_complexity=self._map_complexity(mod.estimated_complexity),
                )
                nodes.append(new_node)
                node_lookup[mod.path] = new_node
        
        # Add new nodes
        for new_mod in architecture_plan.new_modules:
            if new_mod.path not in node_lookup:
                new_node = Node(
                    id=new_mod.path,
                    type=NodeType.NEW,
                    module=self._path_to_module(new_mod.path),
                    language="python",
                    exports=new_mod.exports,
                    imports=new_mod.dependencies,
                    estimated_complexity=self._map_complexity(new_mod.estimated_complexity),
                )
                nodes.append(new_node)
                node_lookup[new_mod.path] = new_node
        
        # Build edges from new module dependencies
        for new_mod in architecture_plan.new_modules:
            source_path = new_mod.path
            for dep in new_mod.dependencies:
                # Find matching node
                target = self._find_module_by_name(node_lookup, dep)
                if target:
                    edges.append(Edge(
                        source=source_path,
                        target=target.id,
                        type=EdgeType.IMPORTS,
                    ))
        
        # Add edges from modified module changes
        for mod in architecture_plan.modified_modules:
            source_path = mod.path
            # Check if module imports any new modules
            for new_mod in architecture_plan.new_modules:
                if new_mod.module in mod.affected_functions or \
                   any(new_mod.name in f for f in mod.affected_functions):
                    target = node_lookup.get(new_mod.path)
                    if target:
                        edges.append(Edge(
                            source=source_path,
                            target=target.id,
                            type=EdgeType.DEPENDS_ON,
                        ))
        
        return DependencyGraph(
            id=f"depgraph-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            repo_id=existing_graph.repo_id,
            requirement_hash=None,  # Will be set by caller
            nodes=nodes,
            edges=edges,
            cycle_free=True,  # Will be validated by cycle detector
            generated_at=datetime.utcnow(),
        )
    
    def _path_to_module(self, path: str) -> str:
        """Convert file path to module name."""
        return path.replace("/", ".").replace("\\", ".")[:-3]
    
    def _map_complexity(self, complexity: str) -> str:
        """Map architecture complexity to node complexity."""
        return complexity  # Same enum values
    
    def _find_module_by_name(
        self,
        node_lookup: dict[str, Node],
        name: str
    ) -> Optional[Node]:
        """Find node by module name or path."""
        # Try exact match
        if name in node_lookup:
            return node_lookup[name]
        
        # Try by module name
        for node in node_lookup.values():
            if node.module == name or node.module.endswith(f".{name}"):
                return node
        
        # Try by path stem
        from pathlib import Path
        stem = Path(name).stem
        for node in node_lookup.values():
            if stem in node.id:
                return node
        
        return None
