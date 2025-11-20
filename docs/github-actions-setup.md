# GitHub Actions Docker Build Setup

This guide explains how to set up automated Docker builds using GitHub Actions for your project.

## 🚀 Quick Setup

### 1. **Add Docker Hub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

- **`DOCKER_USERNAME`**: Your Docker Hub username
- **`REPOSITORY_NAME`**: Your Docker repository name
- **`DOCKER_PASSWORD`**: Your Docker Hub password or access token

### **Platforms Built**

Both workflows build for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, Apple Silicon, etc.)