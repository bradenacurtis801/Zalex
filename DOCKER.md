# 🐳 ScanPro Docker Setup

This document explains how to build and run ScanPro using Docker.

## 📋 Prerequisites

- Docker installed on your system

## 🚀 Quick Start

### Using Helper Scripts (Recommended)

We provide convenient helper scripts in `scripts/docker/`:

**For macOS/Linux:**
```bash
# Build locally for your architecture
./scripts/docker/build-local.sh

# Run the container
./scripts/docker/run.sh

# Build for multiple architectures (amd64 + arm64)
./scripts/docker/build-multiarch.sh

# Run in debug mode
./scripts/docker/debug-container.sh
```

**For Windows PowerShell:**
```powershell
# Build locally
.\scripts\docker\build-local.ps1

# Run the container
.\scripts\docker\run.ps1

# Build multi-architecture
.\scripts\docker\build-multiarch.ps1
```

### Manual Docker Commands

```bash
# Build for your current architecture
docker build -t bradenacurtis801/scanpro:latest .

# Basic run command
docker run -p 3000:3000 -p 5000:5000 bradenacurtis801/scanpro:latest

# With data persistence
docker run -it --name scanpro \
  -p 3000:3000 \
  -p 5000:5000 \
  -v scanpro_data:/app/backend/APP_DATA \
  --rm \
  bradenacurtis801/scanpro:latest
```

## 🎯 Complete Run Command

### Windows PowerShell
```powershell
docker run -it --rm `
  -p 3000:3000 `
  -p 5000:5000 `
  -v "C:\Users\brade\Downloads\ScanPro\ScanPro\APP_DATA:/app/APP_DATA" `
  -e NODE_ENV=development `
  -e DEBUG=0 `
  -e BACKEND_PORT=5000 `
  -e BACKEND_HOST=0.0.0.0 `
  -e POSTGRES_USERNAME=postgres `
  -e POSTGRES_PASSWORD=postgres123 `
  -e POSTGRES_DB_NAME=scanpro_db `
  -e POSTGRES_HOST=0.0.0.0 `
  -e POSTGRES_PORT=5432 `
  -e CORS_ORIGINS='["http://127.0.0.1:3000"]' `
  bradenacurtis801/scanpro:v2.0.0-dev
```

### macOS/Linux
```bash
docker run -it --rm \
  -p 3000:3000 \
  -p 5000:5000 \
  -v "$(pwd)/APP_DATA:/app/APP_DATA" \
  -e NODE_ENV=development \
  -e DEBUG=0 \
  -e BACKEND_PORT=5000 \
  -e BACKEND_HOST=0.0.0.0 \
  -e POSTGRES_USERNAME=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB_NAME=scanpro_db \
  -e POSTGRES_HOST=0.0.0.0 \
  -e POSTGRES_PORT=5432 \
  -e CORS_ORIGINS='["http://127.0.0.1:3000"]' \
  bradenacurtis801/scanpro:v2.0.0-dev
```

### Windows Command Prompt
```cmd
docker run -it --rm ^
  -p 3000:3000 ^
  -p 5000:5000 ^
  -v "C:\Users\brade\Downloads\ScanPro\ScanPro\APP_DATA:/app/APP_DATA" ^
  -e NODE_ENV=development ^
  -e DEBUG=0 ^
  -e BACKEND_PORT=5000 ^
  -e BACKEND_HOST=0.0.0.0 ^
  -e POSTGRES_USERNAME=postgres ^
  -e POSTGRES_PASSWORD=postgres123 ^
  -e POSTGRES_DB_NAME=scanpro_db ^
  -e POSTGRES_HOST=0.0.0.0 ^
  -e POSTGRES_PORT=5432 ^
  -e CORS_ORIGINS='["http://127.0.0.1:3000"]' ^
  bradenacurtis801/scanpro:v2.0.0-dev
```

## 🏗️ Multi-Architecture Build

