import os
import uuid
import json
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import AIJob, AITask, Upload, User
from ..schemas import TaskSubmission, TaskResult
from ..services.analysis_service import analysis_service
from ..services.validator_service import validator_service
from ..services.executor_service import executor_service
from ..services.screenshot_service import screenshot_service
from ..config import settings


class TaskService:
    """Service for orchestrating AI task execution"""
    
    def _map_language_to_theme(self, language: str) -> str:
        """Map programming language to IDE theme"""
        mapping = {
            'python': 'idle',
            'java': 'notepad',
            'c': 'codeblocks',
            'html': 'html',
            'react': 'react',
            'node': 'node'
        }
        return mapping.get(language, 'idle')  # Default to idle
    
    async def submit_tasks(self, file_id: int, tasks: List[TaskSubmission], 
                          theme: str, insertion_preference: str, db: Session) -> int:
        """Submit selected tasks for processing"""
        
        # Get upload record
        upload = db.query(Upload).filter(Upload.id == file_id).first()
        if not upload:
            raise ValueError("Upload not found")
        
        # Normalize theme based on upload language (force correct theme for non-Python)
        if upload.language:
            lang_theme = self._map_language_to_theme(upload.language)
            if not theme or theme not in ["idle", "vscode", "notepad", "codeblocks", "html", "react", "node"]:
                theme = lang_theme
            # If language is non-Python but theme is still a Python theme, override
            if upload.language in ["c", "java", "html", "react", "node"] and theme in ["idle", "vscode"]:
                theme = lang_theme
        
        # Create AI job record
        job = AIJob(
            upload_id=file_id,
            status="pending",
            theme=theme,
            insertion_preference=insertion_preference
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Create AI task records for selected tasks
        selected_tasks = [task for task in tasks if task.selected]
        for task_submission in selected_tasks:
            ai_task = AITask(
                job_id=job.id,
                task_id=task_submission.task_id,
                task_type=task_submission.task_type or "",  # From frontend submission
                question_context=task_submission.question_context or "",  # From frontend
                user_code=task_submission.user_code,
                follow_up_answer=task_submission.follow_up_answer,
                confidence=80,  # Default confidence (0-100 scale for database)
                status="pending",
                suggested_insertion=task_submission.insertion_preference,
                project_files=task_submission.project_files,  # For React projects
                routes=task_submission.routes  # For React projects
            )
            db.add(ai_task)
        
        db.commit()
        
        # Start background processing (in a real app, use Celery or similar)
        # For now, we'll process synchronously
        await self._process_job(job.id, db)
        
        return job.id
    
    async def _process_job(self, job_id: int, db: Session):
        """Process all tasks in a job"""
        
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if not job:
            return
        
        job.status = "running"
        db.commit()
        
        try:
            tasks = db.query(AITask).filter(AITask.job_id == job_id).all()
            
            for task in tasks:
                await self._process_single_task(task, job, db)
            
            job.status = "completed"
            db.commit()
            
        except Exception as e:
            job.status = "failed"
            db.commit()
            raise e
    
    async def _process_single_task(self, task: AITask, job: AIJob, db: Session):
        """Process a single AI task"""
        
        task.status = "running"
        db.commit()
        
        try:
            # Task type and context are already set from submit_tasks method
            # No need to override with mock data
            
            print(f"[Task Service] Processing task {task.id} with type: {task.task_type}")
            print(f"[Task Service] Question context: {task.question_context}")
            
            # If no user code provided, generate code using AI (only for non-React tasks)
            if not task.user_code and task.task_type != "react_project":
                if task.task_type in ["screenshot_request", "code_execution"]:
                    code_result = await analysis_service.generate_code_and_answer(
                        task.task_type, task.question_context, 
                        follow_up_answer=task.follow_up_answer
                    )
                    task.user_code = code_result.get("code", "")
                elif task.task_type == "answer_request":
                    answer_result = await analysis_service.generate_code_and_answer(
                        task.task_type, task.question_context,
                        follow_up_answer=task.follow_up_answer
                    )
                    task.assistant_answer = answer_result.get("answer", "")
            
            # Execute code if it's a code execution task
            if task.task_type in ["screenshot_request", "code_execution"] and task.user_code:
                await self._execute_code_task(task, job, db)
            elif task.task_type == "react_project":
                await self._execute_react_project_task(task, job, db)
            elif task.task_type == "answer_request":
                task.status = "completed"
                db.commit()
            
        except Exception as e:
            task.status = "failed"
            db.commit()
            raise e
    
    async def _execute_code_task(self, task: AITask, job: AIJob, db: Session):
        """Execute code for a task and generate screenshots"""
        
        is_python_theme = job.theme in ["idle", "vscode"]

        # Determine language based on theme
        if job.theme == "codeblocks":
            language = "c"
        elif job.theme == "notepad":
            language = "java"
        elif job.theme == "html":
            language = "html"
        elif job.theme == "react":
            language = "react"
        elif job.theme == "node":
            language = "node"
        else:
            language = "python"

        # For Python themes, validate and execute; for other languages, execute directly
        if is_python_theme:
            # Validate code
            is_valid, error_msg = validator_service.validate_code(task.user_code)
            if not is_valid:
                task.status = "failed"
                task.caption = f"Code validation failed: {error_msg}"
                db.commit()
                return
            
            # Execute code
            success, output, logs, exit_code = await executor_service.execute_code(task.user_code, language)
        else:
            # Non-Python (C, Java, HTML, React, Node): execute directly without Python validation
            success, output, logs, exit_code = await executor_service.execute_code(task.user_code, language)
        
        # Store execution results
        task.stdout = output
        task.exit_code = exit_code
        
        # Generate screenshot
        if success:
            # Get user information for personalized display
            upload = db.query(Upload).filter(Upload.id == job.upload_id).first()
            user = db.query(User).filter(User.id == upload.user_id).first() if upload else None
            
            # Extract first name from full name
            if user and user.name:
                username = user.name.split()[0]  # Get first name only
            else:
                username = "User"
            
            # Use custom filename if provided, otherwise generate default
            filename = getattr(upload, 'custom_filename', None) if upload else None
            if not filename:
                # Pick sensible default extension based on theme
                default_ext = ".py" if is_python_theme else (".c" if job.theme == "codeblocks" else ".java")
                filename = f"exp{job.id}{default_ext}"
            else:
                # Ensure extension matches theme if user omitted it
                if is_python_theme and not filename.endswith(".py"):
                    filename = f"{filename}.py"
                if job.theme == "codeblocks" and not filename.endswith(".c"):
                    filename = f"{filename}.c"
                if job.theme == "notepad" and not filename.endswith(".java"):
                    filename = f"{filename}.java"
            
            screenshot_success, screenshot_path, width, height = await screenshot_service.generate_screenshot(
                task.user_code, output, job.theme, job.id, username, filename
            )
            
            if screenshot_success:
                task.screenshot_path = screenshot_path
        
        # Generate caption
        try:
            caption = await analysis_service.generate_caption(
                task.task_type, output or logs, exit_code, task.user_code
            )
            task.caption = caption
        except:
            task.caption = f"Code execution {'successful' if exit_code == 0 else 'failed'}"
        
        task.status = "completed" if success else "failed"
        db.commit()
    
    async def _execute_react_project_task(self, task: AITask, job: AIJob, db: Session):
        """Execute React project with multiple files and routes"""
        
        print(f"[Task Service] Processing React project task {task.id}")
        
        # Get project files and routes
        project_files = task.project_files or {}
        routes = task.routes or settings.REACT_DEFAULT_ROUTES
        
        if not project_files:
            task.status = "failed"
            task.caption = "No project files found"
            db.commit()
            return
        
        print(f"[Task Service] Project files: {list(project_files.keys())}")
        print(f"[Task Service] Routes to capture: {routes}")
        
        # Execute React project
        success, screenshots_by_route, logs, exit_code = await executor_service.execute_react_project(
            project_files, routes
        )
        
        # Store execution results
        task.stdout = logs
        task.exit_code = exit_code
        
        if success and screenshots_by_route:
            # Get user information for personalized display
            upload = db.query(Upload).filter(Upload.id == job.upload_id).first()
            user = db.query(User).filter(User.id == upload.user_id).first() if upload else None
            
            # Extract first name from full name
            if user and user.name:
                username = user.name.split()[0]  # Get first name only
            else:
                username = "User"
            
            # Generate screenshots for all routes
            screenshot_urls = await screenshot_service.generate_project_screenshots(
                project_files, screenshots_by_route, job.id, task.id, username
            )
            
            # Store screenshot URLs as JSON
            task.screenshot_urls = json.dumps(screenshot_urls)
            
            # Also set first screenshot as primary
            if screenshot_urls:
                task.screenshot_path = screenshot_urls[0]["url"]
            
            print(f"[Task Service] Generated {len(screenshot_urls)} screenshots")
            
            # Generate caption
            try:
                caption = await analysis_service.generate_caption(
                    task.task_type, f"React SPA with {len(routes)} routes", exit_code, ""
                )
                task.caption = caption
            except:
                task.caption = f"React SPA project with {len(routes)} routes captured successfully"
        else:
            task.caption = "React project execution failed"
        
        task.status = "completed" if success else "failed"
        db.commit()
    
    async def get_job_status(self, job_id: int, db: Session) -> Dict[str, Any]:
        """Get status of a job and its tasks"""
        
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if not job:
            raise ValueError("Job not found")
        
        tasks = db.query(AITask).filter(AITask.job_id == job_id).all()
        
        task_results = []
        for task in tasks:
            screenshot_url = None
            if task.screenshot_path:
                # Screenshot path is already a URL path (e.g., /screenshots/154/screenshot_xxx.png)
                # Use it directly if it starts with /screenshots/, otherwise convert from absolute path
                if task.screenshot_path.startswith("/screenshots/"):
                    screenshot_url = task.screenshot_path
                else:
                    # Legacy format: absolute path like /app/screenshots/154/...
                    relative_path = task.screenshot_path.replace(settings.SCREENSHOT_DIR + "/", "")
                    screenshot_url = f"/screenshots/{relative_path}"
            
            task_result = TaskResult(
                id=task.id,
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                screenshot_url=screenshot_url,
                stdout=task.stdout,
                exit_code=task.exit_code,
                caption=task.caption,
                assistant_answer=task.assistant_answer
            )
            task_results.append(task_result)
        
        return {
            "job_id": job.id,
            "status": job.status,
            "tasks": task_results
        }


# Create singleton instance
task_service = TaskService()
