import json
import jsonschema
from typing import List, Dict, Any, Optional
import openai
from ..config import settings
from ..services.parser_service import parser_service


class AnalysisService:
    """Service for AI-powered document analysis using OpenAI Chat API"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        import openai
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai
        
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
                            "task_type": {"type": "string", "enum": ["screenshot_request", "answer_request", "code_execution"]},
                            "suggested_code": {"type": ["string", "null"]},
                            "extracted_code": {"type": ["string", "null"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "suggested_insertion": {"type": "string", "enum": ["below_question", "bottom_of_page"]},
                            "brief_description": {"type": "string"},
                            "follow_up": {"type": ["string", "null"]}
                        },
                        "required": ["task_id", "question_context", "task_type", "confidence", "suggested_insertion", "brief_description"]
                    }
                }
            },
            "required": ["candidates"]
        }
    
    async def analyze_document(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Analyze uploaded document and return AI-generated task candidates
        """
        try:
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
    
    async def _generate_task_candidates(self, document_text: str) -> List[Dict[str, Any]]:
        """Generate task candidates using OpenAI Chat API"""
        
        system_prompt = """You are an expert computer science teaching assistant analyzing programming assignments. 

Your task is to analyze the provided assignment document and identify opportunities for:
1. **screenshot_request**: Code that should be executed and screenshotted to show output
2. **answer_request**: Questions that need AI-generated explanations or answers
3. **code_execution**: Code blocks that need to be run to demonstrate functionality

For each identified task, provide:
- A unique task_id (e.g., "task_1", "task_2")
- The relevant question context (excerpt from the document)
- The appropriate task type
- Suggested code if needed (for execution/screenshot tasks)
- Confidence score (0.0-1.0)
- Brief description of what this task accomplishes
- Optional follow-up question if you need clarification from the user

IMPORTANT: Only output valid JSON matching the exact schema. Do not include any text before or after the JSON."""

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
                        
                        # Ensure all required fields exist
                        if "confidence" not in candidate:
                            candidate["confidence"] = 0.8
                        if "extracted_code" not in candidate:
                            candidate["extracted_code"] = None
                        if "suggested_code" not in candidate:
                            candidate["suggested_code"] = None
                        if "follow_up" not in candidate:
                            candidate["follow_up"] = None
                
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
