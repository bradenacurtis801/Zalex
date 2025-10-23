#!/bin/bash

# ScanPro Debug Container Runner
# This script runs the ScanPro container in debug mode

set -e

echo "🐛 Starting ScanPro in DEBUG mode..."

# Build the image if it doesn't exist
if ! docker image inspect bradenacurtis801/scanpro:latest >/dev/null 2>&1; then
    echo "📦 Building Docker image..."
    docker build -t bradenacurtis801/scanpro:latest .
fi

# Run the container in debug mode
echo "🚀 Starting container with debug port exposed..."
docker run -it \
  --name scanpro-debug \
  -p 3000:3000 \
  -p 5000:5000 \
  -p 5678:5678 \
  -e NODE_ENV=prod \
  -e DEBUG=1 \
  -e DEBUG=false \
  bradenacurtis801/scanpro:latest

echo "✅ Container started in debug mode!"
echo "   Backend: http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo "   Debug Port: 5678"
echo ""
echo "🔗 To attach debugger:"
echo "   1. Open VS Code"
echo "   2. Go to Run and Debug (Ctrl+Shift+D)"
echo "   3. Select 'Attach to Docker Container'"
echo "   4. Click the play button"
echo ""
echo "🛑 To stop: docker stop scanpro-debug"
