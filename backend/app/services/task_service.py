import os
import uuid
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
            'c': 'codeblocks'
        }
        return mapping.get(language, 'idle')  # Default to idle
    
    async def submit_tasks(self, file_id: int, tasks: List[TaskSubmission], 
                          theme: str, insertion_preference: str, db: Session) -> int:
        """Submit selected tasks for processing"""
        
        # Get upload record
        upload = db.query(Upload).filter(Upload.id == file_id).first()
        if not upload:
            raise ValueError("Upload not found")
        
        # Map language to theme if not provided
        if not theme and upload.language:
            theme = self._map_language_to_theme(upload.language)
        
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
                task_type="",  # Will be set when we process the task
                question_context="",  # Will be set when we process the task
                user_code=task_submission.user_code,
                follow_up_answer=task_submission.follow_up_answer,
                confidence=80,  # Default confidence (0-100 scale for database)
                status="pending",
                suggested_insertion=task_submission.insertion_preference
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
            # For now, we'll use mock data since we don't have the full context
            # In a real implementation, you'd store the original task context during analysis
            
            # Mock task context - in real implementation, this would come from analysis
            task.question_context = "Generate the first 10 Fibonacci numbers"
            task.task_type = "code_execution"
            
            # If no user code provided, generate code using AI
            if not task.user_code:
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
            elif task.task_type == "answer_request":
                task.status = "completed"
                db.commit()
            
        except Exception as e:
            task.status = "failed"
            db.commit()
            raise e
    
    async def _execute_code_task(self, task: AITask, job: AIJob, db: Session):
        """Execute code for a task and generate screenshots"""
        
        # Validate code
        is_valid, error_msg = validator_service.validate_code(task.user_code)
        if not is_valid:
            task.status = "failed"
            task.caption = f"Code validation failed: {error_msg}"
            db.commit()
            return
        
        # Execute code
        success, output, logs, exit_code = await executor_service.execute_code(task.user_code)
        
        # Store execution results
        task.stdout = output
        task.exit_code = exit_code
        
        # Generate screenshot
        if success and output:
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
                filename = f"exp{job.id}.py"  # Default filename like exp5.py
            
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
                # Generate URL for screenshot - extract relative path from /app/screenshots/
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
