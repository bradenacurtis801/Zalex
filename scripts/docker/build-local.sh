#!/bin/bash

# Local Docker Build Script
# Builds image for local development and testing

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/utils.sh"

# ===========================================
# CONFIGURATION VARIABLES
# ===========================================

# Get directories
get_script_dirs

load_env $ENV_FILE_PATH

# Check and set Docker Hub configuration from environment variables
ensure_docker_username
ensure_docker_repo_name

# Get directories and git tag
DOCKER_FILE_PATH="$ROOT_DIR/Dockerfile"
IMAGE_TAG=$(get_git_tag)
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${REPOSITORY_NAME}:${IMAGE_TAG}"

# ===========================================
# SCRIPT FUNCTIONS
# ===========================================

# Function to show build information
show_build_info() {
    echo "📋 Local build configuration:"
    echo "   Tag: $FULL_IMAGE_NAME"
    echo "   Platform: $(docker version --format '{{.Server.Arch}}')"
    echo ""
}

# Function to build the image
build_image() {
    local full_image_name="$1"
    
    echo "🏗️  Building image for local development..."
    echo "   Platform: $(docker version --format '{{.Server.Arch}}')"
    echo "   Tag: $full_image_name"
    echo "   Also tagged as: ${DOCKER_USERNAME}/${REPOSITORY_NAME}:latest"
    echo ""
    
    docker build \
        --tag "$full_image_name" \
        --tag "${DOCKER_USERNAME}/${REPOSITORY_NAME}:latest" \
        -f "$DOCKER_FILE_PATH" \
        $ROOT_DIR
}

# ===========================================
# MAIN SCRIPT EXECUTION
# ===========================================

echo "🐳 Local Docker Build Script"
echo "====================================="
echo ""

# Check prerequisites
check_docker

# Show build information
show_build_info

# Build the image
echo "🚀 Starting local build process..."
build_image "$FULL_IMAGE_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Local build completed successfully!"
    echo ""
    echo "🎉 Done! Your local image is ready."
else
    echo "❌ Build failed!"
    exit 1
fi
