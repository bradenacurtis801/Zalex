#!/bin/bash

# Docker Utilities (Bash)
# Shared functions for Docker scripts

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================

# Generic function to ensure an environment variable is set
# Usage: ensure_env_var "VARIABLE_NAME" "friendly-name" "example-value"
ensure_env_var() {
    local var_name="$1"
    local friendly_name="${2:-$var_name}"
    local example_value="${3:-your-value}"
    
    # Use indirect variable reference to check if variable is set
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo "❌ ERROR: $friendly_name environment variable is required but not set" >&2
        echo "   Please set it with: export $var_name='$example_value'" >&2
        exit 1
    fi
    
    # Export the variable so it's available to the calling script
    export "$var_name"
}

# Specific wrapper functions for Docker configuration
ensure_docker_username() {
    ensure_env_var "DOCKER_USERNAME" "DOCKER_USERNAME" "your-dockerhub-username"
}

ensure_docker_repo_name() {
    ensure_env_var "REPOSITORY_NAME" "REPOSITORY_NAME" "your-repository-name"
}

ensure_docker_volume_or_path() {
    ensure_env_var "VOLUME_NAME_OR_PATH" "VOLUME_NAME_OR_PATH" "your_volume_name_or_path"
}

# Check and set Docker Hub configuration from environment variables
# Exits with error if required variables are not set
# This is a convenience function that checks both username and repo name
ensure_docker_hub_config() {
    ensure_docker_username
    ensure_docker_repo_name
}

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
}

# Load environment variables from a file
# Usage: load_env /path/to/.env
# Exports all variables from the file into the current shell environment
load_env() {
    local env_file="$1"
    
    # Check if file path was provided
    if [ -z "$env_file" ]; then
        echo "❌ Error: load_env() requires ENV_FILE argument" >&2
        echo "   Usage: load_env /path/to/.env" >&2
        return 1
    fi
    
    # Check if file exists
    if [ ! -f "$env_file" ]; then
        echo "⚠️  Warning: Environment file not found: $env_file" >&2
        return 1
    fi
    
    # Enable auto-export mode so all variables are exported
    set -a
    
    # Source the file, ignoring errors from comments and empty lines
    # This will export all valid variable assignments
    . "$env_file" 2>/dev/null || true
    
    # Disable auto-export mode
    set +a
}

# Get current git branch as tag
get_git_tag() {
    IMAGE_TAG=$(git branch --show-current 2>/dev/null || echo "latest")
    if [ "$IMAGE_TAG" = "main" ] || [ "$IMAGE_TAG" = "master" ]; then
        IMAGE_TAG="latest"
    fi
    echo "$IMAGE_TAG"
}

# Try to resolve a file path at the project root
# Usage: try_resolve_file <filename> [optional_full_path]
# Returns the path to the file, determining it if not provided
try_resolve_file() {
    local filename="$1"
    local file_path="$2"
    
    # If full path is already provided, return it
    if [ -n "$file_path" ]; then
        echo "$file_path"
        return 0
    fi
    
    # First, try to use ROOT_DIR if it's already set
    if [ -n "$ROOT_DIR" ]; then
        echo "$ROOT_DIR/$filename"
        return 0
    fi
    
    # Try to calculate root directory similar to get_script_dirs
    # Get the directory where this script is located
    local script_file="${BASH_SOURCE[0]}"
    if [ -z "$script_file" ]; then
        script_file="${0}"
    fi
    local script_dir="$(cd "$(dirname "$script_file")" && pwd)"
    # Go up three levels: utils -> docker -> scripts -> root
    local calculated_root=$(absolute_path "$script_dir/../../..")
    
    # Verify it's the right directory by checking for Dockerfile
    if [ -f "$calculated_root/Dockerfile" ]; then
        echo "$calculated_root/$filename"
        return 0
    fi
    
    # Fallback: search from current directory
    local current_dir="$(pwd)"
    local search_dir="$current_dir"
    
    # Walk up the directory tree looking for Dockerfile
    while [ "$search_dir" != "/" ]; do
        if [ -f "$search_dir/Dockerfile" ]; then
            echo "$search_dir/$filename"
            return 0
        fi
        search_dir="$(dirname "$search_dir")"
    done
    
    # If still not found, use current directory
    echo "$current_dir/$filename"
}

