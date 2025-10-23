#!/bin/bash

# ScanPro Local Docker Build Script
# Builds image for local development and testing

set -e

# ===========================================
# CONFIGURATION VARIABLES
# ===========================================

# Build Configuration
IMAGE_TAG="local"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_FILE_PATH="$SCRIPT_DIR/../../Dockerfile"

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

# Function to show build information
show_build_info() {
    echo "📋 Local build configuration:"
    echo "   Tag: scanpro:local"
    echo "   Platform: $(docker version --format '{{.Server.Arch}}')"
    echo ""
}

# Function to build the image
build_image() {
    echo "🏗️  Building image for local development..."
    echo "   Platform: $(docker version --format '{{.Server.Arch}}')"
    echo "   Tag: scanpro:local"
    echo ""
    
    docker build \
        --tag scanpro:local \
        -f "$DOCKER_FILE_PATH" \
        .
}

# Function to show usage instructions
show_usage_instructions() {
    echo "📖 You can now run the image locally with:"
    echo ""
    echo "   # Run the local image"
    echo "   docker run -p 3000:3000 -p 5000:5000 scanpro:local"
    echo ""
    echo "   # Or use docker-compose with the local image"
    echo "   # Update docker-compose.yml to use: image: scanpro:local"
}

# ===========================================
# MAIN SCRIPT EXECUTION
# ===========================================

echo "🐳 ScanPro Local Docker Build Script"
echo "====================================="
echo ""

# Check prerequisites
check_docker

# Show build information
show_build_info

# Build the image
echo "🚀 Starting local build process..."
build_image

if [ $? -eq 0 ]; then
    echo "✅ Local build completed successfully!"
    echo ""
    # Show usage instructions
    show_usage_instructions
    echo "🎉 Done! Your local ScanPro image is ready."
else
    echo "❌ Build failed!"
    exit 1
fi
