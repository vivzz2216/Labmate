# 🔑 OpenAI API Key Setup

## The Issue
You're getting a 500 error because the OpenAI API key is not configured. The system needs a valid OpenAI API key to analyze documents and generate AI suggestions.

## How to Fix

### Step 1: Get Your OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (starts with `sk-`)

### Step 2: Update the Configuration
Edit the `docker-compose.yml` file and replace this line:
```yaml
- OPENAI_API_KEY=your_openai_api_key_here
```

With your actual API key:
```yaml
- OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 3: Restart the Services
```bash
docker compose down
docker compose up -d
```

## Alternative: Using Environment File
You can also create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Then restart the services.

## Cost Information
- **GPT-4o-mini**: Very affordable (~$0.15 per 1M input tokens)
- **Typical usage**: $0.01-0.10 per document analysis
- **Free tier**: OpenAI offers $5 free credits for new accounts

## Security Note
Never commit your API key to version control. Always use environment variables or `.env` files.