# Create .env file with template
create_env_file() {
    local env_file_path=$(try_resolve_file ".env" "${1:-$ENV_FILE_PATH}")
    
    # Check if .env already exists
    if [ -f "$env_file_path" ]; then
        echo "ℹ️  .env file already exists at $env_file_path"
        return 0
    fi
    
    # Get the .env.example file path
    local env_example_path=$(try_resolve_file ".env.example")
    
    # Check if .env.example exists
    if [ ! -f "$env_example_path" ]; then
        echo "❌ Error: .env.example file not found at $env_example_path" >&2
        echo "   Please create a .env.example file at the project root." >&2
        return 1
    fi
    
    # Copy .env.example to .env
    cp "$env_example_path" "$env_file_path"
    
    echo "✅ Created .env file at $env_file_path from $env_example_path"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Open the .env file: $env_file_path"
    echo "   2. Update the environment variables as needed"
    echo ""
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

# Remove Docker volume
remove_volume() {
    local volume_name="$1"
    
    if [ -z "$volume_name" ]; then
        echo "Error: No volume name provided to remove_volume()" >&2
        return 1
    fi
    
    # Check if volume exists
    if ! docker volume inspect "$volume_name" >/dev/null 2>&1; then
        echo "ℹ️  Volume '$volume_name' does not exist"
        return 0
    fi
    
    # Find containers using this volume
    local containers=$(docker ps -a --filter "volume=$volume_name" --format "{{.Names}}")
    
    if [ -n "$containers" ]; then
        echo "⚠️  Warning: The following containers are using volume '$volume_name':"
        echo "$containers" | while read -r container; do
            echo "   - $container"
        done
        echo ""
        echo "   Stopping and removing containers..."
        echo "$containers" | while read -r container; do
            docker stop "$container" 2>/dev/null
            docker rm "$container" 2>/dev/null
        done
    fi
    
    # Remove the volume
    echo "🗑️  Removing volume '$volume_name'..."
    if docker volume rm "$volume_name" 2>/dev/null; then
        echo "✅ Volume '$volume_name' removed successfully"
        return 0
    else
        echo "❌ Failed to remove volume '$volume_name'"
        return 1
    fi
}

# Check if a port is open/available
is_port_open() {
    local port="$1"
    
    if [ -z "$port" ]; then
        echo "Error: No port provided to is_port_open()" >&2
        return 2
    fi
    
    # Check if port is a valid number
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        echo "Error: Invalid port number: $port" >&2
        return 2
    fi
    
    # Check if port is in valid range
    if [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo "Error: Port must be between 1 and 65535" >&2
        return 2
    fi
    
    # Try different methods based on OS
    # macOS and Linux both support lsof
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 1  # Port is in use
        else
            return 0  # Port is open
        fi
    # Fallback to netstat (older systems)
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"; then
            return 1  # Port is in use
        else
            return 0  # Port is open
        fi
    # Final fallback: try to bind to the port (requires nc or similar)
    elif command -v nc >/dev/null 2>&1; then
        if nc -z localhost $port 2>/dev/null; then
            return 1  # Port is in use
        else
            return 0  # Port is open
        fi
    else
        echo "Warning: Cannot check port availability (lsof/netstat/nc not found)" >&2
        # Assume port is open if we can't check
        return 0
    fi
}

# Find an open port starting from the given port, incrementing until one is found
find_open_port() {
    local start_port="$1"
    local max_attempts="${2:-100}"  # Default to 100 attempts
    local current_port="$start_port"
    local attempts=0
    
    if [ -z "$start_port" ]; then
        echo "Error: No starting port provided to find_open_port()" >&2
        return 1
    fi
    
    # Validate starting port
    if ! [[ "$start_port" =~ ^[0-9]+$ ]] || [ "$start_port" -lt 1 ] || [ "$start_port" -gt 65535 ]; then
        echo "Error: Invalid starting port: $start_port" >&2
        return 1
    fi
    
    while [ $attempts -lt $max_attempts ]; do
        if is_port_open "$current_port"; then
            echo "$current_port"
            return 0
        fi
        
        # Increment port
        current_port=$((current_port + 1))
        attempts=$((attempts + 1))
        
        # Don't exceed max port number
        if [ "$current_port" -gt 65535 ]; then
            echo "Error: Reached maximum port number (65535) without finding an open port" >&2
            return 1
        fi
    done
    
    echo "Error: Could not find an open port after $max_attempts attempts starting from $start_port" >&2
    return 1
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
