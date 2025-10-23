from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from .config import settings
from .database import engine, Base
from .routers import upload, parse, run, compose, download, analyze, tasks, assignments, basic_auth

# Create database tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"⚠ Warning: Could not create database tables: {e}")
    print("The application will continue, but database features may not work.")

# Create FastAPI app
app = FastAPI(
    title="LabMate AI API",
    description="Automated lab assignment processing platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # Allow all origins for Railway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files (Next.js export)
frontend_path = "/app/frontend"
if os.path.exists(frontend_path):
    # Mount static frontend files
    app.mount("/_next", StaticFiles(directory=f"{frontend_path}/_next"), name="next")
    app.mount("/static", StaticFiles(directory=f"{frontend_path}/_next/static"), name="static")

# Serve frontend for all non-API routes
@app.get("/{path:path}")
async def serve_frontend(path: str):
    # Don't serve frontend for API routes
    if path.startswith("api/") or path.startswith("health") or path.startswith("docs") or path.startswith("uploads") or path.startswith("screenshots") or path.startswith("reports") or path.startswith("public"):
        return {"message": "Not found"}
    
    # Serve frontend index.html for all other routes
    frontend_index = "/app/frontend/index.html"
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    else:
        return {"message": "Frontend not built. Please build the frontend first."}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "LabMate API is running"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "LabMate AI API", "version": "1.0.0"}

# Create directories if they don't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
os.makedirs("/app/public", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/screenshots", StaticFiles(directory=settings.SCREENSHOT_DIR), name="screenshots")
app.mount("/reports", StaticFiles(directory=settings.REPORT_DIR), name="reports")
app.mount("/public", StaticFiles(directory="/app/public"), name="public")

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(parse.router, prefix="/api", tags=["parse"])
app.include_router(run.router, prefix="/api", tags=["run"])
app.include_router(compose.router, prefix="/api", tags=["compose"])
app.include_router(download.router, prefix="/api", tags=["download"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(basic_auth.router, prefix="/api/basic-auth", tags=["basic-auth"])


@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": "LabMate AI API", "version": "1.0.0"}

@app.get("/api/test-patterns")
async def test_patterns():
    """Test endpoint to verify question pattern matching"""
    import re
    from .services.composer_service import ComposerService
    
    composer = ComposerService()
    test_texts = [
        "1.Write a Python program to demonstrate the use of iterator and generator functions.",
        "2.Write a Python program to calculate sum of first 5 natural numbers using recursion.",
        "B. Questions/Programs:",
        "Question 1: Write a program",
        "Task 2: Demonstrate recursion"
    ]
    
    results = {}
    for text in test_texts:
        pattern_match = composer._find_question_pattern(text)
        results[text] = {
            "matched": pattern_match is not None,
            "task_number": pattern_match
        }
    
    return {"pattern_tests": results}
