@echo off
setlocal enabledelayedexpansion

REM ScanPro Docker Hub Build and Push Script (Windows)
REM Builds image and pushes to Docker Hub

REM ==========================================
REM CONFIGURATION VARIABLES
REM ==========================================

set "DOCKER_USERNAME=bradenacurtis801"
set "REPOSITORY_NAME=scanpro"

REM Get script directory
set SCRIPT_DIR=%~dp0
set "DOCKER_FILE_PATH=%SCRIPT_DIR%..\..\Dockerfile"

REM Get current git branch as tag
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "IMAGE_TAG=%%i"
if "%IMAGE_TAG%"=="" set "IMAGE_TAG=latest"
if "%IMAGE_TAG%"=="main" set "IMAGE_TAG=latest"
if "%IMAGE_TAG%"=="master" set "IMAGE_TAG=latest"

REM Build Configuration
set "BUILDER_NAME=scanpro-multiarch-builder"
set "PLATFORMS=linux/amd64,linux/arm64"

REM ==========================================
REM SCRIPT FUNCTIONS
REM ==========================================

:check_docker
echo Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)
echo ✅ Docker is running
goto :check_docker_end
:check_docker_end

:check_git
echo Checking Git repository...
git status >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Not in a git repository, using 'latest' as tag
    set "IMAGE_TAG=latest"
) else (
    echo ✅ Git repository detected, using branch: %IMAGE_TAG%
)
goto :check_git_end
:check_git_end

:setup_buildx
echo Setting up Docker Buildx...

REM Check if buildx is available
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Buildx is not available. Please update Docker to a newer version.
    pause
    exit /b 1
)

REM Create or use existing builder
docker buildx inspect %BUILDER_NAME% >nul 2>&1
if errorlevel 1 (
    echo Creating new buildx builder: %BUILDER_NAME%
    docker buildx create --name %BUILDER_NAME% --use
) else (
    echo Using existing buildx builder: %BUILDER_NAME%
    docker buildx use %BUILDER_NAME%
)

REM Bootstrap the builder
echo Bootstrapping builder...
docker buildx inspect --bootstrap
goto :setup_buildx_end
:setup_buildx_end

:construct_image_urls
set "FULL_IMAGE_NAME=%DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%"

echo 📋 Multi-architecture image that will be created:
echo    Tag: %FULL_IMAGE_NAME%
echo    Branch: %IMAGE_TAG%
echo    Platforms: %PLATFORMS%
echo.
goto :construct_image_urls_end
:construct_image_urls_end

:build_and_push_image
    echo 🏗️  Building and pushing multi-architecture image...
    echo    Repository: %DOCKER_USERNAME%/%REPOSITORY_NAME%
    echo    Tag: %IMAGE_TAG%
    echo    Branch: %IMAGE_TAG%
    echo    Platforms: %PLATFORMS%
    echo.
    
    docker buildx build --platform %PLATFORMS% --tag %FULL_IMAGE_NAME% --push -f "%DOCKER_FILE_PATH%" .

if errorlevel 1 (
    echo ❌ Build and push failed!
    pause
    exit /b 1
)
echo ✅ Multi-architecture image built and pushed successfully
goto :build_and_push_image_end
:build_and_push_image_end


:show_usage
echo 📖 After pushing, you can pull and run the multi-architecture image with:
echo.
echo    # Pull and run the image (will auto-select correct architecture)
echo    docker pull %FULL_IMAGE_NAME%
echo    docker run -p 3000:3000 -p 5000:5000 %FULL_IMAGE_NAME%
echo.
echo    # Pull for specific platform
echo    docker pull --platform linux/amd64 %FULL_IMAGE_NAME%
echo    docker pull --platform linux/arm64 %FULL_IMAGE_NAME%
echo.
echo    # Or use docker-compose with the image
echo    # Update docker-compose.yml to use: image: %FULL_IMAGE_NAME%
goto :show_usage_end
:show_usage_end

REM ==========================================
REM MAIN SCRIPT EXECUTION
REM ==========================================

echo 🐳 ScanPro Multi-Architecture Docker Build and Push Script
echo ==========================================================
echo.
echo 🔧 Auto-push mode: Will build and push to Docker Hub automatically
echo.

REM Check prerequisites
call :check_docker
if errorlevel 1 exit /b 1

call :check_git
if errorlevel 1 exit /b 1

REM Setup buildx
call :setup_buildx
if errorlevel 1 exit /b 1

REM Show configuration
echo 📋 Build Configuration:
echo    Docker Hub User: %DOCKER_USERNAME%
echo    Repository: %REPOSITORY_NAME%
echo    Tag: %IMAGE_TAG%
echo    Branch: %IMAGE_TAG%
echo    Builder: %BUILDER_NAME%
echo    Platforms: %PLATFORMS%
echo.

REM Construct and show image URLs
call :construct_image_urls

REM Build and push the image
echo 🚀 Starting multi-architecture build and push process...
call :build_and_push_image
if errorlevel 1 exit /b 1

echo ✅ Multi-architecture build and push completed successfully!
echo.

REM Show usage instructions
call :show_usage

echo 🎉 Done! Your ScanPro multi-architecture image is now available on Docker Hub.
echo.
pause
