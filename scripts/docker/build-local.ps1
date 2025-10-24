# ScanPro Local Docker Build Script (PowerShell)
# Builds image for local development and testing

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
$DOCKER_FILE_PATH = Join-Path $ROOT_DIR "Dockerfile"
$IMAGE_TAG = Get-GitTag
$FULL_IMAGE_NAME = "$DOCKER_USERNAME/$REPOSITORY_NAME`:$IMAGE_TAG"

# ==========================================
# SCRIPT FUNCTIONS
# ==========================================

function Show-BuildInfo {
    Write-Host "Local build configuration:" -ForegroundColor Cyan
    Write-Host "   Tag: $FULL_IMAGE_NAME" -ForegroundColor Gray
    Write-Host "   Platform: $env:PROCESSOR_ARCHITECTURE" -ForegroundColor Gray
    Write-Host ""
}

function Invoke-BuildImage {
    param($FullImageName)
    
    Write-Host "Building image for local development..." -ForegroundColor Yellow
    Write-Host "   Platform: $env:PROCESSOR_ARCHITECTURE" -ForegroundColor Gray
    Write-Host "   Tag: $FullImageName" -ForegroundColor Gray
    Write-Host "   Also tagged as: $DOCKER_USERNAME/$REPOSITORY_NAME`:latest" -ForegroundColor Gray
    Write-Host ""
    
    # Run docker build with real-time output using Start-Process
    $process = Start-Process -FilePath "docker" -ArgumentList "build", "-t", $FullImageName, "-t", "$DOCKER_USERNAME/$REPOSITORY_NAME`:latest", "-f", $DOCKER_FILE_PATH, $ROOT_DIR -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Host "Build failed!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Local image built successfully" -ForegroundColor Green
    return $true
}

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================

Write-Host "ScanPro Local Docker Build Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
if (-not (Test-Docker)) {
    exit 1
}

# Show build information
Show-BuildInfo

# Build the image
Write-Host "Starting local build process..." -ForegroundColor Yellow
if (-not (Invoke-BuildImage -FullImageName $FULL_IMAGE_NAME)) {
    exit 1
}

Write-Host "Local build completed successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "Done! Your local ScanPro image is ready." -ForegroundColor Green
Write-Host ""
