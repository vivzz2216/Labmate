#!/bin/sh
# Startup script for Railway deployment

# Set default port if PORT is not set
if [ -z "$PORT" ]; then
    PORT=8000
fi

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
