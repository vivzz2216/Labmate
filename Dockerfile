# Multi-stage build for full-stack LabMate application
# Stage 1: Build Frontend (Next.js)
FROM node:20-alpine AS frontend-builder

# Be explicit about working directory
WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Sanity check: show directory structure before build
RUN echo ">>> WORKDIR: $(pwd)" && ls -la && echo ">>> files in frontend:" && ls -la .

# Clean any existing build cache
RUN rm -rf .next

# Build frontend with verbose output and error handling
RUN echo "--- Starting Next.js build ---" && \
    npm run build --verbose 2>&1 | tee build.log && \
    echo "--- Build completed successfully ---" && \
    cat build.log && \
    echo "--- Checking build exit code ---" && \
    echo "Build exit code: $?" && \
    echo "--- Checking if .next directory was created during build ---" && \
    ls -la .next || echo ".next directory not found during build!" && \
    echo "--- Checking for any build artifacts ---" && \
    find . -name "*.js" -o -name "*.css" -o -name "*.html" | head -10 && \
    echo "--- Checking for any error logs ---" && \
    find . -name "*.log" -o -name "*.error" | head -5 && \
    echo "--- Checking Next.js version ---" && \
    npm list next && \
    echo "--- Checking if Next.js is properly installed ---" && \
    npx next --version && \
    echo "--- Checking Next.js configuration ---" && \
    cat next.config.js && \
    echo "--- Checking package.json build script ---" && \
    cat package.json | grep -A 5 -B 5 "build" && \
    echo "--- Trying to run Next.js build manually ---" && \
    npx next build --verbose && \
    echo "--- Checking if .next was created after manual build ---" && \
    ls -la .next || echo ".next still not found after manual build"

# Verify .next directory was created (will fail build early if not)
RUN echo "--- Final verification: .next directory ---" && \
    ls -la .next || (echo "ERROR: .next directory not found!" && exit 1)

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