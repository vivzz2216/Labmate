#!/bin/bash

# Get PORT from Railway (defaults to 8000 if not set)
export PORT=${PORT:-8000}

echo "Environment variables:"
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:0:30}..."

echo "Using PORT from environment: $PORT"
echo "Starting LabMate Full-Stack Application on port $PORT"

# Start backend in background
echo "Starting FastAPI backend..."
cd /app
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting Next.js frontend..."
cd /app/frontend
npm start &

# Wait for both processes
wait
