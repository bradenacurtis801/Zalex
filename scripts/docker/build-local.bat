@echo off
setlocal enabledelayedexpansion

REM ScanPro Local Docker Build Script (Windows)
REM Builds image for local development and testing

REM ==========================================
REM CONFIGURATION VARIABLES
REM ==========================================

REM Build Configuration
set "IMAGE_TAG=local"

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

:show_build_info
echo 📋 Local build configuration:
echo    Tag: scanpro:local
echo    Platform: %PROCESSOR_ARCHITECTURE%
echo.
goto :show_build_info_end
:show_build_info_end

:build_image
echo 🏗️  Building image for local development...
echo    Platform: %PROCESSOR_ARCHITECTURE%
echo    Tag: scanpro:local
echo.

docker build -t scanpro:local -f ../../Dockerfile ../../

if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)
echo ✅ Local image built successfully
goto :build_image_end
:build_image_end

:show_usage
echo 📖 You can now run the image locally with:
echo.
echo    # Run the local image
echo    docker run -p 3000:3000 -p 5000:5000 scanpro:local
echo.
echo    # Or use docker-compose with the local image
echo    # Update docker-compose.yml to use: image: scanpro:local
goto :show_usage_end
:show_usage_end

REM ==========================================
REM MAIN SCRIPT EXECUTION
REM ==========================================

echo 🐳 ScanPro Local Docker Build Script
echo =====================================
echo.

REM Check prerequisites
call :check_docker
if errorlevel 1 exit /b 1

REM Show build information
call :show_build_info

REM Build the image
echo 🚀 Starting local build process...
call :build_image
if errorlevel 1 exit /b 1

echo ✅ Local build completed successfully!
echo.

REM Show usage instructions
call :show_usage

echo 🎉 Done! Your local ScanPro image is ready.
echo.
pause
