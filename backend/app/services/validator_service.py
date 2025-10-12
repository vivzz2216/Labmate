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
    
    def validate_code(self, code: str, language: str = "python") -> Tuple[bool, str]:
        """
        Validate code for safety based on language
        
        Args:
            code: Code to validate
            language: Programming language ('python', 'java', 'c', 'webdev')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        # Check code length
        if len(code) > settings.MAX_CODE_LENGTH:
            return False, f"Code too long. Maximum {settings.MAX_CODE_LENGTH} characters allowed."
        
        # For web development, use different validation
        if language == "webdev":
            return self._validate_web_code(code)
        
        # For other languages, use Python validation (can be extended later)
        return self._validate_python_code(code)
    
    def _validate_web_code(self, code: str) -> Tuple[bool, str]:
        """Validate web development code (HTML/CSS/JS) - Educational Focus"""
        
        # Basic web code validation
        if not code.strip():
            return False, "Empty code"
        
        # Check code length
        if len(code) > settings.MAX_CODE_LENGTH:
            return False, f"Code too long. Maximum {settings.MAX_CODE_LENGTH} characters allowed."
        
        # Only check for extremely dangerous patterns that could cause real harm
        # Be more permissive for educational web development
        extremely_dangerous_patterns = [
            r'<script[^>]*>.*eval\s*\(',  # eval in script tags
            r'<script[^>]*>.*document\.cookie.*=',  # cookie manipulation
            r'<script[^>]*>.*window\.location\.href\s*=',  # forced page redirection
            r'<script[^>]*>.*XMLHttpRequest.*open.*http',  # external HTTP requests
            r'<iframe[^>]*src\s*=\s*["\']http',  # external iframe embedding
            r'<object[^>]*data\s*=\s*["\']http',  # external object embedding
            r'<embed[^>]*src\s*=\s*["\']http',  # external embed tags
            r'javascript:\s*void',  # javascript: void URLs
            r'data:text/html.*base64',  # data URLs with base64 HTML
        ]
        
        for pattern in extremely_dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                return False, f"Extremely dangerous web code detected"
        
        # For educational purposes, be very permissive
        # Accept any code that looks like web development
        
        # HTML indicators
        html_indicators = ['<html', '<head', '<body', '<div', '<p', '<h1', '<h2', '<h3', '<h4', '<h5', '<h6', 
                          '<span', '<a', '<img', '<ul', '<ol', '<li', '<table', '<tr', '<td', '<th', 
                          '<form', '<input', '<button', '<select', '<option', '<textarea', '<label']
        
        # CSS indicators
        css_indicators = ['color:', 'background:', 'margin:', 'padding:', 'font-', 'border:', 'width:', 'height:', 
                         'display:', 'position:', 'float:', 'text-align:', 'font-size:', 'font-weight:']
        
        # JavaScript indicators
        js_indicators = ['function', 'var ', 'let ', 'const ', 'if (', 'for (', 'while (', 'return', 'alert(', 
                        'console.log', 'document.', 'window.', 'addEventListener', 'onclick', 'onload']
        
        # Check if code contains any web development indicators
        code_lower = code.lower()
        
        has_html = any(indicator in code_lower for indicator in html_indicators)
        has_css = any(indicator in code_lower for indicator in css_indicators)
        has_js = any(indicator in code_lower for indicator in js_indicators)
        
        # If it has any web development characteristics, accept it
        if has_html or has_css or has_js:
            return True, ""
        
        # Even if it doesn't match patterns, be permissive for educational content
        # Accept any non-empty code that might be web-related
        return True, ""
    
    def _validate_python_code(self, code: str) -> Tuple[bool, str]:
        """Validate Python code for safety"""
        
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
