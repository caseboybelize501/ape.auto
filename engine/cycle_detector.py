"""
APE - Autonomous Production Engineer
Cycle Detector

Detects cycles in dependency graph using DFS:
- Identifies circular dependencies
- Suggests break points
- Generates cycle reports for architectural review
"""

from typing import Optional
from collections import defaultdict

from contracts.models.graph import DependencyGraph, CycleInfo, Edge


class CycleDetector:
    """
    Detects cycles in dependency graphs.
    """
    
    def __init__(self):
        """Initialize cycle detector."""
        pass
    
    def detect(self, graph: DependencyGraph) -> tuple[bool, list[CycleInfo]]:
        """
        Detect cycles in dependency graph using DFS.
        
        Args:
            graph: Dependency graph to check
        
        Returns:
            Tuple of (cycle_free, list of cycle info)
        """
        # Build adjacency list
        adj = defaultdict(list)
        for edge in graph.edges:
            adj[edge.source].append(edge.target)
        
        # Track visited states
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node.id: WHITE for node in graph.nodes}
        parent = {node.id: None for node in graph.nodes}
        
        cycles = []
        
        def dfs(node: str, path: list[str]) -> None:
            """DFS to detect back edges (cycles)."""
            color[node] = GRAY
            
            for neighbor in adj[node]:
                if neighbor not in color:
                    continue
                
                if color[neighbor] == GRAY:
                    # Found back edge - cycle detected
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle_path = path[cycle_start:] + [neighbor]
                    
                    # Build cycle edges
                    cycle_edges = []
                    for i in range(len(cycle_path) - 1):
                        cycle_edges.append((cycle_path[i], cycle_path[i + 1]))
                    
                    # Suggest break point
                    suggested_break = self._suggest_break(cycle_path)
                    
                    cycles.append(CycleInfo(
                        cycle_path=cycle_path,
                        edges=cycle_edges,
                        suggested_break=suggested_break,
                        severity=self._assess_cycle_severity(cycle_path, graph),
                    ))
                
                elif color[neighbor] == WHITE:
                    parent[neighbor] = node
                    dfs(neighbor, path + [neighbor])
            
            color[node] = BLACK
        
        # Run DFS from each unvisited node
        for node in graph.nodes:
            if color[node.id] == WHITE:
                dfs(node.id, [node.id])
        
        cycle_free = len(cycles) == 0
        
        # Update graph cycle status
        graph.cycle_free = cycle_free
        graph.cycles = cycles
        
        return cycle_free, cycles
    
    def _suggest_break(self, cycle_path: list[str]) -> str:
        """
        Suggest where to break the cycle.
        
        Strategy: Find the edge where introducing an interface
        or dependency injection would be least disruptive.
        """
        if len(cycle_path) < 2:
            return "Cannot determine break point - cycle too short"
        
        # Prefer breaking at test files or interface modules
        for i, node in enumerate(cycle_path[:-1]):
            if "interface" in node.lower() or "abc" in node.lower():
                return f"Break edge between {cycle_path[i]} and {cycle_path[i+1]} - appears to be interface module"
            if "test" in node.lower():
                return f"Break edge between {cycle_path[i]} and {cycle_path[i+1]} - test file should not create cycle"
        
        # Default: suggest breaking at the module with fewest dependents
        # (would need graph analysis, simplified here)
        return f"Break edge between {cycle_path[0]} and {cycle_path[1]} - consider introducing abstraction or dependency injection"
    
    def _assess_cycle_severity(
        self,
        cycle_path: list[str],
        graph: DependencyGraph
    ) -> str:
        """Assess severity of detected cycle."""
        # Count nodes in cycle
        cycle_length = len(cycle_path) - 1  # Exclude repeated start node
        
        # Check if cycle involves many files
        if cycle_length >= 5:
            return "high"
        
        # Check if cycle involves core modules
        core_indicators = ["core", "main", "app", "service", "model"]
        involves_core = any(
            any(ind in node.lower() for ind in core_indicators)
            for node in cycle_path
        )
        
        if involves_core:
            return "high"
        
        # Check if cycle is between test and source
        has_test = any("test" in node.lower() for node in cycle_path)
        if has_test:
            return "medium"  # Test cycles are less critical
        
        return "medium" if cycle_length >= 3 else "low"
    
    def get_cycle_summary(self, graph: DependencyGraph) -> dict:
        """
        Get summary of all cycles in graph.
        
        Args:
            graph: Dependency graph
        
        Returns:
            Cycle summary dict
        """
        cycle_free, cycles = self.detect(graph)
        
        if cycle_free:
            return {
                "cycle_free": True,
                "total_cycles": 0,
                "cycles": [],
            }
        
        return {
            "cycle_free": False,
            "total_cycles": len(cycles),
            "by_severity": {
                "high": len([c for c in cycles if c.severity == "high"]),
                "medium": len([c for c in cycles if c.severity == "medium"]),
                "low": len([c for c in cycles if c.severity == "low"]),
            },
            "cycles": [
                {
                    "path": c.cycle_path,
                    "suggested_break": c.suggested_break,
                    "severity": c.severity,
                }
                for c in cycles
            ],
        }
    
    def format_cycle_report(self, graph: DependencyGraph) -> str:
        """
        Format cycle detection report for human review.
        
        Args:
            graph: Dependency graph
        
        Returns:
            Formatted report string
        """
        cycle_free, cycles = self.detect(graph)
        
        if cycle_free:
            return "✅ No cycles detected - dependency graph is valid"
        
        lines = [
            "❌ CYCLE DETECTED",
            "=" * 50,
            f"Total cycles found: {len(cycles)}",
            "",
        ]
        
        for i, cycle in enumerate(cycles, 1):
            lines.extend([
                f"Cycle {i} (Severity: {cycle.severity.upper()})",
                "-" * 30,
                "Dependency chain:",
            ])
            
            for j, node in enumerate(cycle.cycle_path):
                arrow = " → " if j < len(cycle.cycle_path) - 1 else " (back to start)"
                lines.append(f"  {node}{arrow}")
            
            lines.extend([
                "",
                f"Suggested break: {cycle.suggested_break}",
                "",
            ])
        
        return "\n".join(lines)
