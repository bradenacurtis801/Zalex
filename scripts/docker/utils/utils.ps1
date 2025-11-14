# ScanPro Docker Utilities (PowerShell)
# Shared functions for Docker scripts

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================

# Get script directory and root directory
function Get-ScriptDirs {
    # Get the directory of the utils script
    $script:SCRIPT_DIR = Split-Path -Parent $PSScriptRoot
    $script:ROOT_DIR = (Resolve-Path (Join-Path $SCRIPT_DIR "..\..")).Path
    $script:ENV_FILE_PATH = Join-Path $ROOT_DIR ".env"
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

# Create .env file with template
function Create-EnvFile {
    param(
        [string]$EnvFilePath = $null
    )
    
    # If EnvFilePath is not provided, try to determine it
    if (-not $EnvFilePath) {
        # First, try to use ENV_FILE_PATH if it's already set
        if ($ENV_FILE_PATH) {
            $EnvFilePath = $ENV_FILE_PATH
        }
        # Try to use ROOT_DIR if it's already set
        elseif ($ROOT_DIR) {
            $EnvFilePath = Join-Path $ROOT_DIR ".env"
        }
        else {
            # Try to calculate root directory similar to Get-ScriptDirs
            $scriptFile = $PSScriptRoot
            if ($scriptFile) {
                $calculatedRoot = (Resolve-Path (Join-Path $scriptFile "..\..\..")).Path
                
                # Verify it's the right directory by checking for Dockerfile
                if (Test-Path (Join-Path $calculatedRoot "Dockerfile")) {
                    $EnvFilePath = Join-Path $calculatedRoot ".env"
                }
            }
            
            # Fallback: search from current directory
            if (-not $EnvFilePath) {
                $currentDir = Get-Location
                $searchDir = $currentDir.Path
                
                # Walk up the directory tree looking for Dockerfile
                while ($searchDir -and $searchDir -ne (Split-Path $searchDir)) {
                    if (Test-Path (Join-Path $searchDir "Dockerfile")) {
                        $EnvFilePath = Join-Path $searchDir ".env"
                        break
                    }
                    $searchDir = Split-Path $searchDir
                }
                
                # If still not found, use current directory
                if (-not $EnvFilePath) {
                    $EnvFilePath = Join-Path $currentDir.Path ".env"
                }
            }
        }
    }
    
    # Check if .env already exists
    if (Test-Path $EnvFilePath) {
        Write-Host ".env file already exists at $EnvFilePath" -ForegroundColor Yellow
        return
    }
    
    # Create .env file with template
    $envContent = @"
# ScanPro Environment Configuration
# ==========================================
# This file contains environment variables required for ScanPro to run.
# DO NOT commit this file to version control (it's in .gitignore)

# Hugging Face Token
# ==========================================
# Required for downloading and accessing ML models from Hugging Face.
# Get your token from: https://huggingface.co/settings/tokens
# Format: hf_xxxxxxxxxxxxxxxxxxxx
SCANPRO_HF_TOKEN=

# Below contains config that is optional and is not required for the container to run.
# Database Configuration (if needed)
# ==========================================
# DATABASE_URL=postgresql://user:password@localhost:5432/scanpro

# Other Configuration (add as needed)
# ==========================================
# DEBUG=0
"@
    
    $envContent | Out-File -FilePath $EnvFilePath -Encoding utf8 -NoNewline
    
    Write-Host "Created .env file at $EnvFilePath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Open the .env file: $EnvFilePath" -ForegroundColor Gray
    Write-Host "   2. Add your Hugging Face token: SCANPRO_HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx" -ForegroundColor Gray
    Write-Host "   3. Get your token from: https://huggingface.co/settings/tokens" -ForegroundColor Gray
    Write-Host ""
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
    
    $runningContainer = docker ps -q --filter "name=$ContainerName" 2>$null
    if ($runningContainer) {
        Write-Host "Stopping running container..." -ForegroundColor Yellow
        docker stop $ContainerName
        docker rm $ContainerName
    }
    else {
        $stoppedContainer = docker ps -aq --filter "name=$ContainerName" 2>$null
        if ($stoppedContainer) {
            Write-Host "Removing stopped container..." -ForegroundColor Yellow
            docker rm $ContainerName
        }
        else {
            Write-Host "No existing container found" -ForegroundColor Gray
        }
    }
}

# Check if a port is open/available
function Test-PortOpen {
    param([int]$Port)
    
    if (-not $Port) {
        Write-Error "Error: No port provided to Test-PortOpen()"
        return 2
    }
    
    # Check if port is a valid number
    if ($Port -lt 1 -or $Port -gt 65535) {
        Write-Error "Error: Port must be between 1 and 65535"
        return 2
    }
    
    # Check if port is available using Get-NetTCPConnection
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connection) {
            return 1  # Port is in use
        } else {
            return 0  # Port is open
        }
    }
    catch {
        # If Get-NetTCPConnection fails, try alternative method
        try {
            $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
            $connections = $listener.GetActiveTcpListeners() | Where-Object { $_.Port -eq $Port }
            if ($connections) {
                return 1  # Port is in use
            } else {
                return 0  # Port is open
            }
        }
        catch {
            Write-Warning "Cannot check port availability, assuming port is open"
            return 0  # Assume port is open if we can't check
        }
    }
}

# Find an open port starting from the given port, incrementing until one is found
function Find-OpenPort {
    param(
        [int]$StartPort,
        [int]$MaxAttempts = 100
    )
    
    if (-not $StartPort) {
        Write-Error "Error: No starting port provided to Find-OpenPort()"
        return $null
    }
    
    # Validate starting port
    if ($StartPort -lt 1 -or $StartPort -gt 65535) {
        Write-Error "Error: Invalid starting port: $StartPort"
        return $null
    }
    
    $currentPort = $StartPort
    $attempts = 0
    
    while ($attempts -lt $MaxAttempts) {
        $portStatus = Test-PortOpen -Port $currentPort
        if ($portStatus -eq 0) {
            return $currentPort
        }
        
        # Increment port
        $currentPort++
        $attempts++
        
        # Don't exceed max port number
        if ($currentPort -gt 65535) {
            Write-Error "Error: Reached maximum port number (65535) without finding an open port"
            return $null
        }
    }
    
    Write-Error "Error: Could not find an open port after $MaxAttempts attempts starting from $StartPort"
    return $null
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
