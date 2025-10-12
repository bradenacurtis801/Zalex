#!/bin/bash

# ScanPro Entrypoint Script
# Starts both FastAPI backend and Next.js frontend

set -e

echo "🚀 Starting ScanPro Services..."

# Normalize NODE_ENV for Next.js compatibility
if [ "$NODE_ENV" = "dev" ]; then
    export NODE_ENV=development
    echo "📝 Normalized NODE_ENV: dev → development"
elif [ "$NODE_ENV" = "prod" ]; then
    export NODE_ENV=production
    echo "📝 Normalized NODE_ENV: prod → production"
fi

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start backend
echo "📡 Starting FastAPI backend on port 5000..."
cd /app/backend

# Check DEBUG mode
if [ "$DEBUG" = "1" ]; then
    echo "🐛 Starting backend in DEBUG mode with debugpy (waiting for client) on port 5678..."
    python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py &
elif [ "$DEBUG" = "2" ]; then
    echo "🐛 Starting backend in DEBUG mode with debugpy (no wait) on port 5678..."
    python -m debugpy --listen 0.0.0.0:5678 main.py &
else
    echo "🚀 Starting backend in production mode..."
    python main.py &
fi
BACKEND_PID=$!

# Start frontend in background
echo "🌐 Starting Next.js frontend on port 3000..."
cd /app/frontend
npm start &
FRONTEND_PID=$!

echo "✅ Both services started!"
echo "   Backend: http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:5000/docs"

# Wait for backend process - if it dies, container exits
wait $BACKEND_PID