# ScanPro Docker Utilities (PowerShell)
# Shared functions for Docker scripts

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================

# Get script directory and root directory
function Get-ScriptDirs {
    # Get the directory of the utils script
    $script:SCRIPT_DIR = Split-Path -Parent $PSScriptRoot
    $script:ROOT_DIR = Join-Path $SCRIPT_DIR "..\.."
    $script:ENV_FILE_PATH = Join-Path $ROOT_DIR ".env"
    
    # Check if .env file exists
    if (-not (Test-Path $script:ENV_FILE_PATH)) {
        Write-Host "Warning: .env file not found at $script:ENV_FILE_PATH" -ForegroundColor Yellow
        Write-Host "   Container will run without environment variables" -ForegroundColor Gray
    }
}

# Get current git branch as tag
function Get-GitTag {
    try {
        $IMAGE_TAG = git branch --show-current 2>$null
        if (-not $IMAGE_TAG) {
            $IMAGE_TAG = "latest"
        }
        if ($IMAGE_TAG -eq "main" -or $IMAGE_TAG -eq "master") {
            $IMAGE_TAG = "latest"
        }
        return $IMAGE_TAG
    }
    catch {
        return "latest"
    }
}

# ==========================================
# DOCKER FUNCTIONS
# ==========================================

# Check if Docker is running
function Test-Docker {
    Write-Host "Checking Docker..." -ForegroundColor Yellow
    
    try {
        docker info | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker not running"
        }
        Write-Host "Docker is running" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Docker is not running. Please start Docker and try again." -ForegroundColor Red
        return $false
    }
}

# Check if local image exists
function Test-LocalImage {
    param($ImageName)
    
    try {
        $localImage = docker images -q $ImageName 2>$null
        if ($localImage) {
            Write-Host "Local image found: $ImageName" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Local image not found: $ImageName" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "Local image not found: $ImageName" -ForegroundColor Yellow
        return $false
    }
}

# Pull image if not found locally
function Invoke-PullImageIfNeeded {
    param($ImageName)
    
    if (Test-LocalImage -ImageName $ImageName) {
        return $true
    }
    
    Write-Host "Pulling image from remote: $ImageName" -ForegroundColor Yellow
    
    # Run docker pull with real-time output using Start-Process
    $process = Start-Process -FilePath "docker" -ArgumentList "pull", $ImageName -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Host "Failed to pull image. Please check your internet connection and try again." -ForegroundColor Red
        Write-Host "   Make sure the image exists: $ImageName" -ForegroundColor Gray
        return $false
    }
    
    Write-Host "Image pulled successfully" -ForegroundColor Green
    return $true
}

# Stop existing container
function Stop-ExistingContainer {
    param($ContainerName)
    
    Write-Host "Checking for existing container..." -ForegroundColor Yellow
    
    $existingContainer = docker ps -q --filter "name=$ContainerName" 2>$null
    if ($existingContainer) {
        Write-Host "Stopping existing container..." -ForegroundColor Yellow
        docker stop $ContainerName
        docker rm $ContainerName
    }
}

# Find available port
function Find-AvailablePort {
    param([int]$StartingPort)
    
    $port = $StartingPort
    
    while ($true) {
        # Check if port is available using Get-NetTCPConnection
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if (-not $connection) {
            return $port
        }
        $port++
    }
}

# ==========================================
# DISPLAY FUNCTIONS
# ==========================================

# Show build configuration
function Show-BuildConfig {
    param(
        $DockerUsername,
        $RepositoryName,
        $ImageTag,
        $Platforms
    )
    
    Write-Host "Build Configuration:" -ForegroundColor Cyan
    Write-Host "   Docker Hub User: $DockerUsername" -ForegroundColor Gray
    Write-Host "   Repository: $RepositoryName" -ForegroundColor Gray
    Write-Host "   Tag: $ImageTag" -ForegroundColor Gray
    Write-Host "   Platforms: $Platforms" -ForegroundColor Gray
    Write-Host ""
}

# Show container information
function Show-ContainerInfo {
    param(
        $ContainerName,
        $ImageName,
        $FrontendPort
    )
    
    Write-Host "Container Information:" -ForegroundColor Cyan
    Write-Host "   Name: $ContainerName" -ForegroundColor Gray
    Write-Host "   Image: $ImageName" -ForegroundColor Gray
    Write-Host "   Frontend: http://localhost:$FrontendPort" -ForegroundColor Gray
    Write-Host ""
}

# Show useful commands
function Show-UsefulCommands {
    param($ContainerName)
    
    Write-Host "Useful Commands:" -ForegroundColor Cyan
    Write-Host "   View logs: docker logs -f $ContainerName" -ForegroundColor Gray
    Write-Host "   Stop: docker stop $ContainerName" -ForegroundColor Gray
    Write-Host "   Remove: docker rm $ContainerName" -ForegroundColor Gray
    Write-Host "   Shell access: docker exec -it $ContainerName /bin/bash" -ForegroundColor Gray
    Write-Host ""
}
