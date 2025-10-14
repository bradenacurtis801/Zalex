@echo off
setlocal enabledelayedexpansion

REM ScanPro Docker Hub Build and Push Script (Windows)
REM Builds multi-architecture image and pushes to Docker Hub

REM ==========================================
REM CONFIGURATION VARIABLES
REM ==========================================

set "DOCKER_USERNAME=bradenacurtis801"
set "REPOSITORY_NAME=scanpro"

REM Get current git branch as tag
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "IMAGE_TAG=%%i"
if "%IMAGE_TAG%"=="" set "IMAGE_TAG=latest"
if "%IMAGE_TAG%"=="main" set "IMAGE_TAG=latest"
if "%IMAGE_TAG%"=="master" set "IMAGE_TAG=latest"

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

:construct_image_urls
set "FULL_IMAGE_NAME=%DOCKER_USERNAME%/%REPOSITORY_NAME%:%IMAGE_TAG%"

echo 📋 Image that will be created:
echo    Tag: %FULL_IMAGE_NAME%
echo    Branch: %IMAGE_TAG%
echo.
goto :construct_image_urls_end
:construct_image_urls_end

:build_image
echo 🏗️  Building image...
echo    Repository: %DOCKER_USERNAME%/%REPOSITORY_NAME%
echo    Tag: %IMAGE_TAG%
echo    Branch: %IMAGE_TAG%
echo.

echo 🔨 Building image...
docker build -t %FULL_IMAGE_NAME% .
if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)
echo ✅ Image built successfully
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
echo    # Pull and run the image
echo    docker pull %FULL_IMAGE_NAME%
echo    docker run -p 3000:3000 -p 5000:5000 %FULL_IMAGE_NAME%
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

call :check_git
if errorlevel 1 exit /b 1

REM Show configuration
echo 📋 Build Configuration:
echo    Docker Hub User: %DOCKER_USERNAME%
echo    Repository: %REPOSITORY_NAME%
echo    Tag: %IMAGE_TAG%
echo    Branch: %IMAGE_TAG%
echo.

REM Construct and show image URLs
call :construct_image_urls

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

REM Build the image
echo 🚀 Starting build process...
call :build_image
if errorlevel 1 exit /b 1

echo ✅ Build completed successfully!
echo.

REM Ask for confirmation before pushing
echo 🔨 Ready to push the image to Docker Hub.
call :ask_confirmation
if errorlevel 1 exit /b 1

REM Push the image
echo 🚀 Pushing image to Docker Hub...
docker push %FULL_IMAGE_NAME%
if errorlevel 1 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo ✅ Push completed successfully!
echo.

REM Show usage instructions
call :show_usage

echo 🎉 Done! Your ScanPro image is now available on Docker Hub.
echo.
pause

:end
