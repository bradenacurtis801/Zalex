#!/bin/bash

# ScanPro Entrypoint Script
# Starts both FastAPI backend and Next.js frontend

set -e

echo "🚀 Starting ScanPro Services..."

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start backend
echo "📡 Starting FastAPI backend on port ${BACKEND_PORT:-5000}..."
cd /app/backend
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting Next.js frontend on port 3000..."
cd /app/frontend
npm start &
FRONTEND_PID=$!

# Wait for both processes
echo "✅ Both services started successfully!"
echo "   Backend: http://localhost:${BACKEND_PORT:-5000}"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:${BACKEND_PORT:-5000}/docs"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
