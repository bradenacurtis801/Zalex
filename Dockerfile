# Simple single-stage Dockerfile for ScanPro
# This avoids all the Python copying issues

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgcc-s1 \
    curl \
    ca-certificates \
    gnupg \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Install frontend dependencies and build
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm install && npm run build && npm prune --production

# Copy entrypoint script
WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 3000 5000

# Set environment variables
ENV NODE_ENV=production \
    BACKEND_PORT=5000 \
    BACKEND_HOST=0.0.0.0 \
    DEBUG=false \
    CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start both services
ENTRYPOINT ["/app/entrypoint.sh"]