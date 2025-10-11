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
        job_id = await task_service.submit_tasks(
            request.file_id,
            request.tasks,
            request.theme,
            request.insertion_preference,
            db
        )
        
        return TasksSubmitResponse(job_id=job_id, status="submitted")
        
    except Exception as e:
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
