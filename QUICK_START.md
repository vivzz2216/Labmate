# 🚀 LabMate AI - Quick Start Guide

## ✅ What's Ready

Your LabMate AI is now fully configured with the **AI-powered workflow**!

## 🔑 Step 1: Update Your OpenAI API Key

Open `docker-compose.yml` and find line 28:

```yaml
- OPENAI_API_KEY=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
```

**Replace with YOUR API key:**

```yaml
- OPENAI_API_KEY=sk-YOUR_ACTUAL_KEY_HERE
```

Get your key from: https://platform.openai.com/account/api-keys

⚠️ **Make sure you have billing set up and credits available!**

## 🏃 Step 2: Run the Application

```bash
# Stop current services (if running)
docker compose down

# Start everything
docker compose up --build
```

Wait ~30 seconds for services to start.

## 🌐 Step 3: Use the Application

1. Open your browser: **http://localhost:3000**

2. **Upload** your lab assignment (DOCX or PDF)

3. **AI Review**: The AI will analyze and suggest:
   - Code blocks to execute with screenshots
   - Theory questions that need AI answers
   - Where to insert results

4. **Select & Edit**:
   - ✅ Check the tasks you want
   - ✏️ Edit code if needed
   - 📍 Choose insertion locations
   - 🎨 Pick theme (IDLE/VS Code)

5. **Execute**: Click "Submit Tasks"
   - AI runs code in Docker
   - Generates screenshots
   - Writes theory answers
   - Creates captions

6. **Download**: Get your completed Word document!

## 🎯 The AI Workflow (3 Simple Steps)

```
1. UPLOAD FILE
   ↓
2. AI REVIEW (Select what you want)
   ↓
3. EXECUTE & REPORT (Download result)
```

## 📝 Example

**Your Document:**
```
Question 1: Write a program to print first 10 Fibonacci numbers.
Question 2: Explain recursion in Python.
Question 3: Implement bubble sort.
```

**AI Will:**
1. Generate Fibonacci code → Run → Screenshot
2. Write recursion explanation (with example)
3. Generate bubble sort code → Run → Screenshot

**You Get:** Complete Word document with code, outputs, screenshots, and explanations!

## 💰 Cost (with gpt-3.5-turbo)

- Per assignment: ~$0.05 - $0.15
- Very affordable for students!

## 🎨 Features

✅ **AI-powered analysis** - Understands your assignment  
✅ **Code execution** - Safe Docker sandbox  
✅ **Screenshots** - Editor + Terminal views  
✅ **AI answers** - Theory questions explained  
✅ **Smart insertion** - Below questions or at bottom  
✅ **Professional themes** - IDLE or VS Code style  
✅ **Downloadable reports** - Ready to submit!  

## ⚠️ Important Notes

1. **Old workflow removed** - No more manual task selection
2. **AI-only** - Everything is AI-powered now
3. **Requires credits** - OpenAI API needs billing setup
4. **Safe execution** - All code runs in isolated containers

## 📚 More Info

- **Detailed guide**: [AI_WORKFLOW_GUIDE.md](./AI_WORKFLOW_GUIDE.md)
- **API key help**: [UPDATE_API_KEY.md](./UPDATE_API_KEY.md)
- **Full docs**: [README.md](./README.md)

## 🆘 Troubleshooting

**"Analysis failed: You exceeded your current quota"**
→ Add credits: https://platform.openai.com/account/billing

**"The model `gpt-4` does not exist"**
→ Change line 29 in `docker-compose.yml` to:
```yaml
- OPENAI_MODEL=gpt-3.5-turbo
```

**"Incorrect API key"**
→ Double-check your key in `docker-compose.yml` line 28

## ✨ You're All Set!

1. Update API key in `docker-compose.yml`
2. Run `docker compose up --build`
3. Go to http://localhost:3000
4. Upload your assignment
5. Let AI do the magic! 🎉

---

**Current Status:** ✅ All services running  
**Frontend:** http://localhost:3000  
**Backend:** http://localhost:8000  
**Database:** PostgreSQL on port 5432  

**Next Step:** Update your OpenAI API key and test with a real assignment!

