from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Report
from ..middleware.beta_key import verify_beta_key
import os

router = APIRouter(dependencies=[Depends(verify_beta_key)])


@router.get("/download/{doc_id}")
async def download_report(
    doc_id: int = Path(..., description="ID of the generated report"),
    db: Session = Depends(get_db)
):
    """Download the generated report file"""
    
    # Get report record
    report = db.query(Report).filter(Report.id == doc_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if file exists
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    
    try:
        # Return file for download
        return FileResponse(
            path=report.file_path,
            filename=report.filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
