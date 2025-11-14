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

# Check if .env file exists
if (-not (Test-Path $ENV_FILE_PATH)) {
    Write-Host "Error: .env file not found at $ENV_FILE_PATH" -ForegroundColor Red
    Write-Host "   The .env file is required for the container to run properly." -ForegroundColor Gray
    Write-Host ""
    Write-Host "   To create a .env file with a template, run:" -ForegroundColor Gray
    Write-Host "   . scripts/docker/utils/utils.ps1; Create-EnvFile" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Or manually create it at: $ENV_FILE_PATH" -ForegroundColor Gray
    exit 1
}

# ==========================================
# FUNCTIONS
# ==========================================


function Start-Container {
    Write-Host "Starting ScanPro container..." -ForegroundColor Yellow
    Write-Host "   Container name: $CONTAINER_NAME" -ForegroundColor Gray
    Write-Host "   Image: $IMAGE_NAME" -ForegroundColor Gray
    Write-Host ""
    
    # Check if the desired port is available
    $portStatus = Test-PortOpen -Port $FRONTEND_PORT
    if ($portStatus -eq 0) {
        # Port is available, use it
        $openFrontendPort = $FRONTEND_PORT
        Write-Host "Port $FRONTEND_PORT is available" -ForegroundColor Green
    }
    else {
        # Port is in use
        Write-Host "Port $FRONTEND_PORT is already in use" -ForegroundColor Yellow
        Write-Host ""
        
        # Find an open port
        Write-Host "Finding available port starting from $FRONTEND_PORT..." -ForegroundColor Cyan
        $openFrontendPort = Find-OpenPort -StartPort $FRONTEND_PORT
        
        if (-not $openFrontendPort) {
            Write-Host "Failed to find an available port starting from $FRONTEND_PORT" -ForegroundColor Red
            exit 1
        }
        
        # Ask for confirmation
        Write-Host "   Found available port: $openFrontendPort" -ForegroundColor Cyan
        Write-Host ""
        $userChoice = Read-Host "   Do you want to run on port $openFrontendPort instead? (y/n)"
        
        if ($userChoice -ne "y" -and $userChoice -ne "Y") {
            Write-Host "Aborted. Please free up port $FRONTEND_PORT or choose a different port." -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "   Using port: $openFrontendPort" -ForegroundColor Gray
    Write-Host ""
    
    # Run docker run with real-time output using Start-Process
    $dockerArgs = @("run", "-it", "--rm", "--name", $CONTAINER_NAME, "-p", "${openFrontendPort}:3000", "-v", "scanpro_data:/app/APP_DATA", "--env-file", $ENV_FILE_PATH, "-e", "DEBUG=0", $IMAGE_NAME)
    $process = Start-Process -FilePath "docker" -ArgumentList $dockerArgs -Wait -NoNewWindow -PassThru
    
    $exitCode = $process.ExitCode
    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "Failed to start container (exit code: $exitCode)" -ForegroundColor Red
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

# Check if image exists and pull if needed
$pullSuccess = Invoke-PullImageIfNeeded -ImageName $IMAGE_NAME
if (-not $pullSuccess) {
    Write-Host "Failed to pull required image. Exiting." -ForegroundColor Red
    Write-Host "   You can build the image locally by running: scripts/docker/build-local.ps1" -ForegroundColor Gray
    exit 1
}

# Run container
Start-Container