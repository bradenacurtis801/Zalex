#!/bin/bash

# ScanPro Run Script (Linux/Mac)
# Runs the ScanPro containers

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


# Check if .env file exists
if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE_PATH"
    echo "   The .env file is required for the container to run properly."
    echo ""
    echo "   To create a .env file with a template, run:"
    echo "   source scripts/docker/utils/utils.sh && create_env_file"
    echo ""
    echo "   Or manually create it at: $ENV_FILE_PATH"
    exit 1
fi

# ==========================================
# FUNCTIONS
# ==========================================

run_container() {
    echo "🐳 Starting ScanPro container..."
    echo "   Container name: $CONTAINER_NAME"
    echo "   Image: $IMAGE_NAME"
    echo ""

    # Check if the desired port is available
    if is_port_open "$FRONTEND_PORT"; then
        # Port is available, use it
        open_frontend_port="$FRONTEND_PORT"
        echo "✅ Port $FRONTEND_PORT is available"
    else
        # Port is in use
        echo "⚠️  Port $FRONTEND_PORT is already in use"
        echo ""
        
        # Find an open port
        echo "🔍 Finding available port starting from $FRONTEND_PORT..."
        open_frontend_port=$(find_open_port "$FRONTEND_PORT")
        port_find_exit_code=$?
        
        if [ $port_find_exit_code -ne 0 ] || [ -z "$open_frontend_port" ] || ! [[ "$open_frontend_port" =~ ^[0-9]+$ ]]; then
            echo "❌ Failed to find an available port starting from $FRONTEND_PORT"
            exit 1
        fi
        
        # Ask for confirmation
        echo "   Found available port: $open_frontend_port"
        echo ""
        read -p "   Do you want to run on port $open_frontend_port instead? (y/n): " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Aborted. Please free up port $FRONTEND_PORT or choose a different port."
            exit 1
        fi
    fi
    
    echo "   Using port: $open_frontend_port"
    echo ""

    docker run -it --rm \
        --name $CONTAINER_NAME \
        -p $open_frontend_port:3000 \
        -v scanpro_data:/app/APP_DATA \
        --env-file $ENV_FILE_PATH \
        -e DEBUG=0 \
        $IMAGE_NAME

    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "❌ Failed to start container (exit code: $exit_code)"
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

# Check if image exists and pull if needed
if ! pull_image_if_needed "$IMAGE_NAME"; then
    echo "Failed to pull required image. Exiting."
    echo "   You can build the image locally by running: scripts/docker/build-local.sh"
    exit 1
fi

# Run container
run_container