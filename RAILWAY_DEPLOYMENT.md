# Railway Deployment Guide

## Prerequisites
- Railway account (free tier available)
- GitHub repository with your code
- OpenAI API key

## Deployment Steps

### 1. Backend Deployment

1. **Connect Repository to Railway**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Backend Service**
   - Railway will detect the `railway.json` file
   - It will use the root `Dockerfile` for backend deployment
   - Add PostgreSQL database:
     - Click "New" → "Database" → "PostgreSQL"
     - Railway will automatically set `DATABASE_URL` environment variable

3. **Set Environment Variables**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   BETA_KEY=your_beta_key_here
   ```

4. **Deploy**
   - Railway will automatically build and deploy using the Dockerfile
   - The backend will be available at: `https://your-app-name.railway.app`

### 2. Frontend Deployment

1. **Create Second Service**
   - In the same Railway project, click "New" → "GitHub Repo"
   - Select the same repository
   - Railway will detect `frontend/railway.json`

2. **Set Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-app-name.railway.app
   ```

3. **Deploy**
   - Railway will build the frontend using `frontend/Dockerfile`
   - The frontend will be available at: `https://your-frontend-app-name.railway.app`

### 3. Database Setup

1. **Run Migrations**
   - Connect to your Railway PostgreSQL database
   - Run the SQL migrations from `backend/migrations/`

2. **Verify Connection**
   - Check that the backend can connect to the database
   - Test the `/health` endpoint

## Environment Variables

### Backend
- `DATABASE_URL` - Automatically provided by Railway PostgreSQL
- `OPENAI_API_KEY` - Your OpenAI API key
- `BETA_KEY` - Your beta key for API access
- `PORT` - Automatically set by Railway

### Frontend
- `NEXT_PUBLIC_API_URL` - URL of your deployed backend
- `PORT` - Automatically set by Railway

## File Structure for Railway

```
/
├── railway.json              # Backend Railway config
├── Dockerfile                 # Backend Dockerfile
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── railway.json          # Frontend Railway config
│   ├── Dockerfile            # Frontend Dockerfile
│   ├── package.json
│   └── ...
└── README.md
```

## Troubleshooting

1. **Build Failures**
   - Check Railway logs for build errors
   - Ensure all dependencies are in requirements.txt/package.json

2. **Database Connection Issues**
   - Verify DATABASE_URL is set correctly
   - Check PostgreSQL service is running

3. **API Connection Issues**
   - Verify NEXT_PUBLIC_API_URL points to correct backend URL
   - Check CORS settings in backend

4. **File Upload Issues**
   - Ensure upload directories exist
   - Check file size limits

## Cost Considerations

- Railway free tier includes:
  - $5 credit per month
  - 512MB RAM per service
  - 1GB storage
  - 100GB bandwidth

- For production use, consider upgrading to paid plans for:
  - More resources
  - Better performance
  - Priority support
