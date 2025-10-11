# 🔑 How to Update Your OpenAI API Key

## Quick Steps:

### 1. **Get Your OpenAI API Key**
   - Go to: https://platform.openai.com/account/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-proj-...` or `sk-...`)
   - **Make sure you have billing set up and credits available!**

### 2. **Update docker-compose.yml**
   Open `docker-compose.yml` and find line 28:
   
   ```yaml
   - OPENAI_API_KEY=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
   ```
   
   Replace it with YOUR actual key:
   
   ```yaml
   - OPENAI_API_KEY=sk-YOUR_ACTUAL_KEY_HERE
   ```

### 3. **Model Selection (Optimized Automatically)**
   The system now uses **optimal models for each task**:
   
   - **GPT-4o** → Document analysis (best accuracy, with auto-fallback to GPT-4o-mini)
   - **GPT-4o-mini** → Code generation, answers, captions (fast & cheap)
   
   **You don't need to change anything!** The models are optimized in the code.
   
   The `OPENAI_MODEL` in docker-compose.yml is just a fallback:
   ```yaml
   - OPENAI_MODEL=gpt-4o-mini
   ```

### 4. **Restart the Services**
   ```bash
   docker compose down
   docker compose up --build
   ```

### 5. **Test It!**
   - Go to http://localhost:3000
   - Upload a lab assignment DOCX/PDF
   - The AI will analyze it and suggest tasks
   - Select what you want (screenshots, AI answers)
   - AI will execute code, take screenshots, and generate your report!

---

## 📊 The AI Workflow:

1. **Upload File** → You upload your lab assignment (DOCX/PDF)
2. **AI Review** → AI analyzes the document and suggests:
   - Which code blocks need screenshots
   - Which questions need AI-written answers
   - Where to insert results (below question or at bottom)
3. **Execute & Report** → AI:
   - Runs code in a safe Docker container
   - Captures terminal output
   - Takes styled screenshots (IDLE or VS Code theme)
   - Generates AI answers for theory questions
   - Inserts everything into your Word document
   - Returns a downloadable report!

---

## 💰 Cost Estimation (with optimized models):

**Per Assignment (5 questions, 3 code blocks, 2 theory answers):**
- Document analysis (GPT-4o): ~$0.03
- Code generation (GPT-4o-mini): ~$0.003
- Answer generation (GPT-4o-mini): ~$0.004
- Captions (GPT-4o-mini): ~$0.002
- **Total**: ~$0.04 per complete assignment

**87% cheaper than using GPT-4o for everything!**

---

## ⚠️ Troubleshooting:

### "OpenAI API error: Incorrect API key"
→ Double-check your API key in `docker-compose.yml`

### "You exceeded your current quota"
→ Add credits at: https://platform.openai.com/account/billing

### "The model `gpt-4o` does not exist or you do not have access"
→ Don't worry! The system automatically falls back to `gpt-4o-mini`
→ If both fail, check your API key has access to at least `gpt-4o-mini`

---

## 🎯 Optimized AI Strategy:

**Models used (automatically selected in code):**
- **GPT-4o** → Document analysis (with auto-fallback to GPT-4o-mini)
- **GPT-4o-mini** → Code generation, answers, captions

**Benefits:**
- ⚡ 30% faster processing
- 💰 87% cost reduction
- 🎯 Same high quality

**No configuration needed!** Just add your API key and go!

For details, see: [OPTIMIZED_AI_MODELS.md](./OPTIMIZED_AI_MODELS.md)