> **Note**: Multi-architecture builds are primarily for CI/CD via GitHub Actions. They run automatically when you push to a version branch. Manual multi-arch builds are typically not needed for local development as they take a long time to build.

### Automated CI/CD (Recommended)

Multi-architecture builds are automatically triggered by GitHub Actions when pushing to version branches:

```bash
# Push to version branch to trigger automatic multi-arch build
git push origin v2.1.0
```

GitHub Actions will automatically:
- Build for both `linux/amd64` (Intel) and `linux/arm64` (Apple Silicon/M1)
- Tag with version and `latest`
- Push to Docker Hub

### Manual Multi-Architecture Build (Advanced)

Only use manually if you need to build locally:

**macOS/Linux:**
```bash
./scripts/docker/build-multiarch.sh
```

**Windows PowerShell:**
```powershell
.\scripts\docker\build-multiarch.ps1
```

**Warning**: This will take a long time to build and push to Docker Hub. For development, use `build-local.sh` instead.

## 🌐 Accessing the Application

Once running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 🚀 Docker Run Command Reference

### Basic Syntax
```bash
docker run [OPTIONS] bradenacurtis801/scanpro:latest
```

### Port Mapping
| Host Port | Container Port | Service | Description |
|-----------|----------------|---------|-------------|
| `3000` | `3000` | Frontend | Next.js web interface |
| `5000` | `5000` | Backend | FastAPI server |
| `5678` | `5678` | Debugger | Remote debugging backend inside container (requires VS Code configuration) |

### Common Options

#### Port Mapping
```bash
# Map ports (host:container)
-p 3000:3000    # Frontend
-p 5000:5000    # Backend
-p 5678:5678    # Debugger (when DEBUG=1 or DEBUG=2)
```

#### Container Management
```bash
--name scanpro          # Name the container
--rm                    # Remove container when it stops
-it                     # Interactive mode with TTY
-d                      # Run in background (detached)
```

#### Data Persistence
```bash
# Mount volume for data persistence
-v scanpro_data:/app/backend/APP_DATA

# Mount local directory (development)
-v $(pwd)/data:/app/backend/APP_DATA
```

#### Environment Variables
```bash
# Set environment variables
-e NODE_ENV=production
-e DEBUG=0
-e BACKEND_PORT=5000
-e CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

## 🐛 Debug Options

### Local Development with Containerized Database

For easier debugging, you can run PostgreSQL in a Docker container while running the backend on your local machine.

#### Quick Start (Recommended)

```bash
# Terminal 1: Start PostgreSQL in its own container
python scripts/run_dev_database.py

# Terminal 2: Run the backend on your host machine
cd backend
python main.py
```

This setup:
- PostgreSQL runs in Docker with your data mounted
- Backend runs natively on your host (easier to debug)
- Reads configuration from `backend/config.py`
- Mounts your local `APP_DATA/db/postgres_data/` directory
- Applies development PostgreSQL configs from `scripts/dev_db_config/`
- Exposes PostgreSQL on port 5432 for local backend connection

**Benefits:**
- Debug backend with local tools (VS Code, Python debugger)
- Direct access to backend logs and process
- Database persists in container
- Easy to restart just the database or just the backend

### Summary

**Two ways to run ScanPro:**

1. **All-in-One Container** (Production/Testing):
   - Everything in one container (PostgreSQL, Backend, Frontend)
   - See "Quick Start" section above
   - `docker run ... bradenacurtis801/scanpro:latest`

2. **PostgreSQL in Container + Backend on Host** (Local Development):
   - PostgreSQL in Docker, Backend runs locally for easier debugging
   - See "Local Development with Containerized Database" section above
   - Use `python scripts/run_dev_database.py` + run backend locally

#### Stopping the Development Database

**If using the helper script (`run_dev_database.py`):**
```bash
# Just press Ctrl+C in the terminal where it's running
# The --rm flag will automatically remove the container
```

**If started manually with docker run:**
```bash
# Stop the PostgreSQL container
docker stop scanpro-postgres

