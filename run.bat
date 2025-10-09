@echo off
setlocal enabledelayedexpansion

REM ScanPro Run Script (Windows)
REM Runs the ScanPro containers

echo 🚀 ScanPro Run Script
echo ====================
echo.

REM ==========================================
REM CONFIGURATION VARIABLES
REM ==========================================

set "IMAGE_NAME=bradenacurtis801/scanpro:latest"
set "CONTAINER_NAME=scanpro"
set "FRONTEND_PORT=3000"
set "BACKEND_PORT=5000"

REM ==========================================
REM FUNCTIONS
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

:stop_existing
echo Checking for existing container...
docker ps -q --filter "name=%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo 🛑 Stopping existing container...
    docker stop %CONTAINER_NAME%
    docker rm %CONTAINER_NAME%
)
goto :stop_existing_end
:stop_existing_end

:pull_image
echo 📥 Checking for image...
echo    Image: %IMAGE_NAME%

REM Check if image exists locally first
docker images %IMAGE_NAME% --format "{{.Repository}}:{{.Tag}}" | findstr /C:"%IMAGE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Image found locally, skipping pull
    goto :eof
)

echo 📥 Pulling latest image...
docker pull %IMAGE_NAME%
if errorlevel 1 (
    echo ❌ Failed to pull image. Please check your internet connection and try again.
    echo    Make sure the image exists: %IMAGE_NAME%
    echo    You can try running with --no-pull to use a local image
    pause
    exit /b 1
)
echo ✅ Image pulled successfully
goto :pull_image_end
:pull_image_end

:run_container
echo 🐳 Starting ScanPro container...
echo    Container name: %CONTAINER_NAME%
echo    Frontend port: %FRONTEND_PORT%
echo    Backend port: %BACKEND_PORT%
echo    Image: %IMAGE_NAME%
echo.

docker run -d ^
    --name %CONTAINER_NAME% ^
    -p %FRONTEND_PORT%:%FRONTEND_PORT% ^
    -p %BACKEND_PORT%:%BACKEND_PORT% ^
    -v scanpro_data:/app/backend/APP_DATA ^
    -e NODE_ENV=production ^
    -e DEBUG=false ^
    -e NEXT_PUBLIC_API_URL=http://localhost:%BACKEND_PORT% ^
    --rm ^
    %IMAGE_NAME%

echo.
echo Docker run command completed with error level: %errorlevel%

if errorlevel 1 (
    echo ❌ Failed to start container!
    echo    Check if ports %FRONTEND_PORT% or %BACKEND_PORT% are already in use
    echo    Try: netstat -an | findstr ":%FRONTEND_PORT%"
    echo    Try: netstat -an | findstr ":%BACKEND_PORT%"
    echo    Check container logs: docker logs %CONTAINER_NAME%
    pause
    exit /b 1
)
echo ✅ Container started successfully
goto :run_container_end
:run_container_end

:show_status
echo.
echo ✅ ScanPro is running!
echo.
echo 📋 Container Information:
echo    Name: %CONTAINER_NAME%
echo    Image: %IMAGE_NAME%
echo    Frontend: http://localhost:%FRONTEND_PORT%
echo    Backend: http://localhost:%BACKEND_PORT%
echo    API Docs: http://localhost:%BACKEND_PORT%/docs
echo.
echo 📊 Container Status:
docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo 🔧 Useful Commands:
echo    View logs: docker logs -f %CONTAINER_NAME%
echo    Stop: docker stop %CONTAINER_NAME%
echo    Remove: docker rm %CONTAINER_NAME%
echo    Shell access: docker exec -it %CONTAINER_NAME% /bin/bash
echo.
goto :show_status_end
:show_status_end

:show_help
echo 📖 Usage: run.bat [options]
echo.
echo Options:
echo    --help, -h     Show this help message
echo    --no-pull      Skip pulling image (use local only)
echo    --stop         Stop and remove existing container
echo.
goto :show_help_end
:show_help_end

REM ==========================================
REM MAIN SCRIPT EXECUTION
REM ==========================================

REM Parse command line arguments
set "NO_PULL="
set "STOP_ONLY="

:parse_args
if "%~1"=="" goto :main
if "%~1"=="--help" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="--no-pull" set "NO_PULL=1" & shift & goto :parse_args
if "%~1"=="--stop" set "STOP_ONLY=1" & shift & goto :parse_args
shift
goto :parse_args

:help
call :show_help
pause
exit /b 0

:main
REM Check prerequisites
call :check_docker
if errorlevel 1 exit /b 1

REM Stop existing container
call :stop_existing

REM Handle stop-only option
if defined STOP_ONLY (
    echo ✅ Container stopped and removed.
    pause
    exit /b 0
)

REM Pull image (unless NO_PULL is specified)
if not defined NO_PULL (
    call :pull_image
    if errorlevel 1 exit /b 1
)

REM Run container
call :run_container
if errorlevel 1 exit /b 1

REM Show status
call :show_status

echo 🎉 ScanPro is ready to use!
echo.
pause
