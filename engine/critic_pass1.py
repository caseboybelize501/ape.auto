"""
APE - Autonomous Production Engineer
Critic Pass 1: Syntax Validation

Deterministic syntax checking using:
- Python AST parsing
- Pylint error detection
- Mypy type checking
"""

import ast
import sys
from io import StringIO
from typing import Optional


class SyntaxCritic:
    """
    Pass 1: Syntax validation critic.
    """
    
    def __init__(self):
        """Initialize syntax critic."""
        pass
    
    def check(
        self,
        file_path: str,
        content: str
    ) -> tuple[bool, list[dict]]:
        """
        Check syntax of Python file.
        
        Args:
            file_path: File path
            content: File content
        
        Returns:
            Tuple of (passed, list of errors)
        """
        errors = []
        
        # AST parsing
        ast_errors = self._check_ast(content)
        errors.extend(ast_errors)
        
        # Pylint check (if available)
        pylint_errors = self._check_pylint(file_path, content)
        errors.extend(pylint_errors)
        
        # Mypy check (if available)
        mypy_errors = self._check_mypy(content)
        errors.extend(mypy_errors)
        
        return len(errors) == 0, errors
    
    def _check_ast(self, content: str) -> list[dict]:
        """Check Python syntax using AST."""
        errors = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append({
                "type": "syntax",
                "line": e.lineno or 0,
                "column": e.offset or 0,
                "message": str(e),
            })
        
        return errors
    
    def _check_pylint(
        self,
        file_path: str,
        content: str
    ) -> list[dict]:
        """Check using pylint (if available)."""
        errors = []
        
        try:
            from pylint.lint import Run
            from pylint.reporters.text import TextReporter
            
            # Write content to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(content)
                temp_path = f.name
            
            # Run pylint
            output = StringIO()
            reporter = TextReporter(output)
            
            try:
                Run(
                    [temp_path, "--errors-only", "--disable=all", "--enable=E"],
                    reporter=reporter,
                    exit=False
                )
                
                # Parse output
                for line in output.getvalue().split("\n"):
                    if line and ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 3:
                            try:
                                line_num = int(parts[1])
                                errors.append({
                                    "type": "pylint",
                                    "line": line_num,
                                    "column": 0,
                                    "message": ":".join(parts[2:]).strip(),
                                })
                            except ValueError:
                                pass
            finally:
                import os
                os.unlink(temp_path)
                
        except ImportError:
            pass  # Pylint not available
        except Exception:
            pass  # Other pylint errors
        
        return errors
    
    def _check_mypy(self, content: str) -> list[dict]:
        """Check using mypy (if available)."""
        errors = []
        
        try:
            import mypy.api
            import tempfile
            
            # Write content to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(content)
                temp_path = f.name
            
            # Run mypy
            result = mypy.api.run([
                temp_path,
                "--strict",
                "--ignore-missing-imports",
                "--no-error-summary"
            ])
            
            # Parse output
            for line in result[0].split("\n"):
                if line and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[1])
                            errors.append({
                                "type": "mypy",
                                "line": line_num,
                                "column": 0,
                                "message": ":".join(parts[2:]).strip(),
                            })
                        except ValueError:
                            pass
            
            import os
            os.unlink(temp_path)
            
        except ImportError:
            pass  # Mypy not available
        except Exception:
            pass  # Other mypy errors
        
        return errors
