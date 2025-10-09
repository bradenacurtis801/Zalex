@echo off
setlocal enabledelayedexpansion

REM ScanPro Docker Hub Build and Push Script (Windows)
REM Builds multi-architecture image and pushes to Docker Hub

REM ==========================================
REM CONFIGURATION VARIABLES
REM ==========================================

set "DOCKER_USERNAME=bradenacurtis801"
set "REPOSITORY_NAME=scanpro"
set "IMAGE_TAG=latest"
set "PLATFORMS=linux/amd64,linux/arm64"
set "BUILDER_NAME=scanpro-hub-builder"

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

:check_buildx
echo Checking Docker Buildx...
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Buildx is not available. Please install Docker Desktop or enable buildx.
    pause
    exit /b 1
)
echo ✅ Docker Buildx is available
goto :check_buildx_end
:check_buildx_end

:setup_builder
echo Setting up buildx builder...
docker buildx inspect %BUILDER_NAME% >nul 2>&1
if errorlevel 1 (
    echo 🔧 Creating new buildx builder: %BUILDER_NAME%
    docker buildx create --name %BUILDER_NAME% --use
) else (
    echo 🔧 Using existing buildx builder: %BUILDER_NAME%
    docker buildx use %BUILDER_NAME%
)
goto :setup_builder_end
:setup_builder_end

:construct_image_urls
set "FULL_IMAGE_NAME=%DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%"
set "AMD64_TAG=%DOCKER_USERNAME%/%REPOSITORY_NAME%:amd64"
set "ARM64_TAG=%DOCKER_USERNAME%/%REPOSITORY_NAME%:arm64"

echo 📋 Image URLs that will be created:
echo    Main: %FULL_IMAGE_NAME%
echo    AMD64: %AMD64_TAG%
echo    ARM64: %ARM64_TAG%
echo.
goto :construct_image_urls_end
:construct_image_urls_end

:build_image
echo 🏗️  Building multi-architecture image...
echo    Platforms: %PLATFORMS%
echo    Repository: %DOCKER_USERNAME%/%REPOSITORY_NAME%
echo    Tag: %IMAGE_TAG%
echo.

REM First build locally for current platform
echo 🔨 Building local image...
docker build -t %FULL_IMAGE_NAME% .
if errorlevel 1 (
    echo ❌ Local build failed!
    pause
    exit /b 1
)
echo ✅ Local image built successfully

REM Then build and push multi-architecture
echo 🚀 Building and pushing multi-architecture image...
docker buildx build ^
    --platform %PLATFORMS% ^
    --tag %FULL_IMAGE_NAME% ^
    --tag %AMD64_TAG% ^
    --tag %ARM64_TAG% ^
    --push ^
    .

if errorlevel 1 (
    echo ❌ Multi-arch build/push failed!
    pause
    exit /b 1
)
goto :build_image_end
:build_image_end

:ask_confirmation
echo 🤔 Do you want to push the built image to Docker Hub? (y/n)
set /p response=
if /i "%response%"=="y" goto :yes
if /i "%response%"=="yes" goto :yes
if /i "%response%"=="n" goto :no
if /i "%response%"=="no" goto :no
echo ❌ Invalid response. Please answer y or n.
goto :ask_confirmation

:yes
goto :ask_confirmation_end

:no
echo ❌ Push cancelled by user.
pause
exit /b 0

:ask_confirmation_end

:show_usage
echo 📖 After pushing, you can pull and run the image with:
echo.
echo    # Pull and run the latest version
echo    docker pull %FULL_IMAGE_NAME%
echo    docker run -p 3000:3000 -p 5000:5000 %FULL_IMAGE_NAME%
echo.
echo    # Or pull specific architecture
echo    docker pull %AMD64_TAG%    # Intel
echo    docker pull %ARM64_TAG%    # Apple M1
echo.
echo    # Or use docker-compose with the image
echo    # Update docker-compose.yml to use: image: %FULL_IMAGE_NAME%
goto :show_usage_end
:show_usage_end

REM ==========================================
REM MAIN SCRIPT EXECUTION
REM ==========================================

REM Parse command line arguments
set "LOCAL_ONLY="
set "NO_PUSH="

:parse_args
if "%~1"=="" goto :main
if "%~1"=="--local-only" set "LOCAL_ONLY=1" & shift & goto :parse_args
if "%~1"=="--no-push" set "NO_PUSH=1" & shift & goto :parse_args
shift
goto :parse_args

:main
echo 🐳 ScanPro Docker Build Script
echo ================================
echo.

REM Check prerequisites
call :check_docker
if errorlevel 1 exit /b 1

if not defined LOCAL_ONLY (
    call :check_buildx
    if errorlevel 1 exit /b 1
)

REM Show configuration
echo 📋 Build Configuration:
echo    Docker Hub User: %DOCKER_USERNAME%
echo    Repository: %REPOSITORY_NAME%
echo    Tag: %IMAGE_TAG%
echo    Platforms: %PLATFORMS%
echo.

REM Construct and show image URLs
call :construct_image_urls

REM Setup buildx builder
call :setup_builder
if errorlevel 1 exit /b 1

REM Handle local-only build
if defined LOCAL_ONLY (
    echo 🔨 Building local image only...
    echo    Using base image: bradenacurtis801/scanpro-base:latest
    echo    If base image doesn't exist, run: .\build-base.bat
    echo.
    docker build -t %FULL_IMAGE_NAME% .
    if errorlevel 1 (
        echo ❌ Local build failed!
        echo    Make sure base image exists: bradenacurtis801/scanpro-base:latest
        echo    Run: .\build-base.bat
        pause
        exit /b 1
    )
    echo ✅ Local image built successfully!
    echo    Image: %FULL_IMAGE_NAME%
    echo    You can now run: .\run.bat --no-pull
    goto :end
)

REM Ask for confirmation before building
echo 🔨 Ready to build and push the image.
call :ask_confirmation
if errorlevel 1 exit /b 1

REM Build and push the image
echo 🚀 Starting build and push process...
call :build_image
if errorlevel 1 exit /b 1

echo ✅ Build and push completed successfully!
echo.

REM Show usage instructions
call :show_usage

echo 🎉 Done! Your ScanPro image is now available on Docker Hub.
echo.
pause

:end
