"""
APE - Autonomous Production Engineer
Topological Sorter

Implements Kahn's algorithm for topological sorting:
- Computes in-degrees
- Generates parallel-safe levels
- Identifies critical path
- Creates build plan for orchestration
"""

from datetime import datetime
from collections import defaultdict, deque
from typing import Optional

from contracts.models.graph import (
    DependencyGraph,
    BuildPlan,
    Level,
    ChordTask,
    ChainTask,
    TestLevel,
    Node,
)


class TopologicalSorter:
    """
    Topological sort using Kahn's algorithm.
    """
    
    def __init__(self):
        """Initialize topological sorter."""
        pass
    
    def sort(self, graph: DependencyGraph) -> BuildPlan:
        """
        Perform topological sort using Kahn's algorithm.
        
        Args:
            graph: Cycle-free dependency graph
        
        Returns:
            BuildPlan with levels for parallel generation
        """
        if not graph.cycle_free:
            raise ValueError("Graph contains cycles - must detect cycles first")
        
        # Build adjacency list and in-degree count
        adj = defaultdict(list)
        in_degree = {node.id: 0 for node in graph.nodes}
        
        for edge in graph.edges:
            adj[edge.target].append(edge.source)  # Reverse: dependents point to dependency
            in_degree[edge.source] = in_degree.get(edge.source, 0) + 1
        
        # Initialize queue with nodes having in-degree 0
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        
        levels = []
        level_num = 0
        processed = set()
        
        while queue:
            # All nodes in current queue can be processed in parallel
            level_nodes = list(queue)
            
            # Create level
            level = Level(
                level=level_num,
                files=level_nodes,
                parallel=True,
                status="pending",
            )
            levels.append(level)
            
            # Process all nodes in this level
            queue.clear()
            for node_id in level_nodes:
                processed.add(node_id)
                
                # Reduce in-degree of dependents
                for dependent in adj[node_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            
            level_num += 1
        
        # Check for orphaned nodes (shouldn't happen in cycle-free graph)
        all_nodes = {node.id for node in graph.nodes}
        unprocessed = all_nodes - processed
        
        if unprocessed:
            # These nodes have unmet dependencies - add as final level
            if unprocessed:
                levels.append(Level(
                    level=level_num,
                    files=list(unprocessed),
                    parallel=True,
                    status="pending",
                ))
        
        # Compute critical path
        critical_path = self._compute_critical_path(graph, levels)
        
        # Create Celery chord plan
        chord_plan = self._create_chord_plan(levels)
        
        # Create test plan
        test_plan = self._create_test_plan(levels, graph)
        
        # Count files
        total_files = sum(len(l.files) for l in levels)
        new_files = sum(
            1 for node in graph.nodes
            if node.type.value == "new" and node.id in all_nodes
        )
        
        return BuildPlan(
            id=f"buildplan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            requirement_spec_id="",  # Will be set by caller
            architecture_plan_id="",  # Will be set by caller
            dependency_graph_id=graph.id,
            levels=levels,
            celery_chord_plan=chord_plan,
            celery_chain_plan=[],
            test_plan=test_plan,
            total_files=total_files,
            total_new_files=new_files,
            total_modified_files=total_files - new_files,
            critical_path=critical_path,
            status="pending",
            created_at=datetime.utcnow(),
        )
    
    def _compute_critical_path(
        self,
        graph: DependencyGraph,
        levels: list[Level]
    ) -> list[str]:
        """
        Compute critical path through the graph.
        
        The critical path is the longest chain of dependencies.
        """
        if not levels:
            return []
        
        # Build reverse adjacency (dependencies point to dependents)
        adj = defaultdict(list)
        for edge in graph.edges:
            adj[edge.target].append(edge.source)
        
        # Find longest path using dynamic programming
        node_level = {}
        for level in levels:
            for node_id in level.files:
                node_level[node_id] = level.level
        
        # Start from nodes in level 0
        max_path = []
        
        def find_longest_path(node: str, path: list[str]) -> list[str]:
            current_path = path + [node]
            
            dependents = adj.get(node, [])
            if not dependents:
                return current_path
            
            longest = current_path
            for dep in dependents:
                candidate = find_longest_path(dep, current_path)
                if len(candidate) > len(longest):
                    longest = candidate
            
            return longest
        
        # Find longest path starting from any level-0 node
        for node_id in levels[0].files if levels else []:
            path = find_longest_path(node_id, [])
            if len(path) > len(max_path):
                max_path = path
        
        return max_path
    
    def _create_chord_plan(self, levels: list[Level]) -> list[ChordTask]:
        """Create Celery chord task specifications."""
        chord_plan = []
        
        for level in levels:
            chord_plan.append(ChordTask(
                group_tasks=level.files,
                callback_task=f"critic_level_{level.level}",
                level=level.level,
            ))
        
        return chord_plan
    
    def _create_test_plan(
        self,
        levels: list[Level],
        graph: DependencyGraph
    ) -> list[TestLevel]:
        """Create test plan mirroring code levels."""
        test_plan = []
        
        # Build node lookup
        node_lookup = {node.id: node for node in graph.nodes}
        
        for level in levels:
            test_level = TestLevel(
                level=level.level,
                code_files=level.files,
                test_files=[],  # Will be populated during test generation
                test_types=["contract", "acceptance", "regression"],
                status="pending",
            )
            test_plan.append(test_level)
        
        return test_plan
    
    def get_level_summary(self, build_plan: BuildPlan) -> dict:
        """
        Get summary of build plan levels.
        
        Args:
            build_plan: Build plan to summarize
        
        Returns:
            Summary dict
        """
        return {
            "total_levels": len(build_plan.levels),
            "total_files": build_plan.total_files,
            "new_files": build_plan.total_new_files,
            "modified_files": build_plan.total_modified_files,
            "critical_path_length": len(build_plan.critical_path),
            "critical_path": build_plan.critical_path,
            "levels": [
                {
                    "level": l.level,
                    "file_count": len(l.files),
                    "files": l.files,
                    "parallel": l.parallel,
                }
                for l in build_plan.levels
            ],
        }
    
    def format_build_order(self, build_plan: BuildPlan) -> str:
        """
        Format build order for human review.
        
        Args:
            build_plan: Build plan
        
        Returns:
            Formatted string
        """
        lines = [
            "BUILD ORDER (Topologically Sorted)",
            "=" * 50,
            f"Total levels: {len(build_plan.levels)}",
            f"Total files: {build_plan.total_files}",
            f"Critical path: {' → '.join(build_plan.critical_path[:5])}{'...' if len(build_plan.critical_path) > 5 else ''}",
            "",
        ]
        
        for level in build_plan.levels:
            lines.append(f"Level {level.level} (parallel):")
            for f in level.files:
                lines.append(f"  - {f}")
            lines.append("")
        
        return "\n".join(lines)
