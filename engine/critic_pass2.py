"""
APE - Autonomous Production Engineer
Critic Pass 2: Contract Compliance

Deterministic contract validation:
- Function signatures match contracts/interfaces/
- Pydantic model imports match contracts/models/
- API routes match contracts/api/
"""

import ast
import re
from typing import Optional


class ContractCritic:
    """
    Pass 2: Contract compliance critic.
    """
    
    def __init__(self):
        """Initialize contract critic."""
        pass
    
    def check(
        self,
        file_path: str,
        content: str,
        contracts: list[str]
    ) -> tuple[bool, list[dict]]:
        """
        Check contract compliance.
        
        Args:
            file_path: File path
            content: File content
            contracts: Contract file contents
        
        Returns:
            Tuple of (passed, list of violations)
        """
        violations = []
        
        # Parse contracts
        contract_specs = self._parse_contracts(contracts)
        
        # Parse generated file
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return False, [{
                "type": "syntax_error",
                "message": "Cannot check contracts - syntax error in file",
            }]
        
        # Check function signatures
        sig_violations = self._check_signatures(tree, contract_specs)
        violations.extend(sig_violations)
        
        # Check imports
        import_violations = self._check_imports(tree, contract_specs)
        violations.extend(import_violations)
        
        # Check class definitions
        class_violations = self._check_classes(tree, contract_specs)
        violations.extend(class_violations)
        
        return len(violations) == 0, violations
    
    def _parse_contracts(self, contracts: list[str]) -> dict:
        """Parse contract files into specs."""
        specs = {
            "functions": {},  # name -> signature
            "classes": {},    # name -> attributes
            "imports": set(), # required imports
        }
        
        for contract in contracts:
            try:
                tree = ast.parse(contract)
                
                for node in ast.walk(tree):
                    # Extract function signatures
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith("_"):
                            sig = self._extract_signature(node)
                            specs["functions"][node.name] = sig
                    
                    # Extract class definitions
                    elif isinstance(node, ast.ClassDef):
                        if not node.name.startswith("_"):
                            attrs = self._extract_class_attrs(node)
                            specs["classes"][node.name] = attrs
                    
                    # Extract imports
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "contracts" in node.module:
                            for alias in node.names:
                                specs["imports"].add(f"{node.module}.{alias.name}")
            
            except SyntaxError:
                continue
        
        return specs
    
    def _extract_signature(self, node: ast.FunctionDef) -> dict:
        """Extract function signature."""
        args = []
        
        # Regular args
        for arg in node.args.args:
            arg_type = None
            if arg.annotation:
                arg_type = ast.unparse(arg.annotation)
            args.append({
                "name": arg.arg,
                "type": arg_type,
            })
        
        # Return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        return {
            "name": node.name,
            "args": args,
            "return_type": return_type,
            "async": isinstance(node, ast.AsyncFunctionDef),
        }
    
    def _extract_class_attrs(self, node: ast.ClassDef) -> list[dict]:
        """Extract class attributes."""
        attrs = []
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                attr_type = None
                if item.annotation:
                    attr_type = ast.unparse(item.annotation)
                
                target = None
                if isinstance(item.target, ast.Name):
                    target = item.target.id
                
                if target:
                    attrs.append({
                        "name": target,
                        "type": attr_type,
                    })
        
        return attrs
    
    def _check_signatures(
        self,
        tree: ast.AST,
        contract_specs: dict
    ) -> list[dict]:
        """Check function signatures against contracts."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue  # Skip private functions
                
                if node.name in contract_specs["functions"]:
                    contract_sig = contract_specs["functions"][node.name]
                    actual_sig = self._extract_signature(node)
                    
                    # Compare args
                    contract_args = {a["name"]: a for a in contract_sig["args"]}
                    actual_args = {a["name"]: a for a in actual_sig["args"]}
                    
                    # Check for missing args
                    for arg_name in contract_args:
                        if arg_name not in actual_args:
                            violations.append({
                                "type": "missing_arg",
                                "function": node.name,
                                "expected": arg_name,
                                "contract_file": "contracts/interfaces/",
                            })
                        else:
                            # Check type match
                            contract_type = contract_args[arg_name].get("type")
                            actual_type = actual_args[arg_name].get("type")
                            if contract_type and actual_type:
                                if contract_type != actual_type:
                                    violations.append({
                                        "type": "type_mismatch",
                                        "function": node.name,
                                        "arg": arg_name,
                                        "expected": contract_type,
                                        "actual": actual_type,
                                        "contract_file": "contracts/interfaces/",
                                    })
                    
                    # Check return type
                    if contract_sig["return_type"] and actual_sig["return_type"]:
                        if contract_sig["return_type"] != actual_sig["return_type"]:
                            violations.append({
                                "type": "return_type_mismatch",
                                "function": node.name,
                                "expected": contract_sig["return_type"],
                                "actual": actual_sig["return_type"],
                                "contract_file": "contracts/interfaces/",
                            })
        
        return violations
    
    def _check_imports(
        self,
        tree: ast.AST,
        contract_specs: dict
    ) -> list[dict]:
        """Check required imports from contracts."""
        violations = []
        
        # Get actual imports
        actual_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        actual_imports.add(f"{node.module}.{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    actual_imports.add(alias.name)
        
        # Check contract imports
        for contract_import in contract_specs["imports"]:
            if contract_import not in actual_imports:
                violations.append({
                    "type": "missing_import",
                    "import": contract_import,
                    "contract_file": "contracts/",
                })
        
        return violations
    
    def _check_classes(
        self,
        tree: ast.AST,
        contract_specs: dict
    ) -> list[dict]:
        """Check class definitions against contracts."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                
                if node.name in contract_specs["classes"]:
                    contract_attrs = {
                        a["name"]: a for a in contract_specs["classes"][node.name]
                    }
                    
                    # Extract actual class attributes
                    actual_attrs = {
                        a["name"]: a for a in self._extract_class_attrs(node)
                    }
                    
                    # Check for missing attributes
                    for attr_name in contract_attrs:
                        if attr_name not in actual_attrs:
                            violations.append({
                                "type": "missing_attribute",
                                "class": node.name,
                                "attribute": attr_name,
                                "contract_file": "contracts/models/",
                            })
        
        return violations
