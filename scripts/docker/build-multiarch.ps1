# Multi-Architecture Docker Build and Push Script (PowerShell)
# Builds multi-architecture image and pushes to Docker Hub
#
# Authentication:
# This script assumes the Docker user is already logged in with credentials
# being handled by Docker itself (via `docker login`). The GitHub workflow
# handles logging into Docker before this automated script runs.


# Load utilities
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$SCRIPT_DIR\utils\utils.ps1"

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================
Get-ScriptDirs
Import-Env -EnvFile $ENV_FILE_PATH

# Check and set Docker Hub configuration from environment variables
Ensure-DockerUsername
Ensure-DockerRepoName
$DOCKER_USERNAME = $script:DOCKER_USERNAME
$REPOSITORY_NAME = $script:REPOSITORY_NAME

# Get directories and git tag
$DOCKER_FILE_PATH = Join-Path $ROOT_DIR "Dockerfile"
$IMAGE_TAG = Get-GitTag

# Build Configuration
$BUILDER_NAME = "multiarch-builder"
$PLATFORMS = "linux/amd64,linux/arm64"

# ==========================================
# SCRIPT FUNCTIONS
# ==========================================

function Test-Git {
    Write-Host "Checking Git repository..." -ForegroundColor Yellow
    
    try {
        git status | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Not in git repository"
        }
        Write-Host "Git repository detected, using branch: $IMAGE_TAG" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Not in a git repository, using 'latest' as tag" -ForegroundColor Yellow
        $script:IMAGE_TAG = "latest"
        return $true
    }
}

function Initialize-Buildx {
    Write-Host "Setting up Docker Buildx..." -ForegroundColor Yellow
    
    # Check if buildx is available
    try {
        docker buildx version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Buildx not available"
        }
    }
    catch {
        Write-Host "Docker Buildx is not available. Please update Docker to a newer version." -ForegroundColor Red
        return $false
    }
    
    # Create or use existing builder
    try {
        docker buildx inspect $BUILDER_NAME | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Creating new buildx builder: $BUILDER_NAME" -ForegroundColor Cyan
            docker buildx create --name $BUILDER_NAME --use
        } else {
            Write-Host "Using existing buildx builder: $BUILDER_NAME" -ForegroundColor Green
            docker buildx use $BUILDER_NAME
        }
    }
    catch {
        Write-Host "Failed to setup buildx builder" -ForegroundColor Red
        return $false
    }
    
    # Bootstrap the builder
    Write-Host "Bootstrapping builder..." -ForegroundColor Cyan
    docker buildx inspect --bootstrap
    
    return $true
}

function Show-ImageInfo {
    $FULL_IMAGE_NAME = "$DOCKER_USERNAME/$REPOSITORY_NAME`:$IMAGE_TAG"
    
    Write-Host "Multi-architecture image that will be created:" -ForegroundColor Cyan
    Write-Host "   Tag: $FULL_IMAGE_NAME" -ForegroundColor Gray
    Write-Host "   Branch: $IMAGE_TAG" -ForegroundColor Gray
    Write-Host "   Platforms: $PLATFORMS" -ForegroundColor Gray
    Write-Host ""
    
    return $FULL_IMAGE_NAME
}

function Invoke-BuildAndPush {
    param($FullImageName)
    
    Write-Host "Building and pushing multi-architecture image..." -ForegroundColor Yellow
    Write-Host "   Repository: $DOCKER_USERNAME/$REPOSITORY_NAME" -ForegroundColor Gray
    Write-Host "   Tag: $IMAGE_TAG" -ForegroundColor Gray
    Write-Host "   Branch: $IMAGE_TAG" -ForegroundColor Gray
    Write-Host "   Platforms: $PLATFORMS" -ForegroundColor Gray
    Write-Host ""
    
    # Run docker buildx with real-time output using Start-Process
    $process = Start-Process -FilePath "docker" -ArgumentList "buildx", "build", "--platform", $PLATFORMS, "--tag", $FullImageName, "--tag", "$DOCKER_USERNAME/$REPOSITORY_NAME`:latest", "--push", "-f", $DOCKER_FILE_PATH, $ROOT_DIR -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Host "Build and push failed!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Multi-architecture image built and pushed successfully" -ForegroundColor Green
    return $true
}

function Show-Usage {
    param($FullImageName)
    
    Write-Host "After pushing, you can pull and run the multi-architecture image with:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   # Pull and run the image (will auto-select correct architecture)" -ForegroundColor Gray
    Write-Host "   docker pull $FullImageName" -ForegroundColor White
    Write-Host "   docker run -p 3000:3000 -p 5000:5000 $FullImageName" -ForegroundColor White
    Write-Host ""
    Write-Host "   # Pull for specific platform" -ForegroundColor Gray
    Write-Host "   docker pull --platform linux/amd64 $FullImageName" -ForegroundColor White
    Write-Host "   docker pull --platform linux/arm64 $FullImageName" -ForegroundColor White
    Write-Host ""
    Write-Host "   # Or use docker-compose with the image" -ForegroundColor Gray
    Write-Host "   # Update docker-compose.yml to use: image: $FullImageName" -ForegroundColor White
}

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================

Write-Host "Multi-Architecture Docker Build and Push Script" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Auto-push mode: Will build and push to Docker Hub automatically" -ForegroundColor Yellow
Write-Host ""

# Check prerequisites
if (-not (Test-Docker)) {
    exit 1
}

if (-not (Test-Git)) {
    exit 1
}

# Setup buildx
if (-not (Initialize-Buildx)) {
    exit 1
}

# Show configuration
Write-Host "Build Configuration:" -ForegroundColor Cyan
Write-Host "   Docker Hub User: $DOCKER_USERNAME" -ForegroundColor Gray
Write-Host "   Repository: $REPOSITORY_NAME" -ForegroundColor Gray
Write-Host "   Tag: $IMAGE_TAG" -ForegroundColor Gray
Write-Host "   Branch: $IMAGE_TAG" -ForegroundColor Gray
Write-Host "   Builder: $BUILDER_NAME" -ForegroundColor Gray
Write-Host "   Platforms: $PLATFORMS" -ForegroundColor Gray
Write-Host ""

# Construct and show image URLs
$FULL_IMAGE_NAME = Show-ImageInfo

# Build and push the image
Write-Host "Starting multi-architecture build and push process..." -ForegroundColor Yellow
if (-not (Invoke-BuildAndPush -FullImageName $FULL_IMAGE_NAME)) {
    exit 1
}

Write-Host "Multi-architecture build and push completed successfully!" -ForegroundColor Green
Write-Host ""

# Show usage instructions
Show-Usage -FullImageName $FULL_IMAGE_NAME

Write-Host "Done! Your multi-architecture image is now available on Docker Hub." -ForegroundColor Green
Write-Host ""
