#!/bin/bash

# ScanPro Docker Utilities (Bash)
# Shared functions for Docker scripts

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================

absolute_path() {
    local path="$1"
    
    # Handle empty input
    if [ -z "$path" ]; then
        echo "Error: No path provided to absolute_path()" >&2
        return 1
    fi
    
    # Try readlink -f first (works on most Linux systems)
    if command -v readlink >/dev/null 2>&1 && readlink -f "$path" >/dev/null 2>&1; then
        readlink -f "$path"
    # Try realpath as fallback (available on macOS and modern Linux)
    elif command -v realpath >/dev/null 2>&1; then
        realpath "$path"
    # Final fallback using cd/pwd (doesn't resolve symlinks)
    else
        # Check if path is a file or directory
        if [ -d "$path" ]; then
            (cd "$path" && pwd)
        elif [ -e "$path" ]; then
            # It's a file, get the directory and append filename
            local dir=$(dirname "$path")
            local file=$(basename "$path")
            (cd "$dir" && echo "$(pwd)/$file")
        else
            # Path doesn't exist yet, try to resolve parent directory
            local dir=$(dirname "$path")
            local file=$(basename "$path")
            if [ -d "$dir" ]; then
                echo "$(cd "$dir" && pwd)/$file"
            else
                echo "Error: Cannot resolve path '$path'" >&2
                return 1
            fi
        fi
    fi
}

# Get script directory and root directory
get_script_dirs() {
    # Get the last element of BASH_SOURCE array (the original calling script)
    local last_source_index=$((${#BASH_SOURCE[@]} - 1))
    SCRIPT_DIR=$(dirname $(absolute_path "${BASH_SOURCE[$last_source_index]}"))
    # Go up two levels from utils to root: utils -> docker -> scripts -> root
    ROOT_DIR=$(absolute_path "$SCRIPT_DIR/../..")
    ENV_FILE_PATH="$ROOT_DIR/.env"
    
    # Debug output for CI
    if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
        echo "🔍 Debug info:"
        echo "   SCRIPT_DIR: $SCRIPT_DIR"
        echo "   ROOT_DIR: $ROOT_DIR"
        echo "   Current dir: $(pwd)"
        echo "   Dockerfile exists: $([ -f "$ROOT_DIR/Dockerfile" ] && echo "yes" || echo "no")"
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE_PATH" ]; then
        echo "⚠️  Warning: .env file not found at $ENV_FILE_PATH"
        echo "   Container will run without environment variables"
    fi
}

# Get current git branch as tag
get_git_tag() {
    IMAGE_TAG=$(git branch --show-current 2>/dev/null || echo "latest")
    if [ "$IMAGE_TAG" = "main" ] || [ "$IMAGE_TAG" = "master" ]; then
        IMAGE_TAG="latest"
    fi
    echo "$IMAGE_TAG"
}

# ==========================================
# DOCKER FUNCTIONS
# ==========================================

# Check if Docker is running
check_docker() {
    echo "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Check if local image exists
check_local_image() {
    local image_name="$1"
    
    if docker images -q "$image_name" >/dev/null 2>&1; then
        echo "✅ Local image found: $image_name"
        return 0
    else
        echo "ℹ️  Local image not found: $image_name"
        return 1
    fi
}

# Pull image if not found locally
pull_image_if_needed() {
    local image_name="$1"
    
    if check_local_image "$image_name"; then
        return 0
    fi
    
    echo "📥 Pulling image from remote: $image_name"
    if ! docker pull "$image_name"; then
        echo "❌ Failed to pull image. Please check your internet connection and try again."
        echo "   Make sure the image exists: $image_name"
        exit 1
    fi
    echo "✅ Image pulled successfully"
}

# Stop existing container
stop_existing_container() {
    local container_name="$1"
    
    echo "Checking for existing container..."
    if docker ps -q --filter "name=$container_name" | grep -q .; then
        echo "🛑 Stopping running container..."
        docker stop "$container_name"
        docker rm "$container_name"
    elif docker ps -aq --filter "name=$container_name" | grep -q .; then
        echo "🛑 Removing stopped container..."
        docker rm "$container_name"
    else
        echo "ℹ️  No existing container found"
    fi
}

# ==========================================
# DISPLAY FUNCTIONS
# ==========================================

# Show build configuration
show_build_config() {
    local docker_username="$1"
    local repository_name="$2"
    local image_tag="$3"
    local platforms="$4"
    
    echo "📋 Build Configuration:"
    echo "   Docker Hub User: $docker_username"
    echo "   Repository: $repository_name"
    echo "   Tag: $image_tag"
    echo "   Platforms: $platforms"
    echo ""
}

# Show container information
show_container_info() {
    local container_name="$1"
    local image_name="$2"
    local frontend_port="$3"
    
    echo "📋 Container Information:"
    echo "   Name: $container_name"
    echo "   Image: $image_name"
    echo "   Frontend: http://localhost:$frontend_port"
    echo ""
}

# Show useful commands
show_useful_commands() {
    local container_name="$1"
    
    echo "🔧 Useful Commands:"
    echo "   View logs: docker logs -f $container_name"
    echo "   Stop: docker stop $container_name"
    echo "   Remove: docker rm $container_name"
    echo "   Shell access: docker exec -it $container_name /bin/bash"
    echo ""
}
