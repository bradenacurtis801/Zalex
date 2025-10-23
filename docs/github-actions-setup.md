# GitHub Actions Docker Build Setup

This guide explains how to set up automated Docker builds using GitHub Actions for your ScanPro project.

## 🚀 Quick Setup

### 1. **Add Docker Hub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

- **`DOCKER_USERNAME`**: `bradenacurtis801`
- **`DOCKER_PASSWORD`**: Your Docker Hub password or access token

### 2. **Choose Your Workflow**

You have two options:

#### Option A: Standard GitHub Actions Workflow
- **File**: `.github/workflows/docker-build-multiarch.yml`
- **Features**: Uses GitHub Actions native Docker build
- **Pros**: Faster, more reliable, better caching
- **Cons**: Doesn't use your custom script

#### Option B: Custom Script Workflow  
- **File**: `.github/workflows/docker-custom-script.yml`
- **Features**: Runs your `build-multiarch.sh` script
- **Pros**: Uses your existing script logic
- **Cons**: Slightly slower, more complex

### 3. **Enable the Workflow**

1. Commit and push the workflow files to your repository
2. Go to Actions tab in your GitHub repository
3. The workflow will automatically run on the next push

## 🔧 Configuration

### **Trigger Events**

The workflows run on:
- **Push** to `main`, `master`, or `develop` branches
- **Pull Requests** to `main` or `master` branches  
- **Manual trigger** via GitHub UI

### **Image Tagging Strategy**

Images are tagged based on:
- **Branch name**: `bradenacurtis801/scanpro:feature-branch`
- **Latest**: `bradenacurtis801/scanpro:latest` (for main/master)
- **SHA**: `bradenacurtis801/scanpro:main-abc1234` (for commits)

### **Platforms Built**

Both workflows build for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, Apple Silicon, etc.)

## 📋 Usage Examples

### **Pull and Run**

```bash
# Pull the latest image (auto-selects your architecture)
docker pull bradenacurtis801/scanpro:latest

# Run the application
docker run -p 3000:3000 -p 5000:5000 bradenacurtis801/scanpro:latest
```

### **Pull Specific Architecture**

```bash
# For Intel/AMD systems
docker pull --platform linux/amd64 bradenacurtis801/scanpro:latest

# For ARM systems (Apple Silicon, Raspberry Pi, etc.)
docker pull --platform linux/arm64 bradenacurtis801/scanpro:latest
```

### **Use in Docker Compose**

```yaml
version: '3.8'
services:
  scanpro:
    image: bradenacurtis801/scanpro:latest
    ports:
      - "3000:3000"
      - "5000:5000"
    environment:
      - NODE_ENV=production
```

## 🔍 Monitoring Builds

### **View Build Status**

1. Go to your GitHub repository
2. Click the "Actions" tab
3. See build history and status

### **Build Logs**

- Click on any workflow run to see detailed logs
- Check for any build errors or warnings
- Monitor build times and success rates

## 🛠️ Customization

### **Modify Triggers**

Edit the workflow files to change when builds run:

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]  # Add more branches
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

### **Add More Platforms**

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7  # Add ARM v7
```

### **Custom Build Arguments**

```yaml
with:
  build-args: |
    BUILD_DATE=${{ github.event.head_commit.timestamp }}
    VERSION=${{ github.sha }}
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Docker Hub Authentication Failed**
   - Check your `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
   - Ensure Docker Hub account has push permissions

2. **Build Timeout**
   - Multi-architecture builds can take 10-20 minutes
   - Consider using build caching (already enabled)

3. **Platform Not Supported**
   - Some platforms may not be available on GitHub runners
   - Check the Actions logs for specific errors

### **Debug Mode**

Add this to your workflow for more verbose output:

```yaml
- name: Build and push
  run: |
    docker buildx build --progress=plain --no-cache ...
```

## 📈 Performance Tips

### **Enable Caching**

The workflows already include:
- **GitHub Actions Cache**: For build layers
- **Multi-stage builds**: For smaller final images
- **BuildKit**: For faster builds

### **Optimize Dockerfile**

- Use `.dockerignore` to exclude unnecessary files
- Leverage multi-stage builds
- Use specific base image tags (not `latest`)

## 🔐 Security

### **Secrets Management**

- Never commit Docker Hub credentials to code
- Use GitHub Secrets for sensitive information
- Rotate access tokens regularly

### **Image Security**

- Scan images for vulnerabilities
- Use minimal base images
- Keep dependencies updated

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/)
- [Multi-Architecture Images Guide](https://docs.docker.com/build/building/multi-platform/)
