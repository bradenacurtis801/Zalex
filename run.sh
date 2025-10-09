#!/bin/bash

# ScanPro Run Script (Linux/Mac)
# Runs the ScanPro containers

set -e

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================

IMAGE_NAME="bradenacurtis801/scanpro:latest"
CONTAINER_NAME="scanpro"
FRONTEND_PORT="3000"
BACKEND_PORT="5000"

# ==========================================
# FUNCTIONS
# ==========================================

check_docker() {
    echo "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

stop_existing() {
    echo "Checking for existing container..."
    if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
        echo "🛑 Stopping existing container..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
    fi
}

pull_image() {
    echo "📥 Pulling latest image..."
    if ! docker pull $IMAGE_NAME; then
        echo "❌ Failed to pull image. Please check your internet connection and try again."
        echo "   Make sure the image exists: $IMAGE_NAME"
        exit 1
    fi
    echo "✅ Image pulled successfully"
}

run_container() {
    echo "🐳 Starting ScanPro container..."
    docker run -d \
        --name $CONTAINER_NAME \
        -p $FRONTEND_PORT:$FRONTEND_PORT \
        -p $BACKEND_PORT:$BACKEND_PORT \
        -v scanpro_data:/app/backend/APP_DATA \
        --restart unless-stopped \
        $IMAGE_NAME

    if [ $? -ne 0 ]; then
        echo "❌ Failed to start container!"
        exit 1
    fi
}

show_status() {
    echo ""
    echo "✅ ScanPro is running!"
    echo ""
    echo "📋 Container Information:"
    echo "   Name: $CONTAINER_NAME"
    echo "   Image: $IMAGE_NAME"
    echo "   Frontend: http://localhost:$FRONTEND_PORT"
    echo "   Backend: http://localhost:$BACKEND_PORT"
    echo "   API Docs: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "📊 Container Status:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs: docker logs -f $CONTAINER_NAME"
    echo "   Stop: docker stop $CONTAINER_NAME"
    echo "   Remove: docker rm $CONTAINER_NAME"
    echo "   Shell access: docker exec -it $CONTAINER_NAME /bin/bash"
    echo ""
}

show_help() {
    echo "📖 Usage: ./run.sh [options]"
    echo ""
    echo "Options:"
    echo "   --help, -h     Show this help message"
    echo "   --no-pull      Skip pulling image (use local only)"
    echo "   --stop         Stop and remove existing container"
    echo ""
}

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================

# Parse command line arguments
NO_PULL=""
STOP_ONLY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --no-pull)
            NO_PULL="1"
            shift
            ;;
        --stop)
            STOP_ONLY="1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "🚀 ScanPro Run Script"
echo "===================="
echo ""

# Check prerequisites
check_docker

# Stop existing container
stop_existing

# Handle stop-only option
if [ -n "$STOP_ONLY" ]; then
    echo "✅ Container stopped and removed."
    exit 0
fi

# Pull image (unless NO_PULL is specified)
if [ -z "$NO_PULL" ]; then
    pull_image
fi

# Run container
run_container

# Show status
show_status

echo "🎉 ScanPro is ready to use!"
echo ""
