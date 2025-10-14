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

# Get current git branch as tag
IMAGE_TAG=$(git branch --show-current 2>/dev/null || echo "latest")
if [ "$IMAGE_TAG" = "main" ] || [ "$IMAGE_TAG" = "master" ]; then
    IMAGE_TAG="latest"
fi

# Build Configuration
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

# Function to check git status
check_git() {
    if ! git status > /dev/null 2>&1; then
        echo "⚠️  Not in a git repository, using 'latest' as tag"
        IMAGE_TAG="latest"
    else
        echo "✅ Git repository detected, using branch: $IMAGE_TAG"
    fi
}

# Function to construct image URLs
construct_image_urls() {
    # Construct the full image name
    FULL_IMAGE_NAME="${DOCKER_USERNAME}/${REPOSITORY_NAME}:${IMAGE_TAG}"
    
    echo "📋 Image that will be created:"
    echo "   Tag: $FULL_IMAGE_NAME"
    echo "   Branch: $IMAGE_TAG"
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
        
        docker build \
            --tag scanpro:latest \
            .
    else
        echo "🏗️  Building image..."
        echo "   Repository: $DOCKER_USERNAME/$REPOSITORY_NAME"
        echo "   Tag: $IMAGE_TAG"
        echo "   Branch: $IMAGE_TAG"
        echo ""
        
        docker build \
            --tag $FULL_IMAGE_NAME \
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
    echo "   # Pull and run the image"
    echo "   docker pull $FULL_IMAGE_NAME"
    echo "   docker run -p 3000:3000 -p 5000:5000 $FULL_IMAGE_NAME"
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
check_git

# Show configuration
echo "📋 Build Configuration:"
echo "   Docker Hub User: $DOCKER_USERNAME"
echo "   Repository: $REPOSITORY_NAME"
echo "   Tag: $IMAGE_TAG"
echo "   Branch: $IMAGE_TAG"
echo ""

# Construct and show image URLs
construct_image_urls

# Build the image
echo "🚀 Starting build process..."
build_image

if [ "$BUILD_ONLY" = true ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "📖 You can now run the image locally with:"
    echo "   docker run -p 3000:3000 -p 5000:5000 scanpro:latest"
else
    echo "✅ Build completed successfully!"
    echo ""
    
    # Ask if user wants to push
    echo "🔨 Ready to push the image to Docker Hub."
    ask_confirmation
    
    # Push the image
    echo "🚀 Pushing image to Docker Hub..."
    docker push $FULL_IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        echo "✅ Push completed successfully!"
        echo ""
        # Show usage instructions
        show_usage
        echo "🎉 Done! Your ScanPro image is now available on Docker Hub."
    else
        echo "❌ Push failed!"
        exit 1
    fi
fi
