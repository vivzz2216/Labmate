# 🔴 URGENT: Fix the 500 Error in 3 Steps

## ❌ The Problem

You're getting a **500 Internal Server Error** because the OpenAI API key is still a placeholder!

Current key in `docker-compose.yml`:
```
sk-proj-YOUR_API_KEY_HERE_REPLACE_THIS
```

This is NOT a real API key - it needs to be replaced with YOUR actual key.

---

## ✅ Solution (3 Simple Steps)

### Step 1: Get Your OpenAI API Key

1. Go to: **https://platform.openai.com/account/api-keys**
2. Sign in (or create account if you don't have one)
3. Click **"Create new secret key"**
4. **Copy the entire key** (it starts with `sk-proj-` or `sk-`)

⚠️ **IMPORTANT:** You also need to add billing:
- Go to: **https://platform.openai.com/account/billing**
- Add a payment method
- Add at least $5 credit

---

### Step 2: Update docker-compose.yml

1. Open `docker-compose.yml` in your editor
2. Find **line 28** (it's already open in your IDE!)
3. Replace this line:
   ```yaml
   - OPENAI_API_KEY=sk-proj-YOUR_API_KEY_HERE_REPLACE_THIS
   ```
   
   With YOUR actual key:
   ```yaml
   - OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_PASTE_IT_HERE
   ```

4. **Save the file**

---

### Step 3: Restart Docker

Open your terminal and run:

```bash
docker compose down
docker compose up -d
```

Wait 15-20 seconds for services to start.

---

## 🧪 Test It

1. Go to **http://localhost:3000**
2. Upload your assignment again
3. ✅ It should work now!

---

## ⚠️ If You Don't Have an OpenAI Account

### Option 1: Create Free OpenAI Account
1. Go to: https://platform.openai.com/signup
2. Verify email
3. Add payment method (required even for trial)
4. Get $5 free trial credit
5. Follow steps above

### Option 2: Use Temporary Test Mode
**NOT RECOMMENDED** - The AI features won't work without a real key.

---

## 💰 Cost After You Fix It

With your API key:
- **Per assignment: ~$0.04**
- **$5 credit: ~125 assignments**
- **Very affordable!**

---

## 🔍 How to Verify Your Key Works

After updating and restarting, run this test:

```bash
docker compose exec backend python -c "import openai, os; openai.api_key = os.getenv('OPENAI_API_KEY'); print(openai.Model.list())"
```

If it shows a list of models → ✅ Key works!  
If it shows an error → ❌ Key is invalid, check it again

---

## 📋 Quick Checklist

- [ ] Got OpenAI API key from platform.openai.com
- [ ] Added billing and credits to OpenAI account
- [ ] Updated line 28 in docker-compose.yml with real key
- [ ] Saved docker-compose.yml
- [ ] Ran `docker compose down`
- [ ] Ran `docker compose up -d`
- [ ] Waited 15-20 seconds
- [ ] Tested at http://localhost:3000

---

## 🆘 Still Having Issues?

### Error: "You exceeded your current quota"
→ Add more credits at: https://platform.openai.com/account/billing

### Error: "Incorrect API key provided"
→ Copy the key again carefully, make sure you got the entire key

### Error: "The model `gpt-4o` does not exist"
→ The system will automatically fallback to `gpt-4o-mini` - this is normal!

---

## 🎯 Summary

**Current Status:**
- ❌ API key is placeholder: `sk-proj-YOUR_API_KEY_HERE_REPLACE_THIS`
- ❌ Can't call OpenAI without real key
- ❌ Getting 500 errors

**After Fix:**
- ✅ Real API key in docker-compose.yml
- ✅ AI analysis works
- ✅ Full workflow functional
- ✅ $0.04 per assignment

**Next Action:** Update docker-compose.yml line 28 with YOUR actual OpenAI API key!

