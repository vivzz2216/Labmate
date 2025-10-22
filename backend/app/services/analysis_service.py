import json
import jsonschema
import re
from typing import List, Dict, Any, Optional
import openai
from ..config import settings
from ..services.parser_service import parser_service


class AnalysisService:
    """Service for AI-powered document analysis using OpenAI Chat API"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        
        if self.api_key:
            import openai
            openai.api_key = self.api_key
            self.client = openai
        else:
            print("Warning: OPENAI_API_KEY not set. AI analysis features will be disabled.")
        
        # Model selection for different tasks
        self.analysis_model = "gpt-4o"  # Best for document analysis (fallback to gpt-4o-mini)
        self.generation_model = "gpt-4o-mini"  # For answer/code generation
        self.caption_model = "gpt-4o-mini"  # For caption summarization
        
        # JSON schema for task candidates
        self.candidates_schema = {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "question_context": {"type": "string"},
                            "task_type": {"type": "string", "enum": ["screenshot_request", "answer_request", "code_execution", "react_project"]},
                            "suggested_code": {"type": ["string", "object", "null"]},
                            "extracted_code": {"type": ["string", "null"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "suggested_insertion": {"type": "string", "enum": ["below_question", "bottom_of_page"]},
                            "brief_description": {"type": "string"},
                            "follow_up": {"type": ["string", "null"]},
                            "project_files": {"type": ["object", "null"]},
                            "routes": {"type": ["array", "null"]}
                        },
                        "required": ["task_id", "question_context", "task_type", "confidence", "suggested_insertion", "brief_description"]
                    }
                }
            },
            "required": ["candidates"]
        }
    
    async def analyze_document(self, file_path: str, file_type: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Analyze uploaded document and return AI-generated task candidates
        """
        if not self.client:
            # Return empty list if OpenAI API key is not available
            return []
            
        try:
            # Add file existence validation
            import os
            if not os.path.exists(file_path):
                raise Exception(f"File not found at path: {file_path}")
            
            # Parse the document to extract text and structure
            parsed_content = await parser_service.parse_file(file_path, file_type)
            
            # Convert parsed content to text for analysis
            document_text = self._extract_text_for_analysis(parsed_content)
            
            # Truncate if too long (keep first 8000 characters to leave room for response)
            if len(document_text) > 8000:
                document_text = document_text[:8000] + "\n\n[Document truncated...]"
            
            # Generate task candidates using OpenAI
            candidates = await self._generate_task_candidates(document_text)
            
            return candidates
            
        except Exception as e:
            raise Exception(f"Document analysis failed: {str(e)}")
    
    def _extract_text_for_analysis(self, parsed_content: List[Dict[str, Any]]) -> str:
        """Extract and format text from parsed content for AI analysis"""
        text_parts = []
        
        for i, task in enumerate(parsed_content):
            text_parts.append(f"Question {i+1}: {task.get('question_text', '')}")
            if task.get('code_snippet'):
                text_parts.append(f"Code: {task['code_snippet']}")
            text_parts.append("")  # Empty line between questions
        
        return "\n".join(text_parts)
    
    def _detect_react_project(self, document_text: str) -> dict:
        """Detect if document contains React SPA project structure"""
        patterns = {
            "has_router": r"react-router|BrowserRouter|Routes|Route",
            "has_components": r"components/.*?\.js|Navbar|Home|About|Contact",
            "has_package_json": r"package\.json|npm install",
            "has_app_js": r"App\.js|function App"
        }
        
        detected = {key: bool(re.search(pattern, document_text, re.IGNORECASE)) 
                    for key, pattern in patterns.items()}
        
        is_react_project = sum(detected.values()) >= 2
        return {"is_project": is_react_project, "features": detected}
    
    def _extract_project_files(self, code_text: str) -> dict:
        """Extract file paths and contents from AI response"""
        files = {}
        
        # Handle None or empty input
        if not code_text or not isinstance(code_text, str):
            return files
        
        # Pattern to match file headers and their content
        # Matches: src/App.js or App.js followed by code block
        pattern = r'(?:^|\n)(?:src/)?([A-Za-z]+\.(?:js|jsx|css))[:\s]*\n(.*?)(?=\n(?:src/)?[A-Za-z]+\.(?:js|jsx|css)|$)'
        matches = re.findall(pattern, code_text, re.DOTALL | re.MULTILINE)
        
        for filepath, content in matches:
            # Clean up content
            content = content.strip()
            # Remove code fence markers if present
            content = re.sub(r'^```(?:javascript|jsx|css)?\n', '', content)
            content = re.sub(r'\n```$', '', content)
            files[f"src/{filepath}"] = content.strip()
        
        # If no files found, treat entire code as App.jsx
        return files if files else {"src/App.jsx": code_text}
    
    def _extract_routes(self, code_text: str) -> list:
        """Extract React Router routes from code"""
        routes = ["/"]  # Always include home
        
        # Handle None or empty input
        if not code_text or not isinstance(code_text, str):
            return routes
            
        route_pattern = r'<Route\s+path=["\']([^"\']+)["\']'
        found_routes = re.findall(route_pattern, code_text)
        routes.extend([r for r in found_routes if r != "/"])
        return list(set(routes))  # Remove duplicates
    
    async def _generate_task_candidates(self, document_text: str) -> List[Dict[str, Any]]:
        """Generate task candidates using OpenAI Chat API"""
        
        if not self.client:
            return []
            
        system_prompt = """You are an expert computer science teaching assistant analyzing programming assignments. 

Your task is to analyze the provided assignment document and identify opportunities for:
1. **answer_request**: Questions that need AI-generated explanations or answers
2. **react_project**: ANY React/JSX code (MUST use this for ALL React code, even "Hello World")
3. **screenshot_request**: Non-React code that should be executed and screenshotted
4. **code_execution**: Non-React code blocks (Python, Java, C, etc.)

**CRITICAL RULE**: If you see ANY of these keywords in code: React, ReactDOM, JSX, import from 'react', useState, useEffect, function component returning JSX (<div>, <h1>, etc.), YOU MUST classify it as "react_project" type. NEVER use "code_execution" or "screenshot_request" for React code.

For each identified task, provide:
- A unique task_id (e.g., "task_1", "task_2")
- The relevant question context (excerpt from the document)
- The appropriate task type
- Suggested code if needed (for execution/screenshot tasks)
- Confidence score (0.0-1.0)
- Brief description of what this task accomplishes
- Optional follow-up question if you need clarification from the user

**CRITICAL: For React Projects (THIS IS MANDATORY)**:
If you see ANY React code whatsoever (even a single line like "import React from 'react'" or "ReactDOM.render"), YOU MUST:
1. Set task_type to "react_project" (NOT "code_execution", NOT "screenshot_request")
2. This applies to ALL React code: simple "Hello World", single components, full SPAs, everything
3. In the "suggested_code" field, create a nested structure with "project_files" and "routes":
   ```json
   "suggested_code": {
       "project_files": {
           "src/App.js": "import React from 'react';\\nimport { BrowserRouter as Router, Routes, Route } from 'react-router-dom';\\n...",
           "src/components/Navbar.js": "import React from 'react';\\nimport { Link } from 'react-router-dom';\\n...",
           "src/components/Home.js": "import React from 'react';\\n\\nfunction Home() {\\n  return <div><h1>Home</h1></div>;\\n}\\nexport default Home;",
           "src/App.css": "body {\\n  font-family: Arial, sans-serif;\\n}"
       },
       "routes": ["/", "/about", "/contact"]
   }
   ```

4. **Generate COMPLETE, WORKING React code**:
   - Use modern React with functional components
   - Use react-router-dom v6 syntax (Routes, Route, Link)
   - Include proper imports and exports
   - Each component file should be complete and working
   - Include ALL necessary files: App.js, all component files, CSS files
   - Ensure proper JSX syntax
   - NO Python code, NO placeholders, ONLY React/JavaScript

5. **Extract files from the document**:
   - If the document shows code examples, use those
   - If the document only describes the project, generate the complete working code
   - Create all necessary component files (Navbar, Home, About, Contact, etc.)
   - Include proper styling in CSS files

6. **For SIMPLE React code (like "Hello World")**:
   - Even if the user only provides a single component, structure it as a full project
   - Create a complete src/ folder structure with:
     * src/App.js (the user's component or a wrapper)
     * src/index.js (entry point with ReactDOM.render)
     * src/index.css (basic styling)
   - Set routes to ["/"] for single-page apps
   - Example for "Hello World":
     ```json
     "project_files": {
       "src/App.js": "import React from 'react';\\n\\nfunction App() {\\n  return <div><h1>Hello, World!</h1></div>;\\n}\\n\\nexport default App;",
       "src/index.js": "import React from 'react';\\nimport ReactDOM from 'react-dom';\\nimport App from './App';\\n\\nReactDOM.render(<App />, document.getElementById('root'));",
       "src/index.css": "body { font-family: Arial, sans-serif; }"
     },
     "routes": ["/"]
     ```

**EXAMPLE OUTPUT for React Project**:
```json
{
  "candidates": [
    {
      "task_id": "task_1",
      "question_context": "Create a single page application using React Router",
      "task_type": "react_project",
      "suggested_code": {
        "project_files": {
          "src/App.js": "COMPLETE REACT CODE HERE",
          "src/components/Navbar.js": "COMPLETE NAVBAR CODE HERE"
        },
        "routes": ["/", "/about"]
      },
      "confidence": 0.95,
      "brief_description": "Complete React SPA with routing",
      "suggested_insertion": "below_question"
    }
  ]
}
```

IMPORTANT: 
- Only output valid JSON matching the exact schema
- For React projects, ALWAYS use JavaScript/React code, NEVER Python
- Generate COMPLETE working code, not snippets
- Do not include any text before or after the JSON"""

        user_prompt = f"""Analyze this programming assignment and identify tasks:

{document_text}

Return a JSON object with a "candidates" array containing task suggestions. Each candidate should help the student complete their assignment by providing screenshots of code execution, AI-generated answers, or code demonstrations."""

        # Try GPT-4o first, fallback to GPT-4o-mini for document analysis
        model_to_use = self.analysis_model
        
        try:
            response = self.client.ChatCompletion.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.3,
                timeout=60  # Add timeout
            )
            
            content = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            
            # Check if content is empty
            if not content:
                raise Exception(f"Empty response from OpenAI. Response object: {response}")
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Parse and validate JSON response
            try:
                parsed_response = json.loads(content)
                
                # Normalize the response - add missing required fields with defaults
                if "candidates" in parsed_response:
                    for candidate in parsed_response["candidates"]:
                        # Handle description vs brief_description
                        if "description" in candidate and "brief_description" not in candidate:
                            candidate["brief_description"] = candidate["description"]
                        if "brief_description" not in candidate:
                            candidate["brief_description"] = f"Task: {candidate.get('task_type', 'unknown')}"
                        
                        # Add default suggested_insertion if missing
                        if "suggested_insertion" not in candidate:
                            candidate["suggested_insertion"] = "below_question"
                        
                        # Map field names if OpenAI uses different names
                        if "context" in candidate and "question_context" not in candidate:
                            candidate["question_context"] = candidate["context"]
                        if "description" in candidate and "brief_description" not in candidate:
                            candidate["brief_description"] = candidate["description"]
                        
                        # Ensure all required fields exist
                        if "confidence" not in candidate:
                            candidate["confidence"] = 0.8
                        if "extracted_code" not in candidate:
                            candidate["extracted_code"] = None
                        if "suggested_code" not in candidate:
                            candidate["suggested_code"] = None
                        if "follow_up" not in candidate:
                            candidate["follow_up"] = None
                        
                        # Handle react_project type: extract files and routes
                        if candidate.get("task_type") == "react_project":
                            suggested_code = candidate.get("suggested_code")
                            
                            # Check if suggested_code has nested project_files and routes structure
                            if isinstance(suggested_code, dict):
                                # Check if it's a nested structure with project_files/routes keys
                                if "project_files" in suggested_code or "routes" in suggested_code:
                                    # Extract from nested structure
                                    candidate["project_files"] = suggested_code.get("project_files", {})
                                    candidate["routes"] = suggested_code.get("routes", [])
                                    # Set suggested_code to the project_files for compatibility
                                    candidate["suggested_code"] = candidate["project_files"]
                                else:
                                    # It's a direct project files dict
                                    candidate["project_files"] = suggested_code
                                    # Extract routes from the combined code (ensure all values are strings)
                                    combined_code = "\n".join([
                                        str(value) for value in suggested_code.values() 
                                        if isinstance(value, str)
                                    ])
                                    candidate["routes"] = self._extract_routes(combined_code)
                            elif isinstance(suggested_code, str):
                                # Extract files from string suggested_code
                                candidate["project_files"] = self._extract_project_files(suggested_code)
                                candidate["routes"] = self._extract_routes(suggested_code)
                            
                            # Set defaults if still not present
                            if not candidate.get("project_files"):
                                candidate["project_files"] = None
                            if not candidate.get("routes"):
                                candidate["routes"] = settings.REACT_DEFAULT_ROUTES
                        else:
                            # For non-project types, set to None
                            if "project_files" not in candidate:
                                candidate["project_files"] = None
                            if "routes" not in candidate:
                                candidate["routes"] = None
                
                # Now validate
                jsonschema.validate(parsed_response, self.candidates_schema)
                return parsed_response["candidates"]
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                raise Exception(f"Invalid JSON response from OpenAI. Error: {str(e)}. Content received: {content[:500]}")
                
        except Exception as e:
            # Fallback to GPT-4o-mini if GPT-4o fails
            if model_to_use == "gpt-4o" and ("does not exist" in str(e) or "not found" in str(e)):
                try:
                    response = self.client.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=settings.OPENAI_MAX_TOKENS,
                        temperature=0.3
                    )
                    content = response.choices[0].message.content.strip()
                    try:
                        parsed_response = json.loads(content)
                        jsonschema.validate(parsed_response, self.candidates_schema)
                        return parsed_response["candidates"]
                    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                        raise Exception(f"Invalid JSON response from OpenAI: {str(e)}")
                except Exception as fallback_error:
                    raise Exception(f"OpenAI API error (tried gpt-4o and gpt-4o-mini): {str(fallback_error)}")
            
            if "rate limit" in str(e).lower():
                raise Exception("OpenAI rate limit exceeded. Please try again later.")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_code_and_answer(self, task_type: str, question_context: str, 
                                     extracted_code: Optional[str] = None,
                                     follow_up_answer: Optional[str] = None) -> Dict[str, str]:
        """Generate code and/or answer for a specific task"""
        
        if task_type == "answer_request":
            return await self._generate_answer(question_context, follow_up_answer)
        elif task_type in ["screenshot_request", "code_execution"]:
            return await self._generate_code(question_context, extracted_code, follow_up_answer)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _generate_answer(self, question_context: str, follow_up_answer: Optional[str] = None) -> Dict[str, str]:
        """Generate AI answer for a question"""
        
        system_prompt = """You are an expert computer science tutor. Provide clear, educational explanations for programming questions.

Focus on:
- Clear explanations of concepts
- Step-by-step reasoning
- Code examples when helpful
- Best practices and common pitfalls

Keep answers concise but comprehensive (2-4 paragraphs)."""

        user_prompt = f"""Answer this programming question:

{question_context}"""

        if follow_up_answer:
            user_prompt += f"\n\nAdditional context from user: {follow_up_answer}"

        try:
            response = self.client.ChatCompletion.create(
                model=self.generation_model,  # Use GPT-4o-mini for answer generation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return {"answer": response.choices[0].message.content.strip()}
            
        except Exception as e:
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    async def _generate_code(self, question_context: str, extracted_code: Optional[str] = None,
                           follow_up_answer: Optional[str] = None) -> Dict[str, str]:
        """Generate runnable Python code for a task"""
        
        system_prompt = """You are an expert Python programmer. Generate clean, runnable Python code that solves the given problem.

Requirements:
- Use only standard library modules (no external packages)
- Include clear variable names and comments
- Add print statements to show output/results
- Handle edge cases appropriately
- Keep code concise but readable

Return only the Python code, no explanations."""

        user_prompt = f"""Generate Python code for this task:

{question_context}"""

        if extracted_code:
            user_prompt += f"\n\nExisting code from document:\n{extracted_code}"
        
        if follow_up_answer:
            user_prompt += f"\n\nUser clarification: {follow_up_answer}"

        try:
            response = self.client.ChatCompletion.create(
                model=self.generation_model,  # Use GPT-4o-mini for code generation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return {"code": response.choices[0].message.content.strip()}
            
        except Exception as e:
            raise Exception(f"Failed to generate code: {str(e)}")
    
    async def generate_caption(self, task_type: str, stdout: str, exit_code: int, 
                             code_snippet: str) -> str:
        """Generate a caption for a screenshot or execution result"""
        
        system_prompt = """Generate a brief, professional caption (1-2 sentences) that describes what the code does and its output.

Focus on:
- What the code accomplishes
- Key results or outputs shown
- Success/failure status if relevant

Keep it concise and educational."""

        user_prompt = f"""Task type: {task_type}
Code executed:
{code_snippet}

Output:
{stdout}

Exit code: {exit_code}

Generate a caption for this execution result."""

        try:
            response = self.client.ChatCompletion.create(
                model=self.caption_model,  # Use GPT-4o-mini for caption generation (fast & cheap)
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback caption if AI generation fails
            return f"Code execution {'successful' if exit_code == 0 else 'failed'} with exit code {exit_code}"


# Create singleton instance
analysis_service = AnalysisService()
