#!/bin/bash

# ScanPro Docker Hub Build and Push Script
# Builds multi-architecture image and pushes to Docker Hub

set -e

# ===========================================
# CONFIGURATION VARIABLES
# ===========================================

# Docker Hub Configuration
DOCKER_USERNAME="bradenacurtis801"
REPOSITORY_NAME="scanpro"
IMAGE_TAG="latest"

# Build Configuration
PLATFORMS="linux/amd64,linux/arm64"
BUILDER_NAME="scanpro-hub-builder"

# ===========================================
# SCRIPT FUNCTIONS
# ===========================================

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if buildx is available
check_buildx() {
    if ! docker buildx version > /dev/null 2>&1; then
        echo "❌ Docker Buildx is not available. Please install Docker Desktop or enable buildx."
        exit 1
    fi
}

# Function to setup buildx builder
setup_builder() {
    if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
        echo "🔧 Creating new buildx builder: $BUILDER_NAME"
        docker buildx create --name $BUILDER_NAME --use
    else
        echo "🔧 Using existing buildx builder: $BUILDER_NAME"
        docker buildx use $BUILDER_NAME
    fi
}

# Function to construct image URLs
construct_image_urls() {
    # Construct the full image name
    FULL_IMAGE_NAME="${DOCKER_USERNAME}/${REPOSITORY_NAME}:${IMAGE_TAG}"
    
    # Construct additional tags
    AMD64_TAG="${DOCKER_USERNAME}/${REPOSITORY_NAME}:amd64"
    ARM64_TAG="${DOCKER_USERNAME}/${REPOSITORY_NAME}:arm64"
    
    echo "📋 Image URLs that will be created:"
    echo "   Main: $FULL_IMAGE_NAME"
    echo "   AMD64: $AMD64_TAG"
    echo "   ARM64: $ARM64_TAG"
    echo ""
}

# Function to build the image
build_image() {
    if [ "$1" = "--build-only" ]; then
        echo "🏗️  Building image for local architecture only..."
        echo "   Platform: $(docker version --format '{{.Server.Arch}}')"
        echo "   Repository: $DOCKER_USERNAME/$REPOSITORY_NAME"
        echo "   Tag: $IMAGE_TAG"
        echo ""
        
        docker buildx build \
            --platform linux/amd64 \
            --tag scanpro:latest \
            --load \
            .
    else
        echo "🏗️  Building multi-architecture image..."
        echo "   Platforms: $PLATFORMS"
        echo "   Repository: $DOCKER_USERNAME/$REPOSITORY_NAME"
        echo "   Tag: $IMAGE_TAG"
        echo ""
        
        docker buildx build \
            --platform $PLATFORMS \
            --tag $FULL_IMAGE_NAME \
            --tag $AMD64_TAG \
            --tag $ARM64_TAG \
            --push \
            .
    fi
}

# Function to ask for confirmation
ask_confirmation() {
    echo "🤔 Do you want to push the built image to Docker Hub? (y/n)"
    read -r response
    case $response in
        [yY]|[yY][eE][sS])
            return 0
            ;;
        [nN]|[nN][oO])
            echo "❌ Push cancelled by user."
            exit 0
            ;;
        *)
            echo "❌ Invalid response. Please answer y or n."
            ask_confirmation
            ;;
    esac
}

# Function to show usage instructions
show_usage() {
    echo "📖 After pushing, you can pull and run the image with:"
    echo ""
    echo "   # Pull and run the latest version"
    echo "   docker pull $FULL_IMAGE_NAME"
    echo "   docker run -p 3000:3000 -p 5000:5000 $FULL_IMAGE_NAME"
    echo ""
    echo "   # Or pull specific architecture"
    echo "   docker pull $AMD64_TAG    # Intel"
    echo "   docker pull $ARM64_TAG    # Apple M1"
    echo ""
    echo "   # Or use docker-compose with the image"
    echo "   # Update docker-compose.yml to use: image: $FULL_IMAGE_NAME"
}

# ===========================================
# MAIN SCRIPT EXECUTION
# ===========================================

echo "🐳 ScanPro Docker Hub Build and Push Script"
echo "=============================================="
echo ""

# Check for build-only flag
BUILD_ONLY=false
if [ "$1" = "--build-only" ]; then
    BUILD_ONLY=true
    echo "🔧 Build-only mode: Will not push to Docker Hub"
    echo ""
fi

# Check prerequisites
check_docker
check_buildx

# Show configuration
echo "📋 Build Configuration:"
echo "   Docker Hub User: $DOCKER_USERNAME"
echo "   Repository: $REPOSITORY_NAME"
echo "   Tag: $IMAGE_TAG"
echo "   Platforms: $PLATFORMS"
echo ""

# Construct and show image URLs
construct_image_urls

# Setup buildx builder
setup_builder

# Ask for confirmation before building (unless build-only mode)
if [ "$BUILD_ONLY" = false ]; then
    echo "🔨 Ready to build and push the image."
    ask_confirmation
else
    echo "🔨 Ready to build the image locally."
fi

# Build and push the image
echo "🚀 Starting build process..."
if [ "$BUILD_ONLY" = true ]; then
    build_image --build-only
    echo "✅ Build completed successfully!"
    echo ""
    echo "📖 You can now run the image locally with:"
    echo "   docker run -p 3000:3000 -p 5000:5000 scanpro:latest"
else
    build_image
    echo "✅ Build and push completed successfully!"
    echo ""
    # Show usage instructions
    show_usage
    echo "🎉 Done! Your ScanPro image is now available on Docker Hub."
fi
