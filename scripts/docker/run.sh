#!/bin/bash

# ScanPro Run Script (Linux/Mac)
# Runs the ScanPro containers

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/utils.sh"

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================

DOCKER_USERNAME="bradenacurtis801"
REPOSITORY_NAME="scanpro"

# Get directories and git tag
get_script_dirs
IMAGE_TAG=$(get_git_tag)
IMAGE_NAME="${DOCKER_USERNAME}/${REPOSITORY_NAME}:${IMAGE_TAG}"
CONTAINER_NAME="scanpro"
FRONTEND_PORT="3000"

# ==========================================
# FUNCTIONS
# ==========================================

run_container() {
    echo "🐳 Starting ScanPro container..."
    echo "   Container name: $CONTAINER_NAME"
    echo "   Frontend port: $FRONTEND_PORT"
    echo "   Image: $IMAGE_NAME"
    echo ""

    docker run -it --rm \
        --name $CONTAINER_NAME \
        -p $FRONTEND_PORT:3000 \
        -v scanpro_data:/app/APP_DATA \
        --env-file $ENV_FILE_PATH \
        -e DEBUG=0 \
        $IMAGE_NAME

    if [ $? -ne 0 ]; then
        echo "❌ Failed to start container!"
        echo "   Check if port $FRONTEND_PORT is already in use"
        echo "   Try: netstat -an | grep :$FRONTEND_PORT"
        echo "   Check container logs: docker logs $CONTAINER_NAME"
        exit 1
    fi
    echo "✅ Container started successfully"
}

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================

echo "🚀 ScanPro Run Script"
echo "===================="
echo ""

# Check prerequisites
check_docker

# Stop existing container
stop_existing_container "$CONTAINER_NAME"

# Run container
run_container