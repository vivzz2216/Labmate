import ast
import re
from typing import Tuple, List
from ..config import settings


class ValidatorService:
    """Service for validating Python code safety"""
    
    def __init__(self):
        # Dangerous imports to block
        self.blocked_imports = {
            'os', 'subprocess', 'sys', 'socket', 'pathlib', 'shutil', 
            'eval', 'exec', 'compile', '__import__', 'glob', 'tempfile',
            'urllib', 'requests', 'http', 'ftplib', 'smtplib',
            'pickle', 'marshal', 'ctypes', 'multiprocessing'
        }
        
        # Dangerous function calls to block
        self.blocked_functions = {
            'open', 'file', 'input', 'raw_input', 'exit', 'quit',
            'help', 'dir', 'vars', 'locals', 'globals'
        }
        
        # Dangerous attributes to block
        self.blocked_attributes = {
            '__import__', '__globals__', '__locals__', '__code__',
            '__func__', '__self__', '__class__', '__bases__',
            '__subclasses__', '__mro__', '__dict__'
        }
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """
        Validate Python code for safety
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        # Check code length
        if len(code) > settings.MAX_CODE_LENGTH:
            return False, f"Code too long. Maximum {settings.MAX_CODE_LENGTH} characters allowed."
        
        # Parse the code into AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        # Validate the AST
        is_valid, error_msg = self._validate_ast(tree)
        if not is_valid:
            return False, error_msg
        
        # Additional string-based checks for edge cases
        is_valid, error_msg = self._validate_strings(code)
        if not is_valid:
            return False, error_msg
        
        return True, ""
    
    
    def _validate_ast(self, tree: ast.AST) -> Tuple[bool, str]:
        """Validate AST nodes recursively"""
        
        for node in ast.walk(tree):
            # Check import statements
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.blocked_imports:
                            return False, f"Dangerous import blocked: {alias.name}"
                        if alias.name.split('.')[0] in self.blocked_imports:
                            return False, f"Dangerous import blocked: {alias.name}"
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in self.blocked_imports:
                        return False, f"Dangerous import blocked: {node.module}"
                    
                    for alias in node.names:
                        if alias.name in self.blocked_imports:
                            return False, f"Dangerous import blocked: {alias.name}"
            
            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.blocked_functions:
                        return False, f"Dangerous function call blocked: {node.func.id}"
                
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.blocked_attributes:
                        return False, f"Dangerous attribute access blocked: {node.func.attr}"
            
            # Check attribute access
            elif isinstance(node, ast.Attribute):
                if node.attr in self.blocked_attributes:
                    return False, f"Dangerous attribute access blocked: {node.attr}"
            
            # Check for eval, exec, compile calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        return False, f"Dangerous function blocked: {node.func.id}"
        
        return True, ""
    
    def _validate_strings(self, code: str) -> Tuple[bool, str]:
        """Additional string-based validation for edge cases"""
        
        # Check for file operations in strings
        file_operations = [
            r'open\s*\(', r'file\s*\(', r'\.write\s*\(', r'\.read\s*\(',
            r'\.append\s*\(', r'\.writelines\s*\('
        ]
        
        for pattern in file_operations:
            if re.search(pattern, code, re.IGNORECASE):
                return False, "File operations are not allowed"
        
        # Check for system commands
        system_commands = [
            r'os\.system', r'subprocess\.', r'\.popen', r'\.call',
            r'\.run\s*\(', r'\.check_output'
        ]
        
        for pattern in system_commands:
            if re.search(pattern, code, re.IGNORECASE):
                return False, "System command execution is not allowed"
        
        # Check for network operations
        network_operations = [
            r'urllib', r'requests\.', r'socket\.', r'http\.',
            r'ftplib', r'smtplib'
        ]
        
        for pattern in network_operations:
            if re.search(pattern, code, re.IGNORECASE):
                return False, "Network operations are not allowed"
        
        return True, ""
    
    def get_allowed_imports(self) -> List[str]:
        """Get list of commonly allowed imports for educational purposes"""
        return [
            'math', 'random', 'datetime', 'time', 'collections',
            'itertools', 'functools', 'operator', 'string',
            'decimal', 'fractions', 'statistics', 'json',
            'csv', 're', 'sys', 'builtins'
        ]


# Global instance
validator_service = ValidatorService()
