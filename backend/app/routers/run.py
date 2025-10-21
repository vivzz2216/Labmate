from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Upload, Job, Screenshot, User
from ..schemas import RunRequest, RunResponse, JobStatus
from ..services.parser_service import parser_service
from ..services.validator_service import validator_service
from ..services.executor_service import executor_service
from ..services.screenshot_service import screenshot_service
from ..middleware.beta_key import verify_beta_key
import os

router = APIRouter(dependencies=[Depends(verify_beta_key)])


@router.post("/run", response_model=RunResponse)
async def run_tasks(
    request: RunRequest,
    db: Session = Depends(get_db)
):
    """Execute selected code blocks and generate screenshots"""
    
    # Get upload record
    upload = db.query(Upload).filter(Upload.id == request.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    try:
        # Parse file to get tasks
        tasks_data = await parser_service.parse_file(upload.file_path, upload.file_type)
        task_dict = {task["id"]: task for task in tasks_data}
        
        jobs = []
        
        # Process each requested task
        for task_id in request.task_ids:
            if task_id not in task_dict:
                continue
            
            task_data = task_dict[task_id]
            code_snippet = task_data["code_snippet"]
            
            if not code_snippet.strip():
                continue
            
            # Create job record
            job = Job(
                upload_id=request.upload_id,
                task_id=task_id,
                question_text=task_data["question_text"],
                code_snippet=code_snippet,
                theme=request.theme,
                status="running"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            try:
                # Determine language based on theme
                if request.theme == "codeblocks":
                    language = "c"
                elif request.theme == "notepad":
                    language = "java"
                elif request.theme == "html":
                    language = "html"
                elif request.theme == "react":
                    language = "react"
                elif request.theme == "node":
                    language = "node"
                else:
                    language = "python"
                
                # Validate code only for Python
                if language == "python":
                    is_valid, validation_error = validator_service.validate_code(code_snippet)
                    if not is_valid:
                        job.status = "failed"
                        job.error_message = f"Code validation failed: {validation_error}"
                        job.execution_time = 0
                        db.commit()
                        continue
                
                # Execute code
                success, output, error, execution_time = await executor_service.execute_code(code_snippet, language)
                
                if success:
                    job.status = "completed"
                    job.output_text = output
                    job.execution_time = execution_time
                    
                    # Generate screenshot if requested
                    if task_data["requires_screenshot"]:
                        # Get user information for personalized display
                        user = db.query(User).filter(User.id == upload.user_id).first() if upload.user_id else None
                        
                        # Extract first name from full name
                        if user and user.name:
                            username = user.name.split()[0]  # Get first name only (e.g., "Vivek" from "Vivek Pillai")
                        else:
                            username = "User"
                        
                        # Use custom filename if provided, otherwise generate default
                        filename = getattr(upload, 'custom_filename', None) if upload else None
                        if not filename:
                            filename = f"task{task_data['id']}.py"  # Default filename like task1.py
                        
                        screenshot_success, screenshot_path, width, height = await screenshot_service.generate_screenshot(
                            code_snippet, output, request.theme, job.id, username, filename
                        )
                        
                        if screenshot_success:
                            # Create screenshot record
                            screenshot = Screenshot(
                                job_id=job.id,
                                file_path=screenshot_path,
                                file_size=os.path.getsize(screenshot_path),
                                width=width,
                                height=height
                            )
                            db.add(screenshot)
                
                else:
                    job.status = "failed"
                    job.error_message = error
                    job.execution_time = execution_time
                
                db.commit()
                
            except Exception as e:
                job.status = "failed"
                job.error_message = f"Execution error: {str(e)}"
                job.execution_time = 0
                db.commit()
            
            jobs.append(job)
        
        # Build response
        job_statuses = []
        for job in jobs:
            # Get screenshot URL if exists
            screenshot_url = None
            screenshot = db.query(Screenshot).filter(Screenshot.job_id == job.id).first()
            if screenshot:
                screenshot_url = f"/screenshots/{job.id}/{os.path.basename(screenshot.file_path)}"
            
            job_status = JobStatus(
                id=job.id,
                task_id=job.task_id,
                question_text=job.question_text,
                status=job.status,
                output_text=job.output_text,
                error_message=job.error_message,
                execution_time=job.execution_time,
                screenshot_url=screenshot_url
            )
            job_statuses.append(job_status)
        
        return RunResponse(jobs=job_statuses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
