# Username Feature - Visual Example

## How It Works

### Step 1: User Signs Up

```
User enters:
- Email: vivek.pillai@example.com
- Name: Vivek Pillai
- Password: ********
```

### Step 2: Database Storage

```sql
INSERT INTO users (email, name, google_id, created_at)
VALUES ('vivek.pillai@example.com', 'Vivek Pillai', NULL, NOW());
```

Database now contains:
```
id  | email                      | name          | created_at
----|----------------------------|---------------|------------------
1   | vivek.pillai@example.com   | Vivek Pillai  | 2025-10-20 10:30
```

### Step 3: User Uploads Assignment

```
User actions:
1. Upload document: "Python_Assignment_5.docx"
2. Set custom filename: "exp5"
3. Click "Analyze" or "Run Tasks"
```

### Step 4: System Processing

```python
# Backend extracts first name
full_name = "Vivek Pillai"           # From database
first_name = full_name.split()[0]    # Extract first part
# first_name = "Vivek"

# Generate screenshot with personalized path
username = "Vivek"
filename = "exp5.py"
path = f"C:/Users/{username}/OneDrive/Desktop/{filename}"
# Result: "C:/Users/Vivek/OneDrive/Desktop/exp5.py"
```

### Step 5: Generated Screenshot

The screenshot will display:

```
┌─────────────────────────────────────────────────────────────────┐
│ exp5.py - C:/Users/Vivek/OneDrive/Desktop/exp5.py (3.10.0)     │
├─────────────────────────────────────────────────────────────────┤
│ File  Edit  Format  Run  Options  Window  Help                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  # Python code here                                             │
│  print("Hello, World!")                                         │
│                                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Python 3.10.0 Shell                                             │
├─────────────────────────────────────────────────────────────────┤
│ File  Edit  Shell  Debug  Options  Window  Help                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Python 3.10.0 (tags/v3.10.0:1234567, Oct 11 2025) on win32     │
│ >>>                                                              │
│ ========== RESTART: C:/Users/Vivek/OneDrive/Desktop/exp5.py == │
│ Hello, World!                                                   │
│ >>>                                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Notice:** 
- Title bar shows: `C:/Users/Vivek/OneDrive/Desktop/exp5.py`
- Shell restart line shows: `C:/Users/Vivek/OneDrive/Desktop/exp5.py`
- **Both use "Vivek" (first name only), not "Vivek Pillai"**

## Comparison: Different Users

### User 1: Sarah Johnson

```
Name stored: "Sarah Johnson"
First name extracted: "Sarah"
Path displayed: C:/Users/Sarah/OneDrive/Desktop/assignment1.py
```

### User 2: Muhammad Ali Khan

```
Name stored: "Muhammad Ali Khan"
First name extracted: "Muhammad"
Path displayed: C:/Users/Muhammad/OneDrive/Desktop/lab3.py
```

### User 3: Priya

```
Name stored: "Priya"
First name extracted: "Priya"
Path displayed: C:/Users/Priya/OneDrive/Desktop/exp10.py
```

### No User (Fallback)

```
Name stored: NULL or empty
First name extracted: "User" (default)
Path displayed: C:/Users/User/OneDrive/Desktop/code.py
```

## Code Flow Diagram

```
┌──────────────┐
│ User Signs Up│
│ Name: "Vivek │
│    Pillai"   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Database    │
│ Stores Full  │
│     Name     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ User Uploads │
│  Assignment  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ Backend Processes Upload     │
│ 1. Query user by user_id     │
│ 2. Get user.name             │
│ 3. Split: name.split()[0]    │
│ 4. username = "Vivek"        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Generate Screenshot          │
│ 1. Load template             │
│ 2. Replace {{ username }}    │
│ 3. Replace {{ filename }}    │
│ 4. Render HTML               │
│ 5. Capture screenshot        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Screenshot Saved             │
│ Path: /screenshots/68/       │
│       screenshot_abc123.png  │
│                              │
│ Displays:                    │
│ C:/Users/Vivek/OneDrive/     │
│ Desktop/exp5.py              │
└──────────────────────────────┘
```

## Technical Implementation

### 1. Name Extraction Function

```python
def extract_first_name(full_name: str) -> str:
    """
    Extract first name from full name.
    
    Examples:
        "Vivek Pillai" -> "Vivek"
        "John Doe" -> "John"
        "Sarah" -> "Sarah"
        "" -> "User"
    """
    if not full_name or not full_name.strip():
        return "User"
    
    return full_name.split()[0]
```

### 2. Usage in Code

```python
# Get user from database
user = db.query(User).filter(User.id == upload.user_id).first()

# Extract first name
if user and user.name:
    username = user.name.split()[0]  # Smart extraction
else:
    username = "User"  # Fallback

# Pass to screenshot service
screenshot_service.generate_screenshot(
    code=code,
    output=output,
    theme="idle",
    job_id=job.id,
    username=username,      # ← First name here
    filename="exp5.py"
)
```

### 3. Template Rendering

```jinja2
<!-- Template: idle_theme.html -->
<div class="title-bar">
    <span>{{ filename }} - C:/Users/{{ username }}/OneDrive/Desktop/{{ filename }}</span>
</div>

<!-- After rendering with username="Vivek", filename="exp5.py" -->
<div class="title-bar">
    <span>exp5.py - C:/Users/Vivek/OneDrive/Desktop/exp5.py</span>
</div>
```

## Why First Name Only?

1. **Privacy:** Students might not want full names visible
2. **Simplicity:** Cleaner display, easier to read
3. **Realistic:** Windows usernames are typically short
4. **Professional:** Matches real Windows username conventions

## Edge Cases Handled

| Input Name         | Extracted Name | Path Result                           |
|-------------------|----------------|---------------------------------------|
| "Vivek Pillai"    | "Vivek"        | C:/Users/Vivek/OneDrive/Desktop/...  |
| "John"            | "John"         | C:/Users/John/OneDrive/Desktop/...   |
| "" (empty)        | "User"         | C:/Users/User/OneDrive/Desktop/...   |
| "   " (spaces)    | "User"         | C:/Users/User/OneDrive/Desktop/...   |
| "Jean-Claude Van" | "Jean-Claude"  | C:/Users/Jean-Claude/OneDrive/...    |

## Summary

✅ **Feature Status:** Fully Implemented  
✅ **Automatic:** Works for all users without configuration  
✅ **Personalized:** Each user sees their own first name  
✅ **Secure:** Only extracts publicly visible first name  
✅ **Tested:** Works across both AI and regular job processing  

---

**Questions?** Check the main documentation at `docs/USERNAME_FEATURE.md`

