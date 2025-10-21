from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import TasksSubmitRequest, TasksSubmitResponse, JobStatusResponse
from ..services.task_service import task_service

router = APIRouter()


@router.post("/tasks/submit", response_model=TasksSubmitResponse)
async def submit_tasks(
    request: TasksSubmitRequest,
    db: Session = Depends(get_db)
):
    """Submit selected tasks for AI processing"""
    
    try:
        print(f"[DEBUG] Tasks submit request received:")
        print(f"[DEBUG] file_id: {request.file_id}")
        print(f"[DEBUG] theme: {request.theme}")
        print(f"[DEBUG] insertion_preference: {request.insertion_preference}")
        print(f"[DEBUG] tasks count: {len(request.tasks)}")
        
        for i, task in enumerate(request.tasks):
            print(f"[DEBUG] Task {i}: task_id={task.task_id}, selected={task.selected}, task_type={task.task_type}")
            print(f"[DEBUG] Task {i} project_files type: {type(task.project_files)}")
            print(f"[DEBUG] Task {i} project_files value: {task.project_files}")
            print(f"[DEBUG] Task {i} routes: {task.routes}")
            if task.project_files:
                print(f"[DEBUG] Task {i} project_files: {len(task.project_files)} files")
            if task.routes:
                print(f"[DEBUG] Task {i} routes: {task.routes}")
        
        job_id = await task_service.submit_tasks(
            request.file_id,
            request.tasks,
            request.theme,
            request.insertion_preference,
            db
        )
        
        return TasksSubmitResponse(job_id=job_id, status="submitted")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in tasks/submit endpoint:")
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Task submission failed: {str(e)}")


@router.get("/tasks/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int = Path(..., description="ID of the job"),
    db: Session = Depends(get_db)
):
    """Get status and results of a job"""
    
    try:
        job_status = await task_service.get_job_status(job_id, db)
        return JobStatusResponse(**job_status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")
