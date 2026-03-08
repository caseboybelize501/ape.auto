"""
APE - Autonomous Production Engineer
Codebase Graph Builder

Scans repository and builds complete dependency graph including:
- Module structure
- Import relationships
- Call graph
- Test coverage per module
- Dependency versions
- Change frequency
- CVE exposure
"""

import os
import ast
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import networkx as nx

from contracts.models.graph import (
    DependencyGraph,
    Node,
    Edge,
    EdgeType,
    NodeType,
    Complexity,
    CycleInfo,
)


class CodebaseGraphBuilder:
    """
    Builds and maintains codebase dependency graph.
    """
    
    # Python standard library modules (partial list for import detection)
    STD_LIBS = {
        "os", "sys", "re", "json", "datetime", "typing", "collections",
        "itertools", "functools", "pathlib", "hashlib", "logging",
        "unittest", "pytest", "asyncio", "concurrent", "threading",
        "multiprocessing", "socket", "http", "urllib", "email", "html",
        "xml", "csv", "sqlite3", "pickle", "shelve", "struct", "codecs",
        "io", "tempfile", "shutil", "glob", "fnmatch", "stat", "time",
        "calendar", "random", "statistics", "math", "decimal", "fractions",
        "copy", "pprint", "reprlib", "enum", "graphlib", "contextlib",
        "abc", "dataclasses", "warnings", "traceback", "inspect", "dis",
        "gc", "weakref", "types", "operator", "posixpath", "ntpath",
    }
    
    def __init__(self, repo_path: str):
        """
        Initialize codebase graph builder.
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        self._graph: Optional[nx.DiGraph] = None
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []
        self._import_cache: dict[str, set[str]] = {}
        self._test_coverage: dict[str, float] = {}
    
    def build(
        self,
        branch: str = "main",
        include_tests: bool = True
    ) -> DependencyGraph:
        """
        Build complete codebase graph.
        
        Args:
            branch: Branch to scan
            include_tests: Include test files
        
        Returns:
            Complete DependencyGraph
        """
        self._graph = nx.DiGraph()
        self._nodes = {}
        self._edges = []
        self._import_cache = {}
        
        # Find all Python files
        py_files = self._find_python_files(include_tests)
        
        # Parse each file
        for file_path in py_files:
            self._parse_file(file_path)
        
        # Build edges from imports
        self._build_edges()
        
        # Calculate test coverage
        if include_tests:
            self._calculate_test_coverage()
        
        # Calculate change frequency (if git available)
        self._calculate_change_frequency()
        
        # Build graph
        for node in self._nodes.values():
            self._graph.add_node(node.id, data=node)
        
        for edge in self._edges:
            self._graph.add_edge(edge.source, edge.target, data=edge)
        
        return self._to_dependency_graph()
    
    def _find_python_files(self, include_tests: bool = True) -> list[Path]:
        """Find all Python files in repository."""
        files = []
        
        # Directories to skip
        skip_dirs = {
            "__pycache__", ".git", ".venv", "venv", "env", "node_modules",
            ".tox", ".eggs", "*.egg-info", "build", "dist", ".mypy_cache",
            ".pytest_cache", ".coverage", "htmlcov",
        }
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            
            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = Path(root) / filename
                    
                    # Skip test files if not including tests
                    if not include_tests:
                        if "test" in file_path.name or "tests" in str(file_path):
                            continue
                    
                    files.append(file_path)
        
        return files
    
    def _parse_file(self, file_path: Path) -> None:
        """Parse a Python file and extract imports, functions, classes."""
        rel_path = str(file_path.relative_to(self.repo_path))
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        # Extract module info
        module_name = self._path_to_module(rel_path)
        
        # Extract imports
        imports = self._extract_imports(tree)
        self._import_cache[rel_path] = imports
        
        # Extract exports (functions, classes)
        exports = self._extract_exports(tree)
        
        # Estimate complexity
        complexity = self._estimate_complexity(tree, content)
        
        # Determine node type
        node_type = NodeType.UNTOUCHED  # Will be updated during generation
        
        # Create node
        node = Node(
            id=rel_path,
            type=node_type,
            module=module_name,
            language="python",
            exports=exports,
            imports=list(imports),
            estimated_complexity=complexity,
        )
        
        self._nodes[rel_path] = node
    
    def _path_to_module(self, path: str) -> str:
        """Convert file path to module name."""
        return path.replace("/", ".").replace("\\", ".")[:-3]
    
    def _extract_imports(self, tree: ast.AST) -> set[str]:
        """Extract all imports from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    if module not in self.STD_LIBS:
                        imports.add(module)
        
        return imports
    
    def _extract_exports(self, tree: ast.AST) -> list[str]:
        """Extract public exports (functions, classes) from AST."""
        exports = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                if not node.name.startswith("_"):
                    exports.append(f"def {node.name}")
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    exports.append(f"class {node.name}")
        
        return exports
    
    def _estimate_complexity(
        self,
        tree: ast.AST,
        content: str
    ) -> Complexity:
        """Estimate code complexity."""
        lines = len(content.split("\n"))
        
        # Count cyclomatic complexity indicators
        complexity_score = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity_score += 1
            elif isinstance(node, ast.BoolOp):
                complexity_score += len(node.values) - 1
        
        # Classify
        if lines < 100 and complexity_score < 5:
            return Complexity.LOW
        elif lines < 300 and complexity_score < 15:
            return Complexity.MEDIUM
        else:
            return Complexity.HIGH
    
    def _build_edges(self) -> None:
        """Build edges from import relationships."""
        # Build module to file mapping
        module_to_file: dict[str, str] = {}
        for path, node in self._nodes.items():
            module_to_file[node.module] = path
            # Also map short name
            short_name = node.module.split(".")[-1]
            if short_name not in module_to_file:
                module_to_file[short_name] = path
        
        # Create edges
        for path, imports in self._import_cache.items():
            for imp in imports:
                if imp in module_to_file:
                    target = module_to_file[imp]
                    if target != path:  # No self-loops
                        self._edges.append(Edge(
                            source=path,
                            target=target,
                            type=EdgeType.IMPORTS,
                        ))
    
    def _calculate_test_coverage(self) -> None:
        """Calculate test coverage per module."""
        # Find test files
        test_files = []
        for path in self._nodes:
            if "test" in path.lower():
                test_files.append(path)
        
        # Simple heuristic: check if module has corresponding test
        for path, node in self._nodes.items():
            if "test" in path.lower():
                continue  # Skip test files themselves
            
            # Look for test file
            base_name = Path(path).stem
            has_test = any(
                f"test_{base_name}.py" in tf or f"{base_name}_test.py" in tf
                for tf in test_files
            )
            
            self._test_coverage[path] = 100.0 if has_test else 0.0
            node.test_coverage = self._test_coverage[path]
    
    def _calculate_change_frequency(self) -> None:
        """Calculate change frequency from git history."""
        try:
            import subprocess
            
            for path in self._nodes:
                try:
                    result = subprocess.run(
                        ["git", "log", "--oneline", "--", path],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        lines = [l for l in result.stdout.split("\n") if l.strip()]
                        commit_count = len(lines)
                        
                        # Classify frequency
                        if commit_count > 20:
                            self._nodes[path].change_frequency = "high"
                        elif commit_count > 5:
                            self._nodes[path].change_frequency = "medium"
                        else:
                            self._nodes[path].change_frequency = "low"
                except Exception:
                    pass
        except Exception:
            pass
    
    def _to_dependency_graph(self) -> DependencyGraph:
        """Convert internal representation to DependencyGraph."""
        return DependencyGraph(
            id=f"graph-{datetime.utcnow().isoformat()}",
            repo_id=str(self.repo_path),
            nodes=list(self._nodes.values()),
            edges=self._edges,
            cycle_free=True,  # Will be updated by cycle detector
            generated_at=datetime.utcnow(),
        )
    
    def update_incremental(
        self,
        existing_graph: DependencyGraph,
        changed_files: list[str]
    ) -> DependencyGraph:
        """
        Update graph with incremental changes.
        
        Args:
            existing_graph: Existing graph
            changed_files: List of changed file paths
        
        Returns:
            Updated DependencyGraph
        """
        # Start with existing graph
        self._nodes = {n.id: n for n in existing_graph.nodes}
        self._edges = list(existing_graph.edges)
        self._graph = nx.DiGraph()
        
        for node in existing_graph.nodes:
            self._graph.add_node(node.id, data=node)
        for edge in existing_graph.edges:
            self._graph.add_edge(edge.source, edge.target, data=edge)
        
        # Re-parse changed files
        for file_path in changed_files:
            full_path = self.repo_path / file_path
            if full_path.exists():
                self._parse_file(full_path)
        
        # Rebuild edges for changed files
        self._build_edges()
        
        return self._to_dependency_graph()
    
    def get_node(self, path: str) -> Optional[Node]:
        """Get node by path."""
        return self._nodes.get(path)
    
    def get_dependencies(self, path: str) -> list[str]:
        """Get dependencies of a file."""
        if self._graph is None:
            return []
        return list(self._graph.successors(path))
    
    def get_dependents(self, path: str) -> list[str]:
        """Get files that depend on this file."""
        if self._graph is None:
            return []
        return list(self._graph.predecessors(path))
    
    def compute_snapshot_hash(self) -> str:
        """Compute hash of current codebase state."""
        hasher = hashlib.sha256()
        
        for path in sorted(self._nodes.keys()):
            hasher.update(path.encode())
            node = self._nodes[path]
            hasher.update(",".join(node.exports).encode())
            hasher.update(",".join(node.imports).encode())
        
        return hasher.hexdigest()
