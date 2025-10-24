# ScanPro Run Script (PowerShell)
# Runs the ScanPro containers

# Load utilities
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$SCRIPT_DIR\utils\utils.ps1"

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================

$DOCKER_USERNAME = "bradenacurtis801"
$REPOSITORY_NAME = "scanpro"

# Get directories and git tag
Get-ScriptDirs
$IMAGE_TAG = Get-GitTag
$IMAGE_NAME = "$DOCKER_USERNAME/$REPOSITORY_NAME`:$IMAGE_TAG"
$CONTAINER_NAME = "scanpro"
$FRONTEND_PORT = 3000

# ==========================================
# FUNCTIONS
# ==========================================


function Start-Container {
    Write-Host "Starting ScanPro container..." -ForegroundColor Yellow
    
    # Find available port
    $originalPort = $FRONTEND_PORT
    $actualPort = Find-AvailablePort -StartingPort $FRONTEND_PORT
    
    # Check if we need to use a different port
    if ($actualPort -ne $originalPort) {
        Write-Host "Port $originalPort is already in use" -ForegroundColor Yellow
        Write-Host "Found available port: $actualPort" -ForegroundColor Cyan
        
        $userChoice = Read-Host "Would you like to use port $actualPort instead? (y/n)"
        if ($userChoice -eq "y" -or $userChoice -eq "Y") {
            $script:FRONTEND_PORT = $actualPort
            Write-Host "Using port $actualPort" -ForegroundColor Green
        }
        else {
            Write-Host "Port $originalPort is not available. Please free the port and try again." -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "   Container name: $CONTAINER_NAME" -ForegroundColor Gray
    Write-Host "   Frontend port: $FRONTEND_PORT" -ForegroundColor Gray
    Write-Host "   Image: $IMAGE_NAME" -ForegroundColor Gray
    Write-Host ""
    
    # Run docker run with real-time output using Start-Process
    $dockerArgs = @("run", "-it", "--rm", "--name", $CONTAINER_NAME, "-p", "${FRONTEND_PORT}:3000", "-v", "scanpro_data:/app/APP_DATA", "--env-file", $ENV_FILE_PATH, "-e", "DEBUG=0", $IMAGE_NAME)
    $process = Start-Process -FilePath "docker" -ArgumentList $dockerArgs -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Host "Failed to start container!" -ForegroundColor Red
        Write-Host "   Check if port $FRONTEND_PORT is already in use" -ForegroundColor Gray
        Write-Host "   Try: netstat -an | findstr :$FRONTEND_PORT" -ForegroundColor Gray
        Write-Host "   Check container logs: docker logs $CONTAINER_NAME" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "Container started successfully" -ForegroundColor Green
}

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================

Write-Host "ScanPro Run Script" -ForegroundColor Magenta
Write-Host "====================" -ForegroundColor Magenta
Write-Host ""

# Check prerequisites
if (-not (Test-Docker)) {
    exit 1
}

# Stop existing container
Stop-ExistingContainer -ContainerName $CONTAINER_NAME

# Run container
Start-Container