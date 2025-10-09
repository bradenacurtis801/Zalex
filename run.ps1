# ScanPro Run Script (PowerShell)
# Runs the ScanPro containers

param(
    [switch]$NoPull,
    [switch]$Stop,
    [switch]$Help
)

# Configuration variables
$ImageName = "bradenacurtis801/scanpro:latest"
$ContainerName = "scanpro"
$FrontendPort = 3000
$BackendPort = 5000

# Functions
function Show-Help {
    Write-Host "Usage: .\run.ps1 [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "    -Help, -h     Show this help message"
    Write-Host "    -NoPull       Skip pulling image (use local only)"
    Write-Host "    -Stop         Stop and remove existing container"
    Write-Host ""
}

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
        Read-Host "Press Enter to continue"
        return $false
    }
}

function Stop-ExistingContainer {
    Write-Host "Checking for existing container..." -ForegroundColor Yellow
    $existingContainer = docker ps -q --filter "name=$ContainerName" 2>$null
    if ($existingContainer) {
        Write-Host "Stopping existing container..." -ForegroundColor Yellow
        docker stop $ContainerName | Out-Null
        docker rm $ContainerName | Out-Null
        Write-Host "Existing container stopped and removed" -ForegroundColor Green
    }
}

function Test-ImageExists {
    Write-Host "Checking for image..." -ForegroundColor Yellow
    Write-Host "   Image: $ImageName" -ForegroundColor Gray
    
    $localImage = docker images $ImageName --format "{{.Repository}}:{{.Tag}}" 2>$null
    if ($localImage -eq $ImageName) {
        Write-Host "Image found locally, skipping pull" -ForegroundColor Green
        return $true
    }
    
    Write-Host "Pulling latest image..." -ForegroundColor Yellow
    docker pull $ImageName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to pull image. Please check your internet connection and try again." -ForegroundColor Red
        Write-Host "   Make sure the image exists: $ImageName" -ForegroundColor Red
        Write-Host "   You can try running with -NoPull to use a local image" -ForegroundColor Red
        Read-Host "Press Enter to continue"
        return $false
    }
    Write-Host "Image pulled successfully" -ForegroundColor Green
    return $true
}

function Start-Container {
    Write-Host "Starting ScanPro container..." -ForegroundColor Yellow
    Write-Host "   Container name: $ContainerName" -ForegroundColor Gray
    Write-Host "   Frontend port: $FrontendPort" -ForegroundColor Gray
    Write-Host "   Backend port: $BackendPort" -ForegroundColor Gray
    Write-Host "   Image: $ImageName" -ForegroundColor Gray
    Write-Host ""
    
    $runCommand = @(
        "run", "-d",
        "--name", $ContainerName,
        "-p", "${FrontendPort}:${FrontendPort}",
        "-p", "${BackendPort}:${BackendPort}",
        "-v", "scanpro_data:/app/backend/APP_DATA",
        "-e", "NODE_ENV=prod",
        "-e", "DEBUG=false",
        "-e", "NEXT_PUBLIC_API_URL=http://localhost:$BackendPort",
        "--rm",
        $ImageName
    )
    
    docker @runCommand
    
    Write-Host ""
    Write-Host "Docker run command completed with exit code: $LASTEXITCODE" -ForegroundColor Gray
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start container!" -ForegroundColor Red
        Write-Host "   Check if ports $FrontendPort or $BackendPort are already in use" -ForegroundColor Red
        Write-Host "   Try: netstat -an | findstr `":$FrontendPort`"" -ForegroundColor Red
        Write-Host "   Try: netstat -an | findstr `":$BackendPort`"" -ForegroundColor Red
        Write-Host "   Check container logs: docker logs $ContainerName" -ForegroundColor Red
        Read-Host "Press Enter to continue"
        return $false
    }
    Write-Host "Container started successfully" -ForegroundColor Green
    return $true
}

function Show-Status {
    Write-Host ""
    Write-Host "ScanPro is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Container Information:" -ForegroundColor Cyan
    Write-Host "   Name: $ContainerName" -ForegroundColor Gray
    Write-Host "   Image: $ImageName" -ForegroundColor Gray
    Write-Host "   Frontend: http://localhost:$FrontendPort" -ForegroundColor Gray
    Write-Host "   Backend: http://localhost:$BackendPort" -ForegroundColor Gray
    Write-Host "   API Docs: http://localhost:$BackendPort/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor Cyan
    docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Cyan
    Write-Host "   View logs: docker logs -f $ContainerName" -ForegroundColor Gray
    Write-Host "   Stop: docker stop $ContainerName" -ForegroundColor Gray
    Write-Host "   Remove: docker rm $ContainerName" -ForegroundColor Gray
    Write-Host "   Shell access: docker exec -it $ContainerName /bin/bash" -ForegroundColor Gray
    Write-Host ""
}

# Main script execution
Write-Host "ScanPro Run Script" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

# Handle help
if ($Help) {
    Show-Help
    exit 0
}

# Check prerequisites
if (-not (Test-Docker)) {
    exit 1
}

# Stop existing container
Stop-ExistingContainer

# Handle stop-only option
if ($Stop) {
    Write-Host "Container stopped and removed." -ForegroundColor Green
    Read-Host "Press Enter to continue"
    exit 0
}

# Pull image (unless NoPull is specified)
if (-not $NoPull) {
    if (-not (Test-ImageExists)) {
        exit 1
    }
}

# Run container
if (-not (Start-Container)) {
    exit 1
}

# Show status
Show-Status

Write-Host "ScanPro is ready to use!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to continue"