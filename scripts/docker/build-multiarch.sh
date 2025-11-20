#!/bin/bash

# Multi-Architecture Docker Build and Push Script
# Builds multi-architecture image and pushes to Docker Hub
#
# Authentication:
# This script assumes the Docker user is already logged in with credentials
# being handled by Docker itself (via `docker login`). The GitHub workflow
# handles logging into Docker before this automated script runs.

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/utils.sh"

# ===========================================
# CONFIGURATION VARIABLES
# ===========================================
get_script_dirs
load_env $ENV_FILE_PATH

# Check and set Docker Hub configuration from environment variables
ensure_docker_username
ensure_docker_repo_name

# Get directories and git tag
DOCKER_FILE_PATH="$ROOT_DIR/Dockerfile"
IMAGE_TAG=$(get_git_tag)

# Verify Dockerfile exists, with fallback
if [ ! -f "$DOCKER_FILE_PATH" ]; then
    echo "⚠️  Dockerfile not found at: $DOCKER_FILE_PATH"
    echo "   Current directory: $(pwd)"
    echo "   ROOT_DIR: $ROOT_DIR"
    echo "   SCRIPT_DIR: $SCRIPT_DIR"
    
    # Try current directory as fallback
    if [ -f "Dockerfile" ]; then
        echo "✅ Found Dockerfile in current directory, using that instead"
        DOCKER_FILE_PATH="Dockerfile"
        ROOT_DIR="$(pwd)"
    else
        echo "❌ Dockerfile not found in current directory either"
        exit 1
    fi
fi

# Build Configuration
BUILDER_NAME="multiarch-builder"
PLATFORMS="linux/amd64,linux/arm64"

# ===========================================
# SCRIPT FUNCTIONS
# ===========================================

# Function to check git status
check_git() {
    if ! git status > /dev/null 2>&1; then
        echo "⚠️  Not in a git repository, using 'latest' as tag"
        IMAGE_TAG="latest"
    else
        echo "✅ Git repository detected, using branch: $IMAGE_TAG"
    fi
}

# Function to setup buildx builder
setup_buildx() {
    echo "🔧 Setting up Docker Buildx..."
    
    # Check if buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        echo "❌ Docker Buildx is not available. Please update Docker to a newer version."
        exit 1
    fi
    
    # Create or use existing builder
    if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
        echo "📦 Creating new buildx builder: $BUILDER_NAME"
        docker buildx create --name $BUILDER_NAME --use
    else
        echo "✅ Using existing buildx builder: $BUILDER_NAME"
        docker buildx use $BUILDER_NAME
    fi
    
    # Bootstrap the builder
    echo "🚀 Bootstrapping builder..."
    docker buildx inspect --bootstrap
}

# Function to construct image URLs
construct_image_urls() {
    # Construct the full image name
    FULL_IMAGE_NAME="${DOCKER_USERNAME}/${REPOSITORY_NAME}:${IMAGE_TAG}"
    
    echo "📋 Multi-architecture image that will be created:"
    echo "   Tag: $FULL_IMAGE_NAME"
    echo "   Branch: $IMAGE_TAG"
    echo "   Platforms: $PLATFORMS"
    echo ""
}


# Function to build and push multi-architecture image
build_and_push_multiarch() {
    echo "🏗️  Building and pushing multi-architecture image..."
    echo "   Platforms: $PLATFORMS"
    echo "   Repository: $DOCKER_USERNAME/$REPOSITORY_NAME"
    echo "   Tag: $IMAGE_TAG"
    echo ""
    
    docker buildx build \
        --platform $PLATFORMS \
        --tag $FULL_IMAGE_NAME \
        --tag ${DOCKER_USERNAME}/${REPOSITORY_NAME}:latest \
        --push \
        -f "$DOCKER_FILE_PATH" \
        "$ROOT_DIR"
}


# Function to show usage instructions
show_usage_instructions() {
    echo "📖 After pushing, you can pull and run the multi-architecture image with:"
    echo ""
    echo "   # Pull and run the image (will auto-select correct architecture)"
    echo "   docker pull $FULL_IMAGE_NAME"
    echo "   docker run -p 3000:3000 -p 5000:5000 $FULL_IMAGE_NAME"
    echo ""
    echo "   # Pull for specific platform"
    echo "   docker pull --platform linux/amd64 $FULL_IMAGE_NAME"
    echo "   docker pull --platform linux/arm64 $FULL_IMAGE_NAME"
    echo ""
    echo "   # Or use docker-compose with the image"
    echo "   # Update docker-compose.yml to use: image: $FULL_IMAGE_NAME"
}

# Function to show platform information
show_platform_info() {
    echo "🔍 Platform Information:"
    echo "   Supported platforms: $PLATFORMS"
    echo "   Current system: $(uname -m)"
    echo "   Docker architecture: $(docker version --format '{{.Server.Arch}}')"
    echo ""
}

# ===========================================
# MAIN SCRIPT EXECUTION
# ===========================================

echo "🐳 Multi-Architecture Docker Build and Push Script"
echo "=========================================================="
echo ""

echo "🔧 Auto-push mode: Will build and push to Docker Hub automatically"
echo ""

# Check prerequisites
check_docker
check_git

# Show platform information
show_platform_info

# Show configuration
echo "📋 Build Configuration:"
echo "   Docker Hub User: $DOCKER_USERNAME"
echo "   Repository: $REPOSITORY_NAME"
echo "   Tag: $IMAGE_TAG"
echo "   Branch: $IMAGE_TAG"
echo "   Builder: $BUILDER_NAME"
echo ""

# Construct and show image URLs
construct_image_urls

# Setup buildx
setup_buildx

# Build and push the image
echo "🚀 Starting multi-architecture build and push process..."
build_and_push_multiarch

if [ $? -eq 0 ]; then
    echo "✅ Multi-architecture build and push completed successfully!"
    echo ""
    # Show usage instructions
    show_usage_instructions
    echo "🎉 Done! Your multi-architecture image is now available on Docker Hub."
else
    echo "❌ Build and push failed!"
    exit 1
fi
