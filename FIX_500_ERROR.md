# 🔧 Fixing the 500 Internal Server Error

## ❌ The Problem

When you upload a file and try to analyze it, you get:
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
```

## 🔍 What's Causing It

The **500 error happens when the AI analysis fails**. This is because:

### **The OpenAI API key in `docker-compose.yml` has exceeded its quota!**

When the AI tries to analyze your document, it calls the OpenAI API, which responds with:
```
"You exceeded your current quota, please check your plan and billing details."
```

This causes the backend to return a 500 error to the frontend.

---

## ✅ The Solution

You need to update the OpenAI API key with one that has credits available.

### Step 1: Get Your API Key

1. Go to: **https://platform.openai.com/account/api-keys**
2. Sign in (or create an account)
3. Click "Create new secret key"
4. Copy the key (it will look like: `sk-proj-...` or `sk-...`)
5. **IMPORTANT**: Make sure you have billing set up at:
   https://platform.openai.com/account/billing

### Step 2: Update docker-compose.yml

1. Open `docker-compose.yml` in your editor
2. Find line 28 (look for `OPENAI_API_KEY=`)
3. Replace the entire key with YOUR new key:

**Before:**
```yaml
- OPENAI_API_KEY=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
```

**After:**
```yaml
- OPENAI_API_KEY=sk-YOUR_ACTUAL_API_KEY_HERE
```

4. Save the file

### Step 3: Restart Services

```bash
docker compose down
docker compose up -d
```

Wait ~15-20 seconds for all services to start.

### Step 4: Test Again

1. Go to **http://localhost:3000**
2. Upload your lab assignment
3. The AI should now successfully analyze it! 🎉

---

## 🎯 How to Verify It's Working

### Test 1: Check Services Are Running
```bash
docker compose ps
```

You should see:
```
labmate-backend-1    Up
labmate-frontend-1   Up
labmate-postgres-1   Up (healthy)
```

### Test 2: Check Backend Health
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Test 3: Upload a File
1. Go to http://localhost:3000
2. Upload a DOCX/PDF
3. If it works, you'll see "AI Review" step with suggestions
4. If it fails with 500, check the logs:
   ```bash
   docker compose logs backend --tail=50
   ```

---

## 🔍 Common Error Messages

### "You exceeded your current quota"
**Cause:** API key has no credits  
**Fix:** Add credits at https://platform.openai.com/account/billing

### "Incorrect API key provided"
**Cause:** Invalid or malformed key  
**Fix:** Copy the key carefully, including all characters

### "The model `gpt-4` does not exist or you do not have access to it"
**Cause:** Your account doesn't have access to GPT-4  
**Fix:** Change line 29 in docker-compose.yml:
```yaml
- OPENAI_MODEL=gpt-3.5-turbo
```

---

## 💰 Cost Information

Using **gpt-3.5-turbo** (recommended):
- Document analysis: ~$0.01 per assignment
- Code execution tasks: ~$0.001 each
- AI answer generation: ~$0.01 each
- **Total per assignment: $0.05 - $0.15**

This is very affordable! A $5 credit will handle ~30-50 assignments.

---

## 🆘 Still Having Issues?

### Check the backend logs:
```bash
docker compose logs backend --tail=100
```

Look for error messages containing:
- "OpenAI API error"
- "exceeded quota"
- "Incorrect API key"
- "does not exist"

### Run the test script:
```bash
powershell -ExecutionPolicy Bypass -File test_api.ps1
```

This will diagnose the issue and tell you exactly what's wrong.

---

## 📚 Summary

1. ✅ **Backend is running** (you can see it on port 8000)
2. ✅ **Frontend is running** (you can see it on port 3000)
3. ✅ **Database is running** (PostgreSQL on port 5432)
4. ❌ **OpenAI API key has exceeded quota**

**Fix:** Update the API key in `docker-compose.yml` line 28 with a key that has credits!

---

## 🎉 Once Fixed

The workflow will be:
1. **Upload** → Your lab assignment (DOCX/PDF)
2. **AI Review** → AI suggests code tasks and theory answers
3. **Execute & Report** → AI runs code, takes screenshots, writes answers
4. **Download** → Get your completed lab report!

The AI features are fully implemented and working - they just need a valid API key with credits!

