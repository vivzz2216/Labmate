from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Upload
from ..schemas import ParseResponse, Task
from ..services.parser_service import parser_service
from ..middleware.beta_key import verify_beta_key

router = APIRouter(dependencies=[Depends(verify_beta_key)])


@router.get("/parse/{file_id}", response_model=ParseResponse)
async def parse_file(
    file_id: int = Path(..., description="ID of the uploaded file"),
    db: Session = Depends(get_db)
):
    """Parse uploaded file and extract code blocks and tasks"""
    
    # Get upload record
    upload = db.query(Upload).filter(Upload.id == file_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Parse the file
        tasks_data = await parser_service.parse_file(upload.file_path, upload.file_type)
        
        # Convert to Task objects
        tasks = []
        for task_data in tasks_data:
            task = Task(
                id=task_data["id"],
                question_text=task_data["question_text"],
                code_snippet=task_data["code_snippet"],
                requires_screenshot=task_data["requires_screenshot"]
            )
            tasks.append(task)
        
        return ParseResponse(tasks=tasks)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
