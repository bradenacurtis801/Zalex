# Docker Utilities (PowerShell)
# Shared functions for Docker scripts

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================

# Generic function to ensure an environment variable is set
# Usage: Ensure-EnvVar -VarName "VARIABLE_NAME" -FriendlyName "Friendly Name" -ExampleValue "example"
function Ensure-EnvVar {
    param(
        [Parameter(Mandatory=$true)]
        [string]$VarName,
        [string]$FriendlyName = $VarName,
        [string]$ExampleValue = "your-value"
    )
    
    # Get the environment variable value dynamically
    $varValue = (Get-Item -Path "env:$VarName" -ErrorAction SilentlyContinue).Value
    
    if (-not $varValue) {
        Write-Host "❌ ERROR: $FriendlyName environment variable is required but not set" -ForegroundColor Red
        Write-Host "   Please set it with: `$env:$VarName = '$ExampleValue'" -ForegroundColor Yellow
        exit 1
    }
    
    # Set script-level variable for use in calling script
    # Use Invoke-Expression to set variable with script scope
    Invoke-Expression "`$script:$VarName = `$varValue"
}

# Specific wrapper functions for Docker configuration
function Ensure-DockerUsername {
    Ensure-EnvVar -VarName "DOCKER_USERNAME" -FriendlyName "DOCKER_USERNAME" -ExampleValue "your-dockerhub-username"
}

function Ensure-DockerRepoName {
    Ensure-EnvVar -VarName "REPOSITORY_NAME" -FriendlyName "REPOSITORY_NAME" -ExampleValue "your-repository-name"
}

function Ensure-DockerVolumeOrPath {
    Ensure-EnvVar -VarName "VOLUME_NAME_OR_PATH" -FriendlyName "VOLUME_NAME_OR_PATH" -ExampleValue "your_volume_name_or_path"
}

# Check and set Docker Hub configuration from environment variables
# Exits with error if required variables are not set
# This is a convenience function that checks both username and repo name
function Ensure-DockerHubConfig {
    Ensure-DockerUsername
    Ensure-DockerRepoName
}

# Get script directory and root directory
function Get-ScriptDirs {
    # Get the directory of the utils script
    $script:SCRIPT_DIR = Split-Path -Parent $PSScriptRoot
    $script:ROOT_DIR = (Resolve-Path (Join-Path $SCRIPT_DIR "..\..")).Path
    $script:ENV_FILE_PATH = Join-Path $ROOT_DIR ".env"
}

# Load environment variables from a file
# Usage: Import-Env -EnvFile /path/to/.env
# Exports all variables from the file into the current PowerShell environment
function Import-Env {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EnvFile
    )
    
    # Check if file exists
    if (-not (Test-Path $EnvFile)) {
        Write-Host "⚠️  Warning: Environment file not found: $EnvFile" -ForegroundColor Yellow
        return $false
    }
    
    # Read file line by line
    $lines = Get-Content $EnvFile
    
    foreach ($line in $lines) {
        # Trim whitespace
        $line = $line.Trim()
        
        # Skip empty lines and comments
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            continue
        }
        
        # Parse KEY=VALUE format
        if ($line -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Remove quotes if present (handles both single and double quotes)
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or 
                ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            
            # Set environment variable
            [Environment]::SetEnvironmentVariable($key, $value, [EnvironmentVariableTarget]::Process)
            Set-Item -Path "env:$key" -Value $value
        }
    }
    
    return $true
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

# Try to resolve a file path at the project root
# Usage: Try-ResolveFile -FileName <filename> [-FilePath <optional_full_path>]
# Returns the path to the file, determining it if not provided
function Try-ResolveFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FileName,
        [string]$FilePath = $null
    )
    
    # If full path is already provided, return it
    if ($FilePath) {
        return $FilePath
    }
    
    # First, try to use ROOT_DIR if it's already set
    if ($ROOT_DIR) {
        return Join-Path $ROOT_DIR $FileName
    }
    
    # Try to calculate root directory similar to Get-ScriptDirs
    $scriptFile = $PSScriptRoot
    if ($scriptFile) {
        $calculatedRoot = (Resolve-Path (Join-Path $scriptFile "..\..\..")).Path
        
        # Verify it's the right directory by checking for Dockerfile
        if (Test-Path (Join-Path $calculatedRoot "Dockerfile")) {
            return Join-Path $calculatedRoot $FileName
        }
    }
    
    # Fallback: search from current directory
    $currentDir = Get-Location
    $searchDir = $currentDir.Path
    
    # Walk up the directory tree looking for Dockerfile
    while ($searchDir -and $searchDir -ne (Split-Path $searchDir)) {
        if (Test-Path (Join-Path $searchDir "Dockerfile")) {
            return Join-Path $searchDir $FileName
        }
        $searchDir = Split-Path $searchDir
    }
    
    # If still not found, use current directory
    return Join-Path $currentDir.Path $FileName
}

# Create .env file with template
function Create-EnvFile {
    param(
        [string]$EnvFilePath = $null
    )
    
    # Get the .env file path
    $EnvFilePath = Try-ResolveFile -FileName ".env" -FilePath $EnvFilePath
    
    # Check if .env already exists
    if (Test-Path $EnvFilePath) {
        Write-Host ".env file already exists at $EnvFilePath" -ForegroundColor Yellow
        return
    }
    
    # Get the .env.example file path
    $envExamplePath = Try-ResolveFile -FileName ".env.example"
    
    # Check if .env.example exists
    if (-not (Test-Path $envExamplePath)) {
        Write-Host "❌ Error: .env.example file not found at $envExamplePath" -ForegroundColor Red
        Write-Host "   Please create a .env.example file at the project root." -ForegroundColor Yellow
        return
    }
    
    # Copy .env.example to .env
    Copy-Item -Path $envExamplePath -Destination $EnvFilePath
    
    Write-Host "Created .env file at $EnvFilePath from $envExamplePath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Open the .env file: $EnvFilePath" -ForegroundColor Gray
    Write-Host "   2. Update the environment variables as needed" -ForegroundColor Gray
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
