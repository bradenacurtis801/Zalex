# 🐳 ScanPro Docker Setup

This document explains how to build and run ScanPro using Docker.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and start both services (multi-architecture)
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop services
docker-compose down
```

### Option 2: Using Docker directly (Current Method)

```bash
# Build for your current architecture
docker build -t bradenacurtis801/scanpro:latest .

# Run the container
docker run -p 3000:3000 -p 5000:5000 bradenacurtis801/scanpro:latest
```

### Option 3: Multi-Architecture Build (Work in Progress)

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

## ⚙️ Configuration

### Environment Variables

You can customize the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Environment mode |
| `BACKEND_PORT` | `5000` | Backend server port |
| `BACKEND_HOST` | `0.0.0.0` | Backend server host |
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed CORS origins |

### Custom Configuration

Create a `.env` file in the root directory:

```env
NODE_ENV=production
BACKEND_PORT=5000
BACKEND_HOST=0.0.0.0
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Then run with docker-compose:

```bash
docker-compose up --build
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
# Using docker-compose
docker-compose logs -f

# Using docker
docker logs -f <container_id>
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
# Stop and remove containers
docker-compose down

# Remove the image
docker rmi bradenacurtis801/scanpro:latest

# Remove volumes (WARNING: This will delete all data)
docker volume rm scanpro_data
```
