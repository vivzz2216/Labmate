from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Upload, Report
from ..schemas import ComposeRequest, ComposeResponse
from ..services.composer_service import composer_service
from ..middleware.beta_key import verify_beta_key
import os

router = APIRouter(dependencies=[Depends(verify_beta_key)])


@router.post("/compose", response_model=ComposeResponse)
async def compose_report(
    request: ComposeRequest,
    db: Session = Depends(get_db)
):
    """Generate final DOCX report with embedded screenshots"""
    
    # Get upload record
    upload = db.query(Upload).filter(Upload.id == request.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    try:
        # Compose the report using our new composer service
        result = await composer_service.compose_report(
            request.upload_id, 
            request.screenshot_order, 
            db
        )
        
        # Create report record
        report = Report(
            upload_id=request.upload_id,
            filename=result["filename"],
            file_path=result["report_path"],
            file_size=os.path.getsize(result["report_path"]),
            screenshot_order=request.screenshot_order
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return ComposeResponse(
            report_id=report.id,
            filename=result["filename"],
            download_url=result["download_url"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report composition failed: {str(e)}")
