from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Upload
from ..schemas import AnalyzeRequest, AnalyzeResponse, AITaskCandidate
from ..services.analysis_service import analysis_service

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Analyze uploaded document and generate AI task suggestions"""
    
    # Get upload record
    upload = db.query(Upload).filter(Upload.id == request.file_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update upload with language if provided
    if request.language:
        upload.language = request.language
        db.commit()
    
    try:
        # Analyze the document
        candidates_data = await analysis_service.analyze_document(
            upload.file_path, upload.file_type, request.language
        )
        
        # Convert to response format
        candidates = []
        for candidate_data in candidates_data:
            print(f"[DEBUG] Processing candidate: task_id={candidate_data.get('task_id')}, task_type={candidate_data.get('task_type')}")
            print(f"[DEBUG] suggested_code type: {type(candidate_data.get('suggested_code'))}")
            print(f"[DEBUG] project_files: {candidate_data.get('project_files') is not None}")
            print(f"[DEBUG] routes: {candidate_data.get('routes')}")
            
            candidate = AITaskCandidate(
                task_id=candidate_data["task_id"],
                question_context=candidate_data["question_context"],
                task_type=candidate_data["task_type"],
                suggested_code=candidate_data.get("suggested_code"),
                extracted_code=candidate_data.get("extracted_code"),
                confidence=candidate_data["confidence"],
                suggested_insertion=candidate_data["suggested_insertion"],
                brief_description=candidate_data["brief_description"],
                follow_up=candidate_data.get("follow_up"),
                project_files=candidate_data.get("project_files"),
                routes=candidate_data.get("routes")
            )
            candidates.append(candidate)
        
        return AnalyzeResponse(candidates=candidates)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in analyze endpoint:")
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
