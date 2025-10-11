import os
import re
from typing import List, Dict, Any
from docx import Document
import pdfplumber
from ..config import settings


class ParserService:
    """Service for parsing DOCX and PDF files to extract code blocks and tasks"""
    
    def __init__(self):
        self.screenshot_keywords = [
            "screenshot", "output", "run this code", "execute", 
            "show output", "capture", "display result", "print result"
        ]
    
    async def parse_file(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """Parse uploaded file and extract tasks with code blocks"""
        
        if file_type.lower() == 'docx':
            return await self._parse_docx(file_path)
        elif file_type.lower() == 'pdf':
            return await self._parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _parse_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse DOCX file and extract tasks"""
        doc = Document(file_path)
        tasks = []
        current_task = None
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            
            # Check if this paragraph indicates a screenshot requirement
            requires_screenshot = any(
                keyword.lower() in text.lower() 
                for keyword in self.screenshot_keywords
            )
            
            # Check if this looks like a question/task
            if self._is_question(text):
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)
                
                # Start new task
                current_task = {
                    "question_text": text,
                    "code_snippet": "",
                    "requires_screenshot": requires_screenshot
                }
            
            # Check if this looks like code
            elif self._is_code(text):
                if current_task:
                    # Append to existing code snippet
                    if current_task["code_snippet"]:
                        current_task["code_snippet"] += "\n" + text
                    else:
                        current_task["code_snippet"] = text
                else:
                    # Create new task with just code
                    current_task = {
                        "question_text": f"Code block {len(tasks) + 1}",
                        "code_snippet": text,
                        "requires_screenshot": requires_screenshot
                    }
            
            # Check if this is a continuation of a question
            elif current_task and not self._is_code(text) and len(text) > 10:
                current_task["question_text"] += " " + text
        
        # Add final task
        if current_task:
            tasks.append(current_task)
        
        # Add task IDs
        for i, task in enumerate(tasks):
            task["id"] = i + 1
        
        return tasks
    
    async def _parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse PDF file and extract tasks"""
        tasks = []
        current_task = None
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this line indicates a screenshot requirement
                    requires_screenshot = any(
                        keyword.lower() in line.lower() 
                        for keyword in self.screenshot_keywords
                    )
                    
                    # Check if this looks like a question/task
                    if self._is_question(line):
                        # Save previous task if exists
                        if current_task:
                            tasks.append(current_task)
                        
                        # Start new task
                        current_task = {
                            "question_text": line,
                            "code_snippet": "",
                            "requires_screenshot": requires_screenshot
                        }
                    
                    # Check if this looks like code
                    elif self._is_code(line):
                        if current_task:
                            # Append to existing code snippet
                            if current_task["code_snippet"]:
                                current_task["code_snippet"] += "\n" + line
                            else:
                                current_task["code_snippet"] = line
                        else:
                            # Create new task with just code
                            current_task = {
                                "question_text": f"Code block {len(tasks) + 1}",
                                "code_snippet": line,
                                "requires_screenshot": requires_screenshot
                            }
                    
                    # Check if this is a continuation of a question
                    elif current_task and not self._is_code(line) and len(line) > 10:
                        current_task["question_text"] += " " + line
        
        # Add final task
        if current_task:
            tasks.append(current_task)
        
        # Add task IDs
        for i, task in enumerate(tasks):
            task["id"] = i + 1
        
        return tasks
    
    def _is_question(self, text: str) -> bool:
        """Check if text looks like a question or task"""
        # Look for question patterns
        question_patterns = [
            r'^\d+\.',  # Numbered questions
            r'^[A-Z][^.]*[?]$',  # Questions ending with ?
            r'^Question\s+\d+',  # "Question 1"
            r'^Task\s+\d+',  # "Task 1"
            r'^Problem\s+\d+',  # "Problem 1"
            r'^Exercise\s+\d+',  # "Exercise 1"
        ]
        
        return any(re.match(pattern, text, re.IGNORECASE) for pattern in question_patterns)
    
    def _is_code(self, text: str) -> bool:
        """Check if text looks like code"""
        # Python-specific indicators
        python_keywords = [
            'def ', 'class ', 'import ', 'from ', 'if __name__',
            'print(', 'for ', 'while ', 'try:', 'except:', 'with ',
            'return ', 'yield ', 'lambda ', 'async ', 'await '
        ]
        
        # Check for indentation (common in code)
        if text.startswith('    ') or text.startswith('\t'):
            return True
        
        # Check for Python keywords
        if any(keyword in text for keyword in python_keywords):
            return True
        
        # Check for code-like patterns
        code_patterns = [
            r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # Function calls
            r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=',  # Variable assignments
            r'^\s*#.*$',  # Comments
        ]
        
        return any(re.match(pattern, text) for pattern in code_patterns)


# Global instance
parser_service = ParserService()