# Remove the container (if started without --rm)
docker rm scanpro-postgres
```

**Using Docker Desktop:**
- Go to Containers tab
- Find `scanpro-postgres`
- Click Stop or Delete

### Debug Mode Levels

| DEBUG Value | Description | Use Case |
|-------------|-------------|----------|
| `0` or unset | Production mode | Normal operation |
| `1` | Debug with wait | Debug startup issues, waits for debugger |
| `2` | Debug without wait | Debug runtime issues, starts normally |

### Debug Commands

#### Production Mode
```bash
docker run -it --name scanpro \
  -p 3000:3000 \
  -p 5000:5000 \
  -v scanpro_data:/app/backend/APP_DATA \
  -e NODE_ENV=production \
  -e DEBUG=0 \
  --rm \
  bradenacurtis801/scanpro:latest
```

#### Debug Mode 1 (Wait for Debugger)
```bash
docker run -it --name scanpro-debug \
  -p 3000:3000 \
  -p 5000:5000 \
  -p 5678:5678 \
  -v scanpro_data:/app/backend/APP_DATA \
  -e NODE_ENV=production \
  -e DEBUG=1 \
  --rm \
  bradenacurtis801/scanpro:latest
```
- **Use case**: Debug startup issues
- **Behavior**: Waits for VS Code debugger to connect before starting
- **VS Code**: Connect using "Python: Remote Attach" configuration

#### Debug Mode 2 (No Wait)
```bash
docker run -it --name scanpro-debug \
  -p 3000:3000 \
  -p 5000:5000 \
  -p 5678:5678 \
  -v scanpro_data:/app/backend/APP_DATA \
  -e NODE_ENV=production \
  -e DEBUG=2 \
  --rm \
  bradenacurtis801/scanpro:latest
```
- **Use case**: Debug runtime issues (like segfaults)
- **Behavior**: Starts normally, debugger can connect anytime
- **VS Code**: Connect when ready to debug

### Debugging Approaches

You have two options for debugging the backend:

#### Option 1: Debug Backend on Host (Recommended for Development)

PostgreSQL in container + Backend on host for easier debugging:

```bash
# Terminal 1: Start PostgreSQL
python scripts/run_dev_database.py

# Terminal 2: Run backend on host (easier debugging)
cd backend
python main.py
```

**Benefits:**
- No VS Code configuration needed
- Direct access to backend process
- Faster iteration
- Use native debugging tools

#### Option 2: Debug Backend Inside Container (Simulate Runtime Environment)

Debug the backend inside the container to match production runtime:

```bash
# Run container with debug port
docker run -it --rm \
  -p 3000:3000 -p 5000:5000 -p 5678:5678 \
  -e DEBUG=1 \
  bradenacurtis801/scanpro:latest
```

### VS Code Configuration for Container Debugging

**Only needed for Option 2 (debugging inside container).**

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Attach to Container",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/backend",
                    "remoteRoot": "/app/backend"
                }
            ],
            "justMyCode": false
        }
    ]
}
```

**Steps:**
1. Set breakpoints in your Python code
2. Start container with `DEBUG=1` (waits for debugger) or `DEBUG=2` (runs normally)
3. Press F5 in VS Code to attach debugger to the container

**Note**: This requires configuring launch.json and path mappings to connect your local code to the code running inside the container.

## ⚙️ Configuration

### Environment Variables

