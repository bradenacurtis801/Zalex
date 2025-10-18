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
    postgresql \
    postgresql-client \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Set PostgreSQL environment variables
ENV PATH="/usr/lib/postgresql/17/bin:$PATH"
ENV PGDATA="/app/APP_DATA/db/postgres_data"

# Add PostgreSQL bin to system PATH for all users
RUN echo 'export PATH="/usr/lib/postgresql/17/bin:$PATH"' >> /etc/environment

# Create postgres user and set up permissions
RUN groupadd -r postgres || true && useradd -r -g postgres postgres || true
RUN mkdir -p /app/APP_DATA/db && chown -R postgres:postgres /app/APP_DATA/db

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

# UI and backend ports that are bound within the container
EXPOSE 3000 5000 5678

# Set environment variables for containerized environment
# These override the defaults in config.py for Docker containers
# This is just for documentation purposes (These are all the default values when not set)
ENV NODE_ENV=production \
    BACKEND_HOST=127.0.0.1 \
    DEBUG=0 \
    CORS_ORIGINS='["http://127.0.0.1:3000"]' \
    NEXT_PUBLIC_API_URL=http://127.0.0.1:5000 \
    POSTGRES_USERNAME=postgres \
    POSTGRES_PASSWORD=password \
    POSTGRES_DB_NAME=scanpro_db \
    POSTGRES_HOST=localhost \
    POSTGRES_PORT=5432

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start both services
ENTRYPOINT ["/app/entrypoint.sh"]