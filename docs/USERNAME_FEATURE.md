# Dynamic Username in File Paths Feature

## Overview

This document explains how the system dynamically extracts and displays the user's first name in file paths shown in generated screenshots.

## Feature Description

When a user signs up with their name (e.g., "Vivek Pillai"), the system:
1. Stores the full name in the database
2. Extracts the **first name only** when generating screenshots
3. Displays personalized file paths like: `C:/Users/Vivek/OneDrive/Desktop/exp5.py`

## Implementation Details

### 1. User Model (Database)

**File:** `backend/app/models.py`

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)  # Stores full name: "Vivek Pillai"
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), server_default=func.now())
    
    uploads = relationship("Upload", back_populates="user")
```

### 2. First Name Extraction Logic

The system extracts the first name using Python's `split()` method:

#### AI Job Processing (`task_service.py`)

**File:** `backend/app/services/task_service.py` (Lines 163-167)

```python
# Extract first name from full name
if user and user.name:
    username = user.name.split()[0]  # "Vivek Pillai" → "Vivek"
else:
    username = "User"  # Fallback if no user found
```

#### Regular Job Processing (`run.py`)

**File:** `backend/app/routers/run.py` (Lines 79-86)

```python
# Get user information for personalized display
user = db.query(User).filter(User.id == upload.user_id).first() if upload.user_id else None

# Extract first name from full name
if user and user.name:
    username = user.name.split()[0]  # Get first name only (e.g., "Vivek" from "Vivek Pillai")
else:
    username = "User"
```

### 3. Screenshot Template Integration

**File:** `backend/templates/idle_theme.html`

The template uses Jinja2 template variables to display the username:

```html
<!-- Title Bar (Line 159) -->
<span>{{ filename }} - C:/Users/{{ username }}/OneDrive/Desktop/{{ filename }} (3.10.0)</span>

<!-- Shell Output Header (Line 197) -->
========== RESTART: C:/Users/{{ username }}/OneDrive/Desktop/{{ filename }} ==========
```

### 4. Screenshot Generation Service

**File:** `backend/app/services/screenshot_service.py`

The screenshot service accepts `username` and `filename` parameters:

```python
async def generate_screenshot(
    self, 
    code: str, 
    output: str, 
    theme: str = "idle",
    job_id: int = None,
    username: str = "User",      # Receives first name here
    filename: str = "new.py"
) -> Tuple[bool, str, int, int]:
```

## Usage Flow

### Example: User "Vivek Pillai" Signs Up

1. **Signup:**
   - User enters email: `vivek@example.com`
   - User enters name: `Vivek Pillai`
   - System stores: `name = "Vivek Pillai"` in database

2. **Upload Assignment:**
   - User uploads a Python assignment document
   - User sets custom filename: `exp5` (becomes `exp5.py`)
   - Upload is linked to user ID

3. **Generate Screenshots:**
   - System retrieves user from database
   - Extracts first name: `"Vivek Pillai".split()[0]` → `"Vivek"`
   - Generates screenshot with path: `C:/Users/Vivek/OneDrive/Desktop/exp5.py`

4. **Result:**
   - Screenshots show personalized paths
   - No hardcoded usernames
   - Works for any user automatically

## Supported Name Formats

| Full Name Input      | Extracted First Name |
|---------------------|---------------------|
| `Vivek Pillai`      | `Vivek`            |
| `John Doe`          | `John`             |
| `Mary Jane Watson`  | `Mary`             |
| `Ali`               | `Ali`              |
| `Jean-Claude`       | `Jean-Claude`      |

## Fallback Behavior

If no user is found or the name field is empty:
- System uses default username: `"User"`
- Path becomes: `C:/Users/User/OneDrive/Desktop/filename.py`

## Benefits

1. **Personalization:** Each student sees their own name in screenshots
2. **Professionalism:** Generated documents look authentic
3. **Automatic:** No manual configuration needed
4. **Privacy-Friendly:** Only first name is displayed (not full name)
5. **Consistent:** Same logic across AI and regular job processing

## Testing the Feature

### Test Case 1: New User Signup

1. Sign up with name "Vivek Pillai"
2. Upload a Python assignment
3. Set filename as "exp5"
4. Generate screenshots
5. **Expected Result:** Path shows `C:/Users/Vivek/OneDrive/Desktop/exp5.py`

### Test Case 2: Different User

1. Sign up with name "Sarah Johnson"
2. Upload assignment
3. Generate screenshots
4. **Expected Result:** Path shows `C:/Users/Sarah/OneDrive/Desktop/...`

### Test Case 3: Single Name

1. Sign up with name "Priya"
2. Upload assignment
3. **Expected Result:** Path shows `C:/Users/Priya/OneDrive/Desktop/...`

## Code Files Modified

1. ✅ `backend/app/routers/run.py` - Added username extraction for regular jobs
2. ✅ `backend/app/services/task_service.py` - Already had username extraction for AI jobs
3. ✅ `backend/templates/idle_theme.html` - Already uses `{{ username }}` template variable
4. ✅ `backend/app/services/screenshot_service.py` - Already accepts username parameter

## Configuration

No configuration needed! The feature works automatically for all users.

## Troubleshooting

### Issue: Screenshots show "User" instead of real name

**Cause:** User record not linked to upload

**Solution:**
- Ensure uploads are properly associated with user IDs
- Check that `upload.user_id` is set when files are uploaded

### Issue: Full name appears instead of first name

**Cause:** Code not splitting the name properly

**Solution:**
- Verify the `user.name.split()[0]` logic is in place
- Check that changes were deployed to production

## Future Enhancements

Possible improvements:
1. Allow users to customize display name separately
2. Support different path formats (Linux, Mac)
3. Add organization/class name to paths
4. Multi-language name support

---

**Last Updated:** October 20, 2025  
**Status:** ✅ Fully Implemented & Tested

