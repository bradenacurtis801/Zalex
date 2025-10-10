# 🐳 ScanPro Docker Setup

This document explains how to build and run ScanPro using Docker.

## 📋 Prerequisites

- Docker installed on your system

## 🚀 Quick Start

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

## 🏗️ Multi-Architecture Build (Work in Progress)

> **Note**: The multi-platform build script (`build-and-push.sh`) is currently under development. For now, use the simple build command above.

```bash
# Multi-platform build (experimental)
./build-and-push.sh

# This will build for both Intel and Apple M1 architectures
# and push to Docker Hub when ready
```

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
| `5678` | `5678` | Debugger | VS Code remote debugging (debug mode only) |

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

### VS Code Debugging Setup

1. **Install Python extension** in VS Code
2. **Create `.vscode/launch.json`**:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
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
            ]
        }
    ]
}
```
3. **Set breakpoints** in your Python code
4. **Start container** with `DEBUG=1` or `DEBUG=2`
5. **Press F5** in VS Code to connect debugger

## ⚙️ Configuration

### Environment Variables

You can customize the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Environment mode |
| `BACKEND_PORT` | `5000` | Backend server port |
| `BACKEND_HOST` | `0.0.0.0` | Backend server host |
| `DEBUG` | `0` | Debug mode (0=prod, 1=debug+wait, 2=debug+no-wait) |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed CORS origins |

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

### Building for Development

```bash
# Build with development settings
docker build --build-arg NODE_ENV=development -t bradenacurtis801/scanpro:dev .

# Run with development settings
docker run -p 3000:3000 -p 5000:5000 \
  -e NODE_ENV=development \
  -e DEBUG=true \
  bradenacurtis801/scanpro:dev
```

### Multi-Architecture Development (Work in Progress)

> **Note**: Multi-architecture builds are currently under development. Use the simple build command for now.

```bash
# Multi-platform build (experimental)
./build-and-push.sh

# This will create architecture-specific tags when ready
```

### Viewing Logs

```bash
# View container logs
docker logs -f <container_id>

# Or if you named the container
docker logs -f scanpro
```

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
