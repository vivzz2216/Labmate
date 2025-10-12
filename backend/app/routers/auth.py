from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import json
import os

from ..database import get_db
from ..models import User

router = APIRouter()

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Try to get Firebase credentials from individual environment variables first
        firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
        firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        firebase_client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        
        if firebase_project_id and firebase_private_key and firebase_client_email:
            try:
                # Create credentials from individual environment variables
                creds_dict = {
                    "type": "service_account",
                    "project_id": firebase_project_id,
                    "private_key": firebase_private_key.replace('\\n', '\n'),
                    "client_email": firebase_client_email,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully from individual env vars")
                return True
            except Exception as e:
                print(f"Failed to initialize Firebase from env vars: {e}")
        
        # Fallback to JSON string
        firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
        if not firebase_creds or firebase_creds == 'your-firebase-credentials-json':
            print("Firebase credentials not configured, authentication will be disabled")
            return False
        
        try:
            # Parse the credentials JSON
            creds_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully from JSON")
            return True
        except Exception as e:
            print(f"Failed to parse Firebase credentials: {e}")
            return False
    
    return True

# Initialize Firebase on module load
firebase_initialized = False
try:
    firebase_initialized = initialize_firebase()
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    firebase_initialized = False


class GoogleAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str
    profile_picture: Optional[str] = None
    created_at: str
    last_login: str


@router.post("/google", response_model=UserResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Verify Google ID token and create/update user
    """
    # Development mode - bypass Firebase verification if not configured
    if not firebase_initialized:
        print("Firebase not initialized, using development mode")
        # Create a mock user for development
        google_id = "dev_user_123"
        email = "dev@example.com"
        name = "Development User"
        profile_picture = ""
    else:
        try:
            # Verify the ID token with Firebase
            decoded_token = firebase_auth.verify_id_token(request.id_token)
            
            # Extract user information
            google_id = decoded_token['uid']
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')
            profile_picture = decoded_token.get('picture', '')
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID token"
            )
    
    try:
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if user:
            # Update existing user
            user.email = email
            user.name = name
            user.profile_picture = profile_picture
            user.last_login = func.now()
        else:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_picture=profile_picture
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            google_id=user.google_id,
            email=user.email,
            name=user.name,
            profile_picture=user.profile_picture,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get current user information
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        profile_picture=user.profile_picture,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat()
    )
