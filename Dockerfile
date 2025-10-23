# Multi-stage build for full-stack LabMate application
# Stage 1: Build Frontend (Next.js)
FROM node:20-alpine AS frontend-builder

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY frontend/package*.json ./frontend/

# Install dependencies
RUN cd frontend && npm ci

# Copy source code
COPY frontend/ ./frontend/

# Sanity check: show directory structure before build
RUN echo ">>> WORKDIR: $(pwd)" && ls -la && echo ">>> files in frontend:" && ls -la frontend/

# Clean any existing build cache
RUN rm -rf frontend/.next

# Build frontend as static export
RUN echo "--- Starting Next.js static build ---" && \
    cd frontend && \
    npm run build && \
    echo "--- Build completed successfully ---" && \
    echo "--- Checking if out directory was created ---" && \
    ls -la out && \
    echo "--- Showing static files ---" && \
    find out -type f | head -20

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

# Copy static frontend from frontend builder
COPY --from=frontend-builder /app/frontend/out /app/frontend
COPY --from=frontend-builder /app/frontend/public /app/frontend/public

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