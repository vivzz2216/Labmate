from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Upload
from ..schemas import UploadResponse
from ..middleware.beta_key import verify_beta_key
from ..config import settings
import os
import uuid
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()  # Temporarily removed beta key requirement for testing


class SetFilenameRequest(BaseModel):
    upload_id: int
    filename: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user_id: int | None = Form(default=None),
    db: Session = Depends(get_db)
):
    """Upload a DOCX or PDF file for processing"""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['docx', 'pdf']:
        raise HTTPException(
            status_code=400, 
            detail="Only DOCX and PDF files are supported"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create database record
        upload = Upload(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=len(file_content),
            user_id=user_id
        )
        
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        return UploadResponse(
            id=upload.id,
            filename=upload.filename,
            original_filename=upload.original_filename,
            file_type=upload.file_type,
            file_size=upload.file_size,
            uploaded_at=upload.uploaded_at
        )
        
    except Exception as e:
        # Clean up file if database save fails
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/set-filename")
async def set_custom_filename(
    request: SetFilenameRequest,
    db: Session = Depends(get_db)
):
    """Set custom filename for an uploaded file"""
    
    # Find the upload record
    upload = db.query(Upload).filter(Upload.id == request.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Accept filename as provided (frontend will ensure correct extension per language)
    filename = request.filename.strip()
    
    # Update the custom filename
    upload.custom_filename = filename
    db.commit()
    
    return {"message": f"Filename set to {filename}", "filename": filename}
