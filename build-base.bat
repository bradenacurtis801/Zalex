@echo off
setlocal enabledelayedexpansion

REM ScanPro Base Image Build Script (Windows)
REM Builds the base image with all heavy dependencies

echo 🏗️  Building ScanPro Base Image
echo ================================
echo.

set "BASE_IMAGE_NAME=bradenacurtis801/scanpro-base:latest"

echo 📋 Base Image Configuration:
echo    Image: %BASE_IMAGE_NAME%
echo    Purpose: Heavy dependencies (Python packages, Node.js, system libs)
echo.

echo 🔨 Building base image for multiple architectures...
docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile.base -t %BASE_IMAGE_NAME% --push .

if errorlevel 1 (
    echo ❌ Base image build failed!
    pause
    exit /b 1
)

echo ✅ Base image built successfully!
echo.
echo 📋 Usage:
echo    The main Dockerfile will now use this base image
echo    Run: .\build-and-push.bat --local-only
echo.
echo 🚀 Benefits:
echo    - Faster builds (dependencies already installed)
echo    - Consistent environment
echo    - Easy to update base dependencies
echo.

pause
