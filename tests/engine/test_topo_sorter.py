"""
APE - Autonomous Production Engineer
Unit Tests for Topological Sorter

Tests for engine/topo_sorter.py
"""

import pytest

from engine.topo_sorter import TopologicalSorter
from contracts.models.graph import (
    DependencyGraph,
    Node,
    Edge,
    EdgeType,
    NodeType,
)


class TestTopologicalSorter:
    """Tests for TopologicalSorter."""
    
    @pytest.fixture
    def simple_graph(self):
        """Create a simple dependency graph."""
        return DependencyGraph(
            id="test-graph",
            repo_id="test/repo",
            nodes=[
                Node(id="a.py", module="a", type=NodeType.NEW, exports=[], imports=[]),
                Node(id="b.py", module="b", type=NodeType.NEW, exports=[], imports=["a"]),
                Node(id="c.py", module="c", type=NodeType.NEW, exports=[], imports=["a"]),
                Node(id="d.py", module="d", type=NodeType.NEW, exports=[], imports=["b", "c"]),
            ],
            edges=[
                Edge(source="b.py", target="a.py", type=EdgeType.IMPORTS),
                Edge(source="c.py", target="a.py", type=EdgeType.IMPORTS),
                Edge(source="d.py", target="b.py", type=EdgeType.IMPORTS),
                Edge(source="d.py", target="c.py", type=EdgeType.IMPORTS),
            ],
            cycle_free=True,
        )
    
    @pytest.fixture
    def cyclic_graph(self):
        """Create a graph with a cycle."""
        return DependencyGraph(
            id="cyclic-graph",
            repo_id="test/repo",
            nodes=[
                Node(id="a.py", module="a", type=NodeType.NEW, exports=[], imports=["b"]),
                Node(id="b.py", module="b", type=NodeType.NEW, exports=[], imports=["a"]),
            ],
            edges=[
                Edge(source="a.py", target="b.py", type=EdgeType.IMPORTS),
                Edge(source="b.py", target="a.py", type=EdgeType.IMPORTS),
            ],
            cycle_free=False,
        )
    
    def test_sort_simple(self, simple_graph):
        """Test topological sort on simple graph."""
        sorter = TopologicalSorter()
        build_plan = sorter.sort(simple_graph)
        
        assert build_plan is not None
        assert len(build_plan.levels) > 0
        
        # Level 0 should have 'a.py' (no dependencies)
        level_0_files = build_plan.levels[0].files
        assert "a.py" in level_0_files
        
        # 'd.py' should be in a later level than 'b.py' and 'c.py'
        d_level = None
        b_level = None
        c_level = None
        
        for level in build_plan.levels:
            if "d.py" in level.files:
                d_level = level.level
            if "b.py" in level.files:
                b_level = level.level
            if "c.py" in level.files:
                c_level = level.level
        
        assert d_level is not None
        assert b_level is not None
        assert c_level is not None
        assert d_level > b_level
        assert d_level > c_level
    
    def test_sort_raises_on_cycle(self, cyclic_graph):
        """Test that sort raises on cyclic graph."""
        sorter = TopologicalSorter()
        
        with pytest.raises(ValueError, match="cycle"):
            sorter.sort(cyclic_graph)
    
    def test_critical_path(self, simple_graph):
        """Test critical path computation."""
        sorter = TopologicalSorter()
        build_plan = sorter.sort(simple_graph)
        
        assert len(build_plan.critical_path) > 0
        assert "a.py" in build_plan.critical_path
        assert "d.py" in build_plan.critical_path
    
    def test_parallel_levels(self, simple_graph):
        """Test that files in same level are parallel-safe."""
        sorter = TopologicalSorter()
        build_plan = sorter.sort(simple_graph)
        
        for level in build_plan.levels:
            assert level.parallel is True
    
    def test_get_level_summary(self, simple_graph):
        """Test level summary generation."""
        sorter = TopologicalSorter()
        build_plan = sorter.sort(simple_graph)
        
        summary = sorter.get_level_summary(build_plan)
        
        assert summary["total_levels"] > 0
        assert summary["total_files"] == 4
        assert "levels" in summary
    
    def test_format_build_order(self, simple_graph):
        """Test build order formatting."""
        sorter = TopologicalSorter()
        build_plan = sorter.sort(simple_graph)
        
        output = sorter.format_build_order(build_plan)
        
        assert "BUILD ORDER" in output
        assert "Level" in output
        assert "a.py" in output