You can customize the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Environment mode (development/production) |
| `DEBUG` | `0` | Debug mode (0=prod, 1=debug+wait, 2=debug+no-wait) |
| `BACKEND_PORT` | `5000` | Backend server port |
| `BACKEND_HOST` | `0.0.0.0` | Backend server host |
| `POSTGRES_USERNAME` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres123` | PostgreSQL password |
| `POSTGRES_DB_NAME` | `scanpro_db` | PostgreSQL database name |
| `POSTGRES_HOST` | `0.0.0.0` | PostgreSQL server host |
| `POSTGRES_PORT` | `5432` | PostgreSQL server port |
| `CORS_ORIGINS` | `["http://127.0.0.1:3000"]` | Allowed CORS origins (JSON array) |

### Custom Configuration

You can set environment variables directly in the docker run command:

```bash
docker run -it --name scanpro \
  -p 3000:3000 \
  -p 5000:5000 \
  -v scanpro_data:/app/backend/APP_DATA \
  -e NODE_ENV=production \
  -e DEBUG=0 \
  -e BACKEND_PORT=5000 \
  -e CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000" \
  --rm \
  bradenacurtis801/scanpro:latest
```

## 📁 Data Persistence

The application data is stored in a Docker volume named `scanpro_data`. This ensures your data persists between container restarts.

To view the volume:
```bash
docker volume ls
docker volume inspect scanpro_data
```

## 🔧 Development

### Helper Scripts

We provide several helper scripts in `scripts/docker/` to make Docker operations easier:

**Available Scripts (macOS/Linux):**
- `build-local.sh` - Build for your local architecture (use for development)
- `run.sh` - Run the container with proper configuration
- `build-multiarch.sh` - Build for multiple architectures (mainly for CI/CD, takes long time)
- `debug-container.sh` - Run in debug mode with debugger support

**Available Scripts (Windows PowerShell):**
- `build-local.ps1` - Build for your local architecture (use for development)
- `run.ps1` - Run the container with proper configuration
- `build-multiarch.ps1` - Build for multiple architectures (mainly for CI/CD, takes long time)

### Building for Development

Using helper script (recommended):
```bash
./scripts/docker/build-local.sh
```

Or manually:
```bash
# Build with development settings
docker build --build-arg NODE_ENV=development -t bradenacurtis801/scanpro:dev .

# Run with development settings
docker run -p 3000:3000 -p 5000:5000 \
  -e NODE_ENV=development \
  -e DEBUG=true \
  bradenacurtis801/scanpro:dev
```

### Viewing Logs

```bash
# View container logs
docker logs -f <container_id>

# Or if you named the container
docker logs -f scanpro

# View specific log files inside the container
docker exec <container_id> cat /app/APP_DATA/logs/app.log
docker exec <container_id> cat /app/APP_DATA/logs/frontend.log
docker exec <container_id> cat /app/APP_DATA/db/postgres.log

# Follow logs in real-time
docker exec <container_id> tail -f /app/APP_DATA/logs/frontend.log
```

### Log Files

The application creates several log files in `/app/APP_DATA/logs/`:

| File | Description | Location |
|------|-------------|----------|
| `app.log` | Backend application logs | `/app/APP_DATA/logs/app.log` |
| `frontend.log` | Frontend Next.js server logs | `/app/APP_DATA/logs/frontend.log` |
| `postgres.log` | PostgreSQL database logs | `/app/APP_DATA/db/postgres.log` |

## 🐛 Troubleshooting

### Port Already in Use

If ports 3000 or 5000 are already in use:

```bash
# Use different ports
docker run -p 3001:3000 -p 5001:5000 scanpro:latest
```

### Frontend Can't Reach Backend

The frontend uses a Next.js proxy to communicate with the backend. If you're having issues:

1. **Check the proxy configuration** in `frontend/next.config.js`
2. **Ensure the backend is running** on port 5000
3. **Check CORS settings** in the backend configuration

### Health Check Failing

The health check might fail if the backend takes time to start. You can disable it:

```bash
docker run -p 3000:3000 -p 5000:5000 \
  --health-cmd="echo 'Health check disabled'" \
  scanpro:latest
```

## 🧹 Cleanup

```bash
# Stop and remove container
docker stop scanpro
docker rm scanpro

# Remove the image
docker rmi bradenacurtis801/scanpro:latest

# Remove volumes (WARNING: This will delete all data)
docker volume rm scanpro_data

# Remove all unused images
docker image prune -a
```
