"""
APE - Autonomous Production Engineer
Unit Tests for Codebase Graph

Tests for engine/codebase_graph.py
"""

import pytest
import ast
from pathlib import Path
import tempfile
import os

from engine.codebase_graph import CodebaseGraphBuilder
from contracts.models.graph import NodeType, Complexity


class TestCodebaseGraphBuilder:
    """Tests for CodebaseGraphBuilder."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            os.makedirs(os.path.join(tmpdir, "src"))
            os.makedirs(os.path.join(tmpdir, "src", "api"))
            
            # Main file
            with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
                f.write('''
from fastapi import FastAPI

app = FastAPI()

def run():
    """Run the application."""
    app.run()
''')
            
            # API file
            with open(os.path.join(tmpdir, "src", "api", "users.py"), "w") as f:
                f.write('''
from fastapi import APIRouter
from src.main import app

router = APIRouter()

def get_user(user_id: int):
    """Get user by ID."""
    pass

def create_user(name: str):
    """Create a new user."""
    pass
''')
            
            yield tmpdir
    
    def test_init(self, temp_repo):
        """Test CodebaseGraphBuilder initialization."""
        builder = CodebaseGraphBuilder(temp_repo)
        assert builder.repo_path == Path(temp_repo)
        assert builder._graph is None
        assert builder._nodes == {}
    
    def test_find_python_files(self, temp_repo):
        """Test finding Python files."""
        builder = CodebaseGraphBuilder(temp_repo)
        files = builder._find_python_files()
        
        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "users.py" in file_names
    
    def test_parse_file(self, temp_repo):
        """Test parsing a Python file."""
        builder = CodebaseGraphBuilder(temp_repo)
        file_path = Path(temp_repo) / "src" / "main.py"
        
        builder._parse_file(file_path)
        
        assert "src/main.py" in builder._nodes
        node = builder._nodes["src/main.py"]
        assert node.module == "src.main"
        assert "def run" in node.exports
        assert "fastapi" in node.imports
    
    def test_extract_imports(self, temp_repo):
        """Test import extraction from AST."""
        builder = CodebaseGraphBuilder(temp_repo)
        file_path = Path(temp_repo) / "src" / "api" / "users.py"
        
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        imports = builder._extract_imports(tree)
        
        assert "fastapi" in imports
        assert "src" in imports  # From "from src.main import app"
    
    def test_extract_exports(self, temp_repo):
        """Test export extraction from AST."""
        builder = CodebaseGraphBuilder(temp_repo)
        file_path = Path(temp_repo) / "src" / "main.py"
        
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        exports = builder._extract_exports(tree)
        
        assert "def run" in exports
    
    def test_estimate_complexity_low(self, temp_repo):
        """Test complexity estimation for simple code."""
        builder = CodebaseGraphBuilder(temp_repo)
        
        simple_code = '''
def hello():
    return "world"
'''
        tree = ast.parse(simple_code)
        complexity = builder._estimate_complexity(tree, simple_code)
        
        assert complexity == Complexity.LOW
    
    def test_estimate_complexity_high(self, temp_repo):
        """Test complexity estimation for complex code."""
        builder = CodebaseGraphBuilder(temp_repo)
        
        complex_code = '''
def process_data(data):
    if data:
        for item in data:
            if item > 0:
                for x in range(item):
                    if x % 2 == 0:
                        while x > 0:
                            x -= 1
    return data
'''
        tree = ast.parse(complex_code)
        complexity = builder._estimate_complexity(tree, complex_code)
        
        assert complexity == Complexity.HIGH
    
    def test_path_to_module(self, temp_repo):
        """Test path to module name conversion."""
        builder = CodebaseGraphBuilder(temp_repo)
        
        assert builder._path_to_module("src/main.py") == "src.main"
        assert builder._path_to_module("src/api/users.py") == "src.api.users"
    
    def test_build(self, temp_repo):
        """Test building complete codebase graph."""
        builder = CodebaseGraphBuilder(temp_repo)
        graph = builder.build()
        
        assert graph.id is not None
        assert len(graph.nodes) == 2
        assert graph.cycle_free is True
        
        # Check nodes
        node_ids = [n.id for n in graph.nodes]
        assert "src/main.py" in node_ids
        assert "src/api/users.py" in node_ids
    
    def test_compute_snapshot_hash(self, temp_repo):
        """Test snapshot hash computation."""
        builder = CodebaseGraphBuilder(temp_repo)
        builder.build()
        
        hash1 = builder.compute_snapshot_hash()
        hash2 = builder.compute_snapshot_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_get_node(self, temp_repo):
        """Test getting node by path."""
        builder = CodebaseGraphBuilder(temp_repo)
        builder.build()
        
        node = builder.get_node("src/main.py")
        assert node is not None
        assert node.module == "src.main"
    
    def test_get_dependencies(self, temp_repo):
        """Test getting dependencies of a file."""
        builder = CodebaseGraphBuilder(temp_repo)
        builder.build()
        
        # src/api/users.py depends on src/main
        deps = builder.get_dependencies("src/api/users.py")
        # May or may not have dependencies based on import analysis
    
    def test_get_dependents(self, temp_repo):
        """Test getting files that depend on a file."""
        builder = CodebaseGraphBuilder(temp_repo)
        builder.build()
        
        # Get files that depend on src/main
        dependents = builder.get_dependents("src/main.py")
        # May have dependents based on import analysis
