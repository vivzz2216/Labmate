# Multi-stage build for full-stack LabMate application
# Stage 1: Build Frontend (Next.js)
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code (including lib directory)
COPY frontend/ ./

# Verify lib directory exists and show full directory structure
RUN ls -la && echo "--- Checking for lib directory ---" && ls -la lib/ || echo "lib directory not found" && echo "--- Checking if lib exists as file ---" && find . -name "lib" -type d && echo "--- Contents of lib directory if it exists ---" && ls -la lib/ 2>/dev/null || echo "lib directory not accessible"

# Clean any existing build cache
RUN rm -rf .next

# Build frontend with verbose output
RUN npm run build --verbose

# Verify .next directory was created
RUN ls -la && echo "--- Checking for .next directory ---" && ls -la .next/ || echo ".next directory not found"

# Stage 2: Build Backend (Python + FastAPI)
FROM python:3.10-slim

# Install system dependencies including Playwright dependencies and Java
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    # Java JDK for Java code execution
    default-jdk \
    # Playwright dependencies
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and browsers
RUN pip install playwright==1.40.0
RUN playwright install chromium

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy built frontend from frontend builder
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next
COPY --from=frontend-builder /app/frontend/public /app/frontend/public
COPY --from=frontend-builder /app/frontend/package*.json /app/frontend/

# Explicitly copy public images
COPY backend/app/public /app/public

# Create necessary directories
RUN mkdir -p /app/uploads /app/screenshots /app/reports

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port (Railway will set PORT environment variable)
EXPOSE 8000

# Run the application
CMD ["/app/start.sh"]