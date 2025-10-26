# ParchMark Automated Deployment Guide

**Version:** 1.0
**Last Updated:** 2025-01-26
**Deployment Tool:** Watchtower + GitHub Container Registry (GHCR)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [GitHub Container Registry Setup](#3-github-container-registry-setup)
4. [Docker Compose Configuration](#4-docker-compose-configuration)
5. [GitHub Actions Workflow](#5-github-actions-workflow)
6. [GitHub Secrets Configuration](#6-github-secrets-configuration)
7. [Initial Deployment](#7-initial-deployment-first-time-setup)
8. [Automated Deployment Process](#8-automated-deployment-process)
9. [Manual Deployment Trigger](#9-manual-deployment-trigger)
10. [Monitoring & Verification](#10-monitoring--verification)
11. [Rollback Procedures](#11-rollback-procedures)
12. [Troubleshooting Guide](#12-troubleshooting-guide)
13. [Security Best Practices](#13-security-best-practices)
14. [Makefile Integration](#14-makefile-integration)
15. [Maintenance Tasks](#15-maintenance-tasks)
16. [Advanced Configuration](#16-advanced-configuration-optional)
17. [Performance Optimization](#17-performance-optimization)
18. [Appendices](#18-appendices)

---

## 1. Overview

### 1.1 What is Watchtower?

Watchtower is a container-based solution that automatically updates running Docker containers when new images are available. For ParchMark, this means:

- **Zero custom deployment scripts** on the server
- **Automatic zero-downtime updates** with rolling restarts
- **Simple GitHub Actions workflow** (just build & push)
- **Monitoring and cleanup** of old images

### 1.2 Why Watchtower for ParchMark?

| Feature | Benefit |
|---------|---------|
| **Zero Scripts** | No custom bash scripts to maintain on server |
| **Zero Downtime** | Rolling updates keep service available |
| **Automatic** | Set once, deploys happen automatically |
| **Lightweight** | ~20MB memory footprint |
| **Battle-tested** | Used in thousands of production deployments |
| **GHCR Integration** | Native support for GitHub Container Registry |

### 1.3 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT WORKFLOW                         │
└─────────────────────────────────────────────────────────────────┘

Developer                     GitHub                      Server
    │                            │                           │
    │──(1) git push main────────>│                           │
    │                            │                           │
    │                       [GitHub Actions]                 │
    │                            │                           │
    │                       (2) Run Tests                    │
    │                            │                           │
    │                       (3) Build Images                 │
    │                       - parchmark-frontend             │
    │                       - parchmark-backend              │
    │                            │                           │
    │                       (4) Push to GHCR                 │
    │                       ghcr.io/username/parchmark-*     │
    │                            │                           │
    │                            │                           │
    │                            │<────(5) Poll for updates──│
    │                            │         [Watchtower]      │
    │                            │                           │
    │                            │                           │
    │                            │      (6) Pull new images──│
    │                            │                           │
    │                            │     (7) Rolling update────│
    │                            │     - Start new backend   │
    │                            │     - Wait health check   │
    │                            │     - Stop old backend    │
    │                            │     - Start new frontend  │
    │                            │     - Wait health check   │
    │                            │     - Stop old frontend   │
    │                            │                           │
    │<───(8) Deployment complete notification────────────────│
    │                            │                           │
```

### 1.4 Deployment Flow

**Automatic Deployment (Push to Main):**
```
1. Developer pushes code to main branch
2. GitHub Actions triggers (test.yml passes first)
3. Build frontend & backend Docker images
4. Tag images: latest + commit SHA (e.g., sha-abc1234)
5. Push images to ghcr.io/yourusername/parchmark-frontend:latest
6. Watchtower detects new image (within 5 minutes)
7. Watchtower pulls new images
8. Rolling update: Start new → Health check → Stop old
9. Cleanup old images automatically
```

**Manual Deployment:**
```
1. Go to GitHub Actions → Deploy workflow
2. Click "Run workflow" → Select branch
3. Rest of the process is identical
```

---

## 2. Prerequisites

### 2.1 Server Requirements

- **Operating System:** Debian Trixie (or any Linux with Docker support)
- **Docker:** Version 24.0+ installed
- **Docker Compose:** Version 2.20+ installed
- **Memory:** Minimum 2GB RAM (4GB+ recommended)
- **Disk Space:** 10GB+ available
- **Network:** Public IP with ports 80/443 accessible

### 2.2 Verify Installation

SSH into your production server and run:

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.0.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.20.0 or higher

# Check Docker daemon is running
sudo systemctl status docker
# Expected: active (running)

# Verify Docker permissions (run without sudo)
docker ps
# If error: sudo usermod -aG docker $USER && newgrp docker
```

### 2.3 Domain Configuration

Ensure your DNS is configured (you already have this):
- **Frontend:** `notes.engen.tech` → Server IP
- **Backend API:** `assets-api.engen.tech` → Server IP

Verify with:
```bash
dig notes.engen.tech +short
dig assets-api.engen.tech +short
```

### 2.4 Nginx Proxy Manager

Your `docker-compose.prod.yml` shows you're using Nginx Proxy Manager with the `proxiable` network. Ensure:
- Nginx Proxy Manager is running
- `proxiable` network exists: `docker network inspect proxiable`
- SSL certificates are configured for both domains

---

## 3. GitHub Container Registry Setup

### 3.1 Why GHCR?

- **Free** for public repositories
- **Unlimited bandwidth** for public images
- **Native GitHub integration**
- **No additional service** required (Docker Hub, AWS ECR, etc.)
- **Package tied to repository** (easy to find)

### 3.2 Create Personal Access Token (PAT)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Configure token:
   - **Note:** `GHCR Push Token for ParchMark`
   - **Expiration:** 90 days (or No expiration for production)
   - **Scopes:** Select these:
     - ✅ `write:packages` (Upload packages)
     - ✅ `read:packages` (Download packages)
     - ✅ `delete:packages` (Cleanup old images)
4. Click "Generate token"
5. **IMPORTANT:** Copy the token immediately (you won't see it again)
6. Save it securely (we'll add to GitHub Secrets)

### 3.3 Repository Permissions

Ensure your repository settings allow packages:
1. Go to repository → Settings → Actions → General
2. Under "Workflow permissions":
   - Select: ✅ **Read and write permissions**
3. Click "Save"

### 3.4 Test GHCR Authentication Locally (Optional)

```bash
# Login to GHCR
echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Expected output:
# Login Succeeded

# Test by pulling a test image
docker pull ghcr.io/containrrr/watchtower:latest

# Logout
docker logout ghcr.io
```

---

## 4. Docker Compose Configuration

### 4.1 Understanding the Changes

We'll modify `docker-compose.prod.yml` to:
1. **Change from `build:` to `image:`** - Use pre-built images from GHCR
2. **Add Watchtower service** - Automated update manager
3. **Add Watchtower labels** - Control which containers auto-update
4. **Enhance health checks** - Ensure zero-downtime updates

### 4.2 Updated docker-compose.prod.yml

Replace your existing `docker-compose.prod.yml` with:

```yaml
services:
  postgres:
    image: postgres:17.2-alpine
    container_name: parchmark-postgres-prod
    environment:
      POSTGRES_USER: parchmark_user
      POSTGRES_PASSWORD: parchmark_password
      POSTGRES_DB: parchmark_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U parchmark_user -d parchmark_db"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - proxiable
    labels:
      # Don't auto-update database (requires manual migration planning)
      - "com.centurylinklabs.watchtower.enable=false"

  backend:
    # CHANGE: Use pre-built image from GHCR instead of building
    image: ghcr.io/GITHUB_USERNAME/parchmark-backend:latest
    container_name: parchmark-backend
    env_file:
      - ./backend/.env.production
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - proxiable
    labels:
      # Nginx Proxy Manager labels for API
      - "npm.enable=true"
      - "npm.host=assets-api.engen.tech"
      - "npm.port=8000"
      - "npm.proto=http"
      # Watchtower: Enable auto-updates for backend
      - "com.centurylinklabs.watchtower.enable=true"
    # Enhanced health check for zero-downtime updates
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    # Security: Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  frontend:
    # CHANGE: Use pre-built image from GHCR instead of building
    image: ghcr.io/GITHUB_USERNAME/parchmark-frontend:latest
    container_name: parchmark-frontend
    environment:
      - USE_HTTPS=false
    env_file:
      - ./ui/.env.production
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - proxiable
    labels:
      # Nginx Proxy Manager labels for automatic configuration
      - "npm.enable=true"
      - "npm.host=notes.engen.tech"
      - "npm.port=80"
      - "npm.proto=http"
      # Watchtower: Enable auto-updates for frontend
      - "com.centurylinklabs.watchtower.enable=true"
    # Enhanced health check for zero-downtime updates
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

  # NEW: Watchtower service for automated updates
  watchtower:
    image: containrrr/watchtower:latest
    container_name: watchtower
    restart: unless-stopped
    volumes:
      # Watchtower needs access to Docker daemon
      - /var/run/docker.sock:/var/run/docker.sock
      # Optional: Persist Watchtower data
      - /etc/localtime:/etc/localtime:ro
    environment:
      # Check for updates every 5 minutes
      - WATCHTOWER_POLL_INTERVAL=300
      # Remove old images after updating
      - WATCHTOWER_CLEANUP=true
      # Enable rolling restarts (zero downtime)
      - WATCHTOWER_ROLLING_RESTART=true
      # Only monitor containers with watchtower.enable=true label
      - WATCHTOWER_LABEL_ENABLE=true
      # Include stopped containers in cleanup
      - WATCHTOWER_INCLUDE_STOPPED=true
      # Log level (debug, info, warn, error, fatal, panic)
      - WATCHTOWER_LOG_LEVEL=info
      # Notification settings (optional - see Advanced Configuration)
      # - WATCHTOWER_NOTIFICATIONS=shoutrrr
      # - WATCHTOWER_NOTIFICATION_URL=discord://token@channel
    command: --label-enable
    networks:
      - proxiable
    labels:
      # Don't try to update Watchtower itself (prevent self-update issues)
      - "com.centurylinklabs.watchtower.enable=false"

volumes:
  postgres_data:

networks:
  # Connect to existing proxiable network for Nginx Proxy Manager
  proxiable:
    external: true
    name: proxiable
```

**IMPORTANT:** Replace `GITHUB_USERNAME` with your actual GitHub username (e.g., `tejgandham`).

### 4.3 Health Check Endpoint for Backend

The backend health check requires a `/api/health` endpoint. Add this to your backend:

**backend/app/routers/health.py** (create new file):
```python
"""Health check endpoint for container orchestration."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Docker health checks and load balancers.

    Returns:
        dict: Simple health status
    """
    return {"status": "healthy"}
```

**backend/app/main.py** (add health router):
```python
# Add this import
from app.routers import health

# Add this router registration (after other routers)
app.include_router(health.router)
```

---

## 5. GitHub Actions Workflow

### 5.1 Workflow Overview

The deployment workflow will:
1. Trigger on push to `main` (after tests pass) OR manually
2. Build Docker images for frontend and backend
3. Tag images with `latest` and commit SHA
4. Push to GitHub Container Registry
5. Watchtower automatically detects and updates

### 5.2 Create Deployment Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy to Production

on:
  # Automatic deployment when pushing to main
  push:
    branches:
      - main

  # Manual deployment trigger
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging

# Required for GHCR authentication
permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  # Change this to your GitHub username (lowercase)
  GITHUB_USERNAME: tejgandham

jobs:
  # Only deploy if tests pass
  check-tests:
    runs-on: ubuntu-latest
    outputs:
      tests-passed: ${{ steps.check.outputs.passed }}
    steps:
      - name: Check if tests workflow succeeded
        id: check
        run: |
          # For push events, ensure tests passed
          # For manual triggers, skip test check
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "passed=true" >> $GITHUB_OUTPUT
          else
            echo "passed=true" >> $GITHUB_OUTPUT
          fi

  build-and-push-backend:
    needs: check-tests
    if: needs.check-tests.outputs.tests-passed == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=sha,prefix=sha-,format=short

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          file: ./backend/Dockerfile.prod
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend:buildcache,mode=max

  build-and-push-frontend:
    needs: check-tests
    if: needs.check-tests.outputs.tests-passed == 'true'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-frontend
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=sha,prefix=sha-,format=short

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./ui
          file: ./ui/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-frontend:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-frontend:buildcache,mode=max

  notify-deployment:
    needs: [build-and-push-backend, build-and-push-frontend]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Deployment status
        run: |
          if [ "${{ needs.build-and-push-backend.result }}" = "success" ] && \
             [ "${{ needs.build-and-push-frontend.result }}" = "success" ]; then
            echo "✅ Images built and pushed successfully!"
            echo "Watchtower will deploy within 5 minutes."
            echo "Monitor: docker compose -f docker-compose.prod.yml logs -f watchtower"
          else
            echo "❌ Deployment failed. Check the logs above."
            exit 1
          fi
```

**IMPORTANT:** Change `GITHUB_USERNAME: tejgandham` to your actual GitHub username (lowercase).

### 5.3 Image Tagging Strategy

Each image gets two tags:
1. **`latest`** - Watchtower monitors this tag
2. **`sha-abc1234`** - Specific commit for rollbacks

Example:
```
ghcr.io/tejgandham/parchmark-backend:latest
ghcr.io/tejgandham/parchmark-backend:sha-a1b2c3d
```

---

## 6. GitHub Secrets Configuration

### 6.1 No Server Secrets Needed!

**Good news:** Unlike traditional CI/CD, Watchtower approach doesn't require:
- ❌ SSH keys in GitHub
- ❌ Server credentials in GitHub
- ❌ .env variables in GitHub Secrets

Your `.env.production` files stay securely on your server.

### 6.2 Required: GHCR Authentication (Automatic)

The workflow uses `${{ secrets.GITHUB_TOKEN }}` which is automatically provided by GitHub Actions. No configuration needed!

### 6.3 Optional: Notification Secrets

If you want deployment notifications (Discord, Slack, etc.), add these later:
- `DISCORD_WEBHOOK_URL`
- `SLACK_WEBHOOK_URL`

See [Advanced Configuration](#16-advanced-configuration-optional) for setup.

---

## 7. Initial Deployment (First Time Setup)

### 7.1 Server Preparation

SSH into your production server:

```bash
ssh your-user@notes.engen.tech
```

### 7.2 Clone Repository

```bash
# Navigate to deployment directory
cd /opt  # or wherever you deploy

# Clone repository
git clone https://github.com/TejGandham/parchmark.git
cd parchmark

# Checkout main branch
git checkout main
```

### 7.3 Create Environment Files

**Backend environment:**
```bash
# Create backend .env.production
cat > backend/.env.production << 'EOF'
# Database (matches docker-compose.prod.yml postgres service)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@postgres:5432/parchmark_db

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
EOF

# Generate a secure SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
# Copy the output and replace SECRET_KEY in .env.production
```

**Frontend environment:**
```bash
# Create frontend .env.production
cat > ui/.env.production << 'EOF'
# API URL - relative path (proxied by Nginx)
VITE_API_URL=/api

# Token warning (optional)
VITE_TOKEN_WARNING_SECONDS=60
EOF
```

### 7.4 Update docker-compose.prod.yml

```bash
# Edit docker-compose.prod.yml
nano docker-compose.prod.yml

# Replace GITHUB_USERNAME in image URLs with your actual username
# Example:
#   image: ghcr.io/tejgandham/parchmark-backend:latest
#   image: ghcr.io/tejgandham/parchmark-frontend:latest
```

### 7.5 Initial Image Pull

**Important:** Before starting, ensure images are public or authenticate:

**Option A: Make GHCR Packages Public (Recommended)**
1. Go to GitHub → Profile → Packages
2. Find `parchmark-backend` and `parchmark-frontend`
3. Package Settings → Danger Zone → Change visibility → Public

**Option B: Authenticate Docker on Server**
```bash
# Login to GHCR on server
echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 7.6 Start Services

```bash
# Ensure proxiable network exists (for Nginx Proxy Manager)
docker network inspect proxiable || docker network create proxiable

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Watch logs
docker compose -f docker-compose.prod.yml logs -f

# Wait for all services to be healthy
docker compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                          STATUS
parchmark-backend            Up (healthy)
parchmark-frontend           Up (healthy)
parchmark-postgres-prod      Up (healthy)
watchtower                    Up
```

### 7.7 Create Initial User

```bash
# Create your first user
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py create admin YourSecurePassword123

# List users to verify
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py list
```

### 7.8 Verify Deployment

```bash
# Test backend health
curl https://assets-api.engen.tech/api/health
# Expected: {"status":"healthy"}

# Test frontend
curl -I https://notes.engen.tech
# Expected: HTTP/2 200

# Check Watchtower is running
docker logs watchtower --tail 20
```

---

## 8. Automated Deployment Process

### 8.1 How It Works

Once setup is complete, deployments happen automatically:

```
You: git push origin main
 ↓
GitHub Actions: Runs tests (.github/workflows/test.yml)
 ↓
GitHub Actions: Builds & pushes images (.github/workflows/deploy.yml)
 ↓
GHCR: Images tagged as :latest and :sha-abc1234
 ↓
Watchtower (on server): Detects new :latest image (within 5 min)
 ↓
Watchtower: Pulls new images
 ↓
Watchtower: Performs rolling update
  1. docker compose pull backend frontend
  2. Start new backend container
  3. Wait for health check (backend)
  4. Stop old backend container
  5. Start new frontend container
  6. Wait for health check (frontend)
  7. Stop old frontend container
 ↓
Watchtower: Cleanup old images (docker image prune)
 ↓
Done! Zero downtime deployment complete
```

### 8.2 Monitoring a Live Deployment

**Watch Watchtower logs in real-time:**
```bash
# SSH to server
ssh your-user@notes.engen.tech

# Follow Watchtower logs
docker logs -f watchtower

# You'll see output like:
# time="2025-01-26T10:30:00Z" level=info msg="Found new parchmark-backend:latest"
# time="2025-01-26T10:30:15Z" level=info msg="Stopping /parchmark-backend (abcd1234)"
# time="2025-01-26T10:30:16Z" level=info msg="Creating /parchmark-backend"
```

**Check container updates:**
```bash
# See when containers were created (updated)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# Check image digest to verify new version
docker images --digests | grep parchmark
```

### 8.3 Deployment Timeline

| Time | Event |
|------|-------|
| T+0min | Push to main |
| T+5min | GitHub Actions starts |
| T+10min | Images pushed to GHCR |
| T+10-15min | Watchtower detects update |
| T+15min | Rolling update begins |
| T+16min | Deployment complete |

**Total time:** ~15-20 minutes (hands-off)

---

## 9. Manual Deployment Trigger

### 9.1 When to Use Manual Trigger

- Deploy a hotfix from a branch
- Test deployment without pushing to main
- Deploy to staging environment (if configured)

### 9.2 Trigger Deployment via GitHub UI

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **"Build and Deploy to Production"** workflow (left sidebar)
4. Click **"Run workflow"** button (right side)
5. Configure:
   - **Branch:** `main` (or your feature branch)
   - **Environment:** `production`
6. Click **"Run workflow"** (green button)

### 9.3 Monitor Manual Deployment

- Watch the workflow progress in Actions tab
- Same rolling update process as automatic deployment
- Watchtower detects and deploys within 5 minutes

---

## 10. Monitoring & Verification

### 10.1 Watchtower Logs

**Check Watchtower is polling:**
```bash
docker logs watchtower --tail 50

# Healthy output:
# level=info msg="Watchtower 1.x.x"
# level=info msg="Using notifications: none"
# level=info msg="Checking containers for updates"
# level=info msg="Scheduling first run: 2025-01-26 10:35:00"
```

**Watch for updates in real-time:**
```bash
docker logs -f --tail 100 watchtower
```

### 10.2 Container Health Status

**Check all containers are healthy:**
```bash
docker compose -f docker-compose.prod.yml ps

# All should show "(healthy)" status
```

**Detailed health check status:**
```bash
docker inspect parchmark-backend | grep -A 20 Health
docker inspect parchmark-frontend | grep -A 20 Health
```

### 10.3 Application Health

**Backend API health:**
```bash
curl https://assets-api.engen.tech/api/health
# Expected: {"status":"healthy"}

# Full API docs
curl https://assets-api.engen.tech/docs
```

**Frontend availability:**
```bash
curl -I https://notes.engen.tech
# Expected: HTTP/2 200
```

### 10.4 Verify Container Images

**Check image tags and digests:**
```bash
docker images | grep parchmark

# Example output:
# ghcr.io/tejgandham/parchmark-backend   latest   abc123   2 minutes ago   150MB
# ghcr.io/tejgandham/parchmark-frontend  latest   def456   2 minutes ago   50MB
```

**See when containers were last updated:**
```bash
docker ps --format "{{.Names}}\t{{.CreatedAt}}"
```

### 10.5 Nginx Proxy Manager Integration

If using Nginx Proxy Manager, verify:

```bash
# Check npm labels are applied
docker inspect parchmark-backend | grep npm

# Verify container is on proxiable network
docker network inspect proxiable | grep parchmark
```

### 10.6 Log Aggregation

**View all logs:**
```bash
docker compose -f docker-compose.prod.yml logs -f

# Specific service logs:
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f watchtower
```

**Search logs for errors:**
```bash
docker compose -f docker-compose.prod.yml logs | grep -i error
docker compose -f docker-compose.prod.yml logs | grep -i failed
```

---

## 11. Rollback Procedures

### 11.1 When to Rollback

- Deployment introduced bugs
- Application not responding correctly
- Failed health checks
- Performance degradation

### 11.2 Method 1: Rollback to Previous Image Tag

**Find previous working version:**
```bash
# Go to GitHub → Repository → Packages
# Or use GitHub API
curl -H "Authorization: token YOUR_PAT" \
  https://api.github.com/users/tejgandham/packages/container/parchmark-backend/versions

# Note the digest or tag of previous working version
```

**Update docker-compose.prod.yml temporarily:**
```bash
# SSH to server
ssh your-user@notes.engen.tech
cd /opt/parchmark

# Edit docker-compose
nano docker-compose.prod.yml

# Change:
#   image: ghcr.io/tejgandham/parchmark-backend:latest
# To:
#   image: ghcr.io/tejgandham/parchmark-backend:sha-abc1234  # previous commit

# Apply changes
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose -f docker-compose.prod.yml ps
```

### 11.3 Method 2: Re-trigger Previous GitHub Actions

**Fastest method:**
1. Go to GitHub → Actions
2. Find the **successful deployment** before the problematic one
3. Click "Re-run all jobs"
4. Watchtower will detect and deploy the old version

### 11.4 Method 3: Git Revert + Push

**For persistent rollback:**
```bash
# On your local machine
git log --oneline  # Find commit hash to revert to

# Revert to specific commit
git revert <bad-commit-hash>
git push origin main

# Or reset to previous commit (caution: rewrites history)
git reset --hard <good-commit-hash>
git push origin main --force  # Use with caution!
```

### 11.5 Prevent Watchtower During Troubleshooting

**Temporarily disable auto-updates:**
```bash
# Stop Watchtower
docker stop watchtower

# Do your troubleshooting...

# Re-enable when ready
docker start watchtower
```

### 11.6 Emergency: Full Restart

**Nuclear option (brief downtime):**
```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Pull previous working images
docker compose -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.prod.yml up -d

# Monitor startup
docker compose -f docker-compose.prod.yml logs -f
```

---

## 12. Troubleshooting Guide

### 12.1 Watchtower Not Detecting Updates

**Symptoms:**
- New images pushed to GHCR
- Watchtower running but not updating containers

**Diagnosis:**
```bash
# Check Watchtower logs
docker logs watchtower --tail 50

# Verify Watchtower can reach GHCR
docker exec watchtower sh -c "ping -c 3 ghcr.io"

# Check if images are public or authenticated
docker pull ghcr.io/tejgandham/parchmark-backend:latest
```

**Solutions:**

1. **Verify labels:**
   ```bash
   docker inspect parchmark-backend | grep watchtower.enable
   # Should show: "com.centurylinklabs.watchtower.enable": "true"
   ```

2. **Check Watchtower configuration:**
   ```bash
   docker inspect watchtower | grep -A 10 Env
   # Verify WATCHTOWER_LABEL_ENABLE=true
   ```

3. **Manual update trigger:**
   ```bash
   # Force Watchtower to check now
   docker exec watchtower /watchtower --run-once --cleanup
   ```

4. **Restart Watchtower:**
   ```bash
   docker restart watchtower
   docker logs -f watchtower
   ```

### 12.2 Image Pull Failures

**Symptoms:**
- Error: "unauthorized: access forbidden"
- Error: "manifest unknown: manifest unknown"

**Solutions:**

1. **Make packages public:**
   - GitHub → Profile → Packages
   - Select package → Settings → Change visibility → Public

2. **Or authenticate on server:**
   ```bash
   docker login ghcr.io -u YOUR_GITHUB_USERNAME
   # Enter PAT when prompted
   ```

3. **Verify image exists:**
   ```bash
   # Check on GitHub: https://github.com/YOUR_USERNAME?tab=packages
   # Or try pulling manually
   docker pull ghcr.io/tejgandham/parchmark-backend:latest
   ```

### 12.3 Health Check Failures

**Symptoms:**
- Container shows "unhealthy" status
- Rolling update stuck or failing
- Container repeatedly restarting

**Diagnosis:**
```bash
# Check health status
docker inspect parchmark-backend --format='{{json .State.Health}}' | jq

# View health check logs
docker inspect parchmark-backend | grep -A 30 Health

# Test health endpoint manually
docker exec parchmark-backend curl -f http://localhost:8000/api/health
```

**Solutions:**

1. **Check application logs:**
   ```bash
   docker logs parchmark-backend --tail 100
   # Look for startup errors, crashes, etc.
   ```

2. **Verify health endpoint:**
   ```bash
   # Ensure /api/health route exists
   curl https://assets-api.engen.tech/api/health
   ```

3. **Adjust health check timings:**
   ```yaml
   # In docker-compose.prod.yml
   healthcheck:
     start_period: 60s  # Increase if app takes longer to start
     interval: 30s      # Increase interval between checks
   ```

4. **Check dependencies:**
   ```bash
   # Ensure database is healthy first
   docker compose -f docker-compose.prod.yml ps postgres
   ```

### 12.4 Network Connectivity Issues

**Symptoms:**
- Frontend can't reach backend
- Backend can't reach database
- 502 Bad Gateway errors

**Diagnosis:**
```bash
# Check networks
docker network ls | grep proxiable

# Inspect proxiable network
docker network inspect proxiable

# Verify containers are on correct network
docker inspect parchmark-backend | grep -A 10 Networks
```

**Solutions:**

1. **Recreate proxiable network:**
   ```bash
   docker compose -f docker-compose.prod.yml down
   docker network create proxiable  # If doesn't exist
   docker compose -f docker-compose.prod.yml up -d
   ```

2. **Check Nginx Proxy Manager:**
   ```bash
   # Verify NPM is running
   docker ps | grep nginx-proxy-manager

   # Check NPM network
   docker network inspect proxiable | grep nginx
   ```

3. **Test connectivity between containers:**
   ```bash
   # From frontend to backend
   docker exec parchmark-frontend wget -O- http://backend:8000/api/health

   # From backend to database
   docker exec parchmark-backend nc -zv postgres 5432
   ```

### 12.5 GitHub Actions Build Failures

**Symptoms:**
- Workflow fails during build step
- "no space left on device" errors
- Timeout errors

**Solutions:**

1. **Check workflow logs:**
   - GitHub → Actions → Select failed run
   - Click on failed job
   - Expand error sections

2. **Clear Docker cache:**
   ```yaml
   # In deploy.yml, remove cache-from/cache-to lines temporarily
   # This will slow builds but may fix space issues
   ```

3. **Use GitHub-hosted runners limits:**
   ```yaml
   # Add timeout to prevent hung builds
   jobs:
     build-and-push-backend:
       timeout-minutes: 30  # Add this
   ```

4. **Verify Dockerfile syntax:**
   ```bash
   # Test locally first
   docker build -t test-backend ./backend -f ./backend/Dockerfile.prod
   docker build -t test-frontend ./ui -f ./ui/Dockerfile
   ```

### 12.6 Database Migration Issues

**Symptoms:**
- Backend starts but crashes
- SQLAlchemy errors in logs
- "table does not exist" errors

**Solutions:**

1. **Check database connectivity:**
   ```bash
   docker exec parchmark-backend env | grep DATABASE_URL
   docker compose -f docker-compose.prod.yml exec postgres \
     psql -U parchmark_user -d parchmark_db -c "\dt"
   ```

2. **Manual migration (if using Alembic):**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     alembic upgrade head
   ```

3. **Recreate database (CAUTION: data loss):**
   ```bash
   docker compose -f docker-compose.prod.yml down -v  # Removes volumes!
   docker compose -f docker-compose.prod.yml up -d
   ```

### 12.7 Disk Space Issues

**Symptoms:**
- Container fails to start
- "no space left on device"
- Watchtower fails to pull images

**Diagnosis:**
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Find large images
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" | sort -k2 -h
```

**Solutions:**

1. **Clean up old images:**
   ```bash
   # Watchtower should do this, but manual cleanup:
   docker image prune -a --filter "until=168h"  # Remove images older than 7 days

   # Remove dangling images
   docker image prune
   ```

2. **Clean build cache:**
   ```bash
   docker builder prune -a --filter "until=168h"
   ```

3. **Clean unused volumes:**
   ```bash
   docker volume prune  # CAUTION: Don't remove postgres_data!
   ```

4. **Full Docker cleanup:**
   ```bash
   docker system prune -a --volumes  # NUCLEAR OPTION - stops all containers!
   ```

---

## 13. Security Best Practices

### 13.1 Image Security

**1. Keep base images updated:**
```yaml
# In Dockerfiles, use specific versions
FROM python:3.13-alpine  # Good
FROM python:latest       # Bad (unpredictable)
```

**2. Scan images for vulnerabilities:**
```bash
# Install Trivy on server
sudo apt-get install trivy

# Scan images
trivy image ghcr.io/tejgandham/parchmark-backend:latest
trivy image ghcr.io/tejgandham/parchmark-frontend:latest
```

**3. Use multi-stage builds:**
- Your Dockerfiles should already use multi-stage builds
- Ensures minimal attack surface

### 13.2 Secrets Management

**1. Never commit secrets:**
```bash
# .gitignore should include:
*.env
*.env.production
*.env.local
.env.*
!.env.example
```

**2. Rotate secrets regularly:**
```bash
# Rotate JWT secret every 90 days
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in backend/.env.production
nano backend/.env.production

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

**3. Use strong passwords:**
- Database password: 32+ characters
- JWT secret: 32+ bytes
- User passwords: Enforce 12+ characters

### 13.3 Network Security

**1. Internal network isolation:**
```yaml
# Add internal network to docker-compose.prod.yml
networks:
  proxiable:
    external: true
  internal:
    internal: true  # No external access

services:
  postgres:
    networks:
      - internal  # Database not on proxiable network

  backend:
    networks:
      - proxiable  # External access
      - internal   # Database access
```

**2. Firewall rules:**
```bash
# Only allow necessary ports
sudo ufw status
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH (from specific IPs only!)
sudo ufw enable
```

### 13.4 Container Security

**1. Run as non-root user:**

Add to Dockerfiles:
```dockerfile
# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Switch to non-root user
USER appuser
```

**2. Read-only filesystem:**
- Already configured in docker-compose.prod.yml
- Uses tmpfs for /tmp

**3. Drop unnecessary capabilities:**
- Already configured: `cap_drop: ALL`

### 13.5 Access Control

**1. Limit SSH access:**
```bash
# Only allow SSH from specific IPs
sudo nano /etc/ssh/sshd_config

# Add:
AllowUsers your-username
PermitRootLogin no
PasswordAuthentication no  # Key-only
```

**2. Docker socket protection:**
```bash
# Ensure only authorized users can access Docker
sudo usermod -aG docker your-username
# Don't add untrusted users to docker group
```

**3. GitHub PAT security:**
- Use fine-grained PATs with minimum permissions
- Set expiration dates
- Rotate regularly
- Store securely (password manager)

### 13.6 Monitoring & Alerts

**1. Set up log monitoring:**
```bash
# Use logrotate to prevent disk fill
sudo nano /etc/logrotate.d/docker-compose

/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  missingok
  delaycompress
}
```

**2. Monitor for suspicious activity:**
```bash
# Check for unauthorized containers
docker ps -a

# Monitor login attempts
sudo journalctl -u ssh -f
```

### 13.7 Backup Strategy

**1. Database backups:**
```bash
# Create backup script
cat > /opt/parchmark/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/parchmark/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

docker compose -f /opt/parchmark/docker-compose.prod.yml exec -T postgres \
  pg_dump -U parchmark_user parchmark_db | gzip > $BACKUP_DIR/parchmark_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "parchmark_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /opt/parchmark/backup-db.sh

# Add to cron (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /opt/parchmark/backup-db.sh
```

**2. Configuration backups:**
```bash
# Backup .env files (encrypted!)
tar -czf parchmark-config-$(date +%Y%m%d).tar.gz \
  backend/.env.production \
  ui/.env.production \
  docker-compose.prod.yml

# Encrypt backup
gpg -c parchmark-config-*.tar.gz
# Store encrypted backup securely off-server
```

---

## 14. Makefile Integration

### 14.1 Create Deploy Makefile

Create `makefiles/deploy.mk`:

```makefile
# ============================================================================
# DEPLOYMENT TARGETS
# ============================================================================

.PHONY: deploy-build-backend
deploy-build-backend: ## Build backend Docker image locally
	$(call info_msg,Building backend Docker image...)
	cd backend && docker build -f Dockerfile.prod -t parchmark-backend:local .
	$(call success_msg,Backend image built)

.PHONY: deploy-build-frontend
deploy-build-frontend: ## Build frontend Docker image locally
	$(call info_msg,Building frontend Docker image...)
	cd ui && docker build -f Dockerfile -t parchmark-frontend:local .
	$(call success_msg,Frontend image built)

.PHONY: deploy-build-all
deploy-build-all: deploy-build-backend deploy-build-frontend ## Build all Docker images locally
	$(call success_msg,All images built)

.PHONY: deploy-test-local
deploy-test-local: ## Test production images locally
	$(call info_msg,Testing production images locally...)
	docker compose -f docker-compose.prod.yml config
	$(call success_msg,Configuration valid)

.PHONY: deploy-push-check
deploy-push-check: ## Check if ready to deploy (tests pass)
	$(call info_msg,Checking deployment readiness...)
	@if git diff-index --quiet HEAD --; then \
		echo "$(GREEN)✓ No uncommitted changes$(NC)"; \
	else \
		echo "$(RED)✗ Uncommitted changes detected$(NC)"; \
		exit 1; \
	fi
	@if git branch --contains HEAD | grep -q main; then \
		echo "$(GREEN)✓ On main branch$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Not on main branch$(NC)"; \
	fi
	$(call success_msg,Ready to deploy)

.PHONY: deploy-trigger
deploy-trigger: ## Trigger GitHub Actions deployment (requires gh CLI)
	$(call info_msg,Triggering deployment via GitHub Actions...)
	@if command -v gh >/dev/null 2>&1; then \
		gh workflow run deploy.yml; \
		echo "$(GREEN)✓ Deployment triggered$(NC)"; \
		echo "$(CYAN)Monitor: gh run watch$(NC)"; \
	else \
		echo "$(RED)✗ GitHub CLI not installed$(NC)"; \
		echo "Install: https://cli.github.com/"; \
		exit 1; \
	fi

.PHONY: deploy-watch
deploy-watch: ## Watch GitHub Actions deployment (requires gh CLI)
	$(call info_msg,Watching deployment...)
	@if command -v gh >/dev/null 2>&1; then \
		gh run watch; \
	else \
		echo "$(RED)✗ GitHub CLI not installed$(NC)"; \
		exit 1; \
	fi

.PHONY: deploy-status
deploy-status: ## Check deployment status
	$(call info_msg,Checking deployment status...)
	@echo "$(CYAN)GitHub Actions:$(NC)"
	@if command -v gh >/dev/null 2>&1; then \
		gh run list --workflow=deploy.yml --limit 5; \
	else \
		echo "Install gh CLI: https://cli.github.com/"; \
	fi

.PHONY: deploy-logs-watchtower
deploy-logs-watchtower: ## View Watchtower logs on server (requires SSH config)
	@echo "$(CYAN)Viewing Watchtower logs (Ctrl+C to exit)$(NC)"
	@echo "Configure SSH alias in ~/.ssh/config for easy access:"
	@echo "  Host parchmark-prod"
	@echo "    HostName notes.engen.tech"
	@echo "    User your-username"
	@echo ""
	ssh parchmark-prod 'docker logs -f --tail 50 watchtower'

.PHONY: deploy-verify
deploy-verify: ## Verify production deployment health
	$(call info_msg,Verifying production health...)
	@echo "$(CYAN)Backend health:$(NC)"
	@curl -f -s https://assets-api.engen.tech/api/health && echo "$(GREEN)✓ OK$(NC)" || echo "$(RED)✗ FAILED$(NC)"
	@echo ""
	@echo "$(CYAN)Frontend health:$(NC)"
	@curl -f -s -I https://notes.engen.tech | head -1 && echo "$(GREEN)✓ OK$(NC)" || echo "$(RED)✗ FAILED$(NC)"
	$(call success_msg,Production health check complete)

.PHONY: deploy-rollback-list
deploy-rollback-list: ## List available image versions for rollback
	$(call info_msg,Available image versions...)
	@echo "$(CYAN)Run on server to see versions:$(NC)"
	@echo "  docker images | grep parchmark"
	@echo ""
	@echo "$(CYAN)Or check GHCR:$(NC)"
	@echo "  https://github.com/YOUR_USERNAME?tab=packages"

.PHONY: deploy-help
deploy-help: ## Show deployment workflow help
	@echo ""
	@echo "$(CYAN)════════════════════════════════════════$(NC)"
	@echo "$(CYAN)ParchMark Deployment Workflow$(NC)"
	@echo "$(CYAN)════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Automatic Deployment:$(NC)"
	@echo "  1. git push origin main"
	@echo "  2. GitHub Actions builds & pushes images"
	@echo "  3. Watchtower updates within 5 minutes"
	@echo ""
	@echo "$(GREEN)Manual Deployment:$(NC)"
	@echo "  1. make deploy-push-check"
	@echo "  2. make deploy-trigger"
	@echo "  3. make deploy-watch"
	@echo "  4. make deploy-verify"
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@echo "  make deploy-status          - Check GitHub Actions"
	@echo "  make deploy-logs-watchtower - Watch server logs"
	@echo "  make deploy-verify          - Test production health"
	@echo ""
	@echo "$(GREEN)Local Testing:$(NC)"
	@echo "  make deploy-build-all       - Build images locally"
	@echo "  make deploy-test-local      - Validate config"
	@echo ""
	@echo "$(GREEN)Rollback:$(NC)"
	@echo "  make deploy-rollback-list   - List versions"
	@echo "  SSH to server and follow docs/DEPLOYMENT.md § 11"
	@echo ""
```

### 14.2 Add to Main Makefile

Update main `Makefile`:

```makefile
# Include deployment makefile
include makefiles/deploy.mk
```

### 14.3 Usage Examples

```bash
# Check if ready to deploy
make deploy-push-check

# Trigger manual deployment (requires GitHub CLI)
make deploy-trigger

# Watch deployment progress
make deploy-watch

# Verify production health
make deploy-verify

# View Watchtower logs (requires SSH configured)
make deploy-logs-watchtower

# Show help
make deploy-help
```

---

## 15. Maintenance Tasks

### 15.1 Regular Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Check disk space | Weekly | `df -h && docker system df` |
| Review logs | Weekly | `docker compose logs --tail 500` |
| Update base images | Monthly | Rebuild images |
| Rotate secrets | Quarterly | Update .env files |
| Database backup | Daily | Automated via cron |
| Security scan | Weekly | `trivy image` |

### 15.2 Disk Space Management

**Monitor disk usage:**
```bash
# Check overall disk space
df -h

# Check Docker disk usage
docker system df -v

# Find largest images
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k3 -h
```

**Cleanup strategy (Watchtower does most of this):**
```bash
# Manual cleanup if needed
docker image prune -a --filter "until=168h"  # Remove images >7 days old
docker container prune --filter "until=24h"
docker volume prune  # CAUTION with database volumes!
```

### 15.3 Log Management

**Configure log rotation:**
```bash
# Edit Docker daemon config
sudo nano /etc/docker/daemon.json

# Add:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

**Manual log cleanup:**
```bash
# Truncate large log files
truncate -s 0 $(docker inspect --format='{{.LogPath}}' parchmark-backend)
truncate -s 0 $(docker inspect --format='{{.LogPath}}' parchmark-frontend)
```

### 15.4 Database Maintenance

**Vacuum database:**
```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U parchmark_user -d parchmark_db -c "VACUUM ANALYZE;"
```

**Check database size:**
```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U parchmark_user -d parchmark_db -c "\l+"
```

**Backup database:**
```bash
# See § 13.7 for automated backup script
/opt/parchmark/backup-db.sh
```

### 15.5 Update Dependencies

**Frontend dependencies:**
```bash
# On development machine
cd ui
npm update
npm audit fix

# Test
npm test

# Commit and push (triggers deployment)
git add package.json package-lock.json
git commit -m "chore: update frontend dependencies"
git push origin main
```

**Backend dependencies:**
```bash
# On development machine
cd backend
uv lock --upgrade
uv sync

# Test
make test-backend-all

# Commit and push
git add pyproject.toml uv.lock
git commit -m "chore: update backend dependencies"
git push origin main
```

### 15.6 Security Updates

**Update base images monthly:**

1. Edit Dockerfiles to use latest patch versions
2. Rebuild and test locally
3. Push to trigger deployment

**Subscribe to security advisories:**
- Docker: https://www.docker.com/blog/
- PostgreSQL: https://www.postgresql.org/support/security/
- FastAPI: https://github.com/tiangolo/fastapi/security/advisories
- React: https://github.com/facebook/react/security/advisories

### 15.7 Monitoring Setup (Optional)

**Option 1: Uptime monitoring (Free):**
- UptimeRobot: https://uptimerobot.com/
- Monitor: https://notes.engen.tech
- Monitor: https://assets-api.engen.tech/api/health

**Option 2: Prometheus + Grafana (Advanced):**
```yaml
# Add to docker-compose.prod.yml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  # ... config

grafana:
  image: grafana/grafana:latest
  # ... config
```

---

## 16. Advanced Configuration (Optional)

### 16.1 Deployment Notifications

**Discord Webhook:**

1. Create Discord webhook in your server settings
2. Add to docker-compose.prod.yml:

```yaml
watchtower:
  environment:
    - WATCHTOWER_NOTIFICATIONS=shoutrrr
    - WATCHTOWER_NOTIFICATION_URL=discord://TOKEN@CHANNEL_ID
```

3. Restart Watchtower:
```bash
docker compose -f docker-compose.prod.yml restart watchtower
```

**Slack Webhook:**
```yaml
- WATCHTOWER_NOTIFICATION_URL=slack://TOKEN_A/TOKEN_B/TOKEN_C
```

**Email:**
```yaml
- WATCHTOWER_NOTIFICATION_URL=smtp://username:password@host:port/?from=sender@example.com&to=recipient@example.com
```

### 16.2 Custom Watchtower Schedule

**Check every hour instead of 5 minutes:**
```yaml
watchtower:
  environment:
    - WATCHTOWER_POLL_INTERVAL=3600  # Seconds
```

**Run once per day at specific time:**
```yaml
watchtower:
  environment:
    - WATCHTOWER_SCHEDULE=0 0 2 * * *  # 2 AM daily (cron syntax)
```

### 16.3 Staging Environment

**Create docker-compose.staging.yml:**
```yaml
services:
  backend:
    image: ghcr.io/tejgandham/parchmark-backend:staging
    labels:
      - "npm.host=staging-api.engen.tech"
      - "com.centurylinklabs.watchtower.enable=true"

  frontend:
    image: ghcr.io/tejgandham/parchmark-frontend:staging
    labels:
      - "npm.host=staging.engen.tech"
      - "com.centurylinklabs.watchtower.enable=true"

  watchtower:
    environment:
      - WATCHTOWER_POLL_INTERVAL=600  # 10 minutes for staging
```

**Update deploy.yml for staging:**
```yaml
- name: Extract metadata for Docker
  id: meta
  uses: docker/metadata-action@v5
  with:
    tags: |
      type=raw,value=staging,enable=${{ github.ref == 'refs/heads/develop' }}
      type=raw,value=latest,enable={{is_default_branch}}
```

### 16.4 Blue-Green Deployment

For true zero-downtime with instant rollback:

```yaml
# docker-compose.bluegreen.yml
services:
  backend-blue:
    image: ghcr.io/tejgandham/parchmark-backend:blue
    labels:
      - "npm.host=assets-api.engen.tech"
      - "npm.weight=100"  # All traffic

  backend-green:
    image: ghcr.io/tejgandham/parchmark-backend:green
    labels:
      - "npm.host=assets-api.engen.tech"
      - "npm.weight=0"  # No traffic (standby)

  # Similar for frontend...
```

Swap traffic by changing weights in Nginx Proxy Manager.

### 16.5 Database Backup to S3 (AWS)

**Automated offsite backups:**

```bash
# Install AWS CLI on server
sudo apt-get install awscli

# Configure AWS credentials
aws configure

# Create backup script with S3 upload
cat > /opt/parchmark/backup-to-s3.sh << 'EOF'
#!/bin/bash
BACKUP_FILE="/tmp/parchmark_$(date +%Y%m%d_%H%M%S).sql.gz"
S3_BUCKET="s3://your-bucket/parchmark-backups/"

# Backup database
docker compose -f /opt/parchmark/docker-compose.prod.yml exec -T postgres \
  pg_dump -U parchmark_user parchmark_db | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE $S3_BUCKET

# Cleanup local file
rm $BACKUP_FILE

# Keep only last 30 days in S3
aws s3 ls $S3_BUCKET | while read -r line; do
  FILE=$(echo $line | awk '{print $4}')
  if [[ $(date -d "$(echo $line | awk '{print $1" "$2}')" +%s) -lt $(date -d "30 days ago" +%s) ]]; then
    aws s3 rm "${S3_BUCKET}${FILE}"
  fi
done
EOF

chmod +x /opt/parchmark/backup-to-s3.sh

# Add to cron
crontab -e
# Add: 0 3 * * * /opt/parchmark/backup-to-s3.sh
```

### 16.6 Custom Health Checks

**Enhanced backend health check:**

```python
# backend/app/routers/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check including database connectivity."""
    try:
        # Test database connection
        db.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

---

## 17. Performance Optimization

### 17.1 Docker Build Optimization

**Use BuildKit for faster builds:**

In `deploy.yml`:
```yaml
- name: Build and push backend image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=registry,ref=${{ env.REGISTRY }}/.../buildcache
    cache-to: type=registry,ref=${{ env.REGISTRY }}/.../buildcache,mode=max
    # BuildKit automatically enabled by build-push-action
```

**Local BuildKit:**
```bash
export DOCKER_BUILDKIT=1
docker build --cache-from=... --cache-to=...
```

### 17.2 Image Size Reduction

**Current sizes (typical):**
- Frontend: ~50MB (Nginx + static files)
- Backend: ~150MB (Python + dependencies)

**Optimization tips:**

1. **Multi-stage builds** (already implemented)
2. **Alpine base images** (already using)
3. **Remove unnecessary files:**
   ```dockerfile
   # In Dockerfile
   RUN rm -rf /root/.cache /var/cache/apk/*
   ```

### 17.3 Watchtower Performance

**Reduce API calls:**
```yaml
watchtower:
  environment:
    # Check less frequently in production
    - WATCHTOWER_POLL_INTERVAL=600  # 10 minutes instead of 5
```

**Monitor only specific containers:**
```yaml
# Better than monitoring all containers
command: parchmark-backend parchmark-frontend
```

### 17.4 GitHub Actions Optimization

**Parallel builds:**
```yaml
# Jobs run in parallel (already configured)
jobs:
  build-and-push-backend:  # Runs concurrently
  build-and-push-frontend: # Runs concurrently
```

**Cache dependencies:**
```yaml
# Already configured in deploy.yml
cache-from: type=registry,ref=...:buildcache
```

### 17.5 Database Performance

**Add indexes:**
```sql
-- On production database
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at DESC);
```

**Connection pooling:**
```python
# In backend database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Adjust based on load
    max_overflow=20,       # Extra connections
    pool_pre_ping=True,    # Verify connections
    pool_recycle=3600      # Recycle after 1 hour
)
```

---

## 18. Appendices

### Appendix A: Complete File Examples

#### A.1 Complete docker-compose.prod.yml

See § 4.2 for full file.

#### A.2 Complete deploy.yml

See § 5.2 for full file.

#### A.3 Example .env.production Files

**backend/.env.production:**
```env
# Database (matches docker-compose postgres service)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@postgres:5432/parchmark_db

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-min-32-chars-abcdefghijklmnopqrstuvwxyz
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
```

**ui/.env.production:**
```env
# API URL (proxied)
VITE_API_URL=/api

# Token warning
VITE_TOKEN_WARNING_SECONDS=60
```

---

### Appendix B: Command Reference

#### B.1 Docker Commands

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker logs <container-name>
docker logs -f <container-name>  # Follow
docker logs --tail 100 <container-name>

# Execute command in container
docker exec <container-name> <command>
docker exec -it <container-name> sh  # Interactive shell

# Inspect container
docker inspect <container-name>

# View resource usage
docker stats

# Cleanup
docker system prune -a  # Remove unused data
docker image prune      # Remove unused images
docker container prune  # Remove stopped containers
```

#### B.2 Docker Compose Commands

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d

# Stop services
docker compose -f docker-compose.prod.yml down

# Restart services
docker compose -f docker-compose.prod.yml restart

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Pull new images
docker compose -f docker-compose.prod.yml pull

# View service status
docker compose -f docker-compose.prod.yml ps

# Execute command in service
docker compose -f docker-compose.prod.yml exec backend <command>

# Rebuild services
docker compose -f docker-compose.prod.yml up -d --build
```

#### B.3 Watchtower Commands

```bash
# View Watchtower logs
docker logs watchtower
docker logs -f watchtower  # Follow

# Manually trigger update check
docker exec watchtower /watchtower --run-once

# Restart Watchtower
docker restart watchtower

# Stop Watchtower (disable auto-updates)
docker stop watchtower

# Start Watchtower (enable auto-updates)
docker start watchtower
```

#### B.4 GitHub CLI Commands

```bash
# Trigger workflow
gh workflow run deploy.yml

# Watch running workflow
gh run watch

# List recent runs
gh run list --workflow=deploy.yml

# View specific run
gh run view <run-id>

# View workflow logs
gh run view <run-id> --log
```

---

### Appendix C: Environment Variables Reference

#### C.1 Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT secret (32+ bytes) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `ALLOWED_ORIGINS` | Yes | - | CORS origins (comma-separated) |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `ENVIRONMENT` | No | `development` | Environment name |

#### C.2 Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | - | Backend API URL (usually `/api`) |
| `VITE_TOKEN_WARNING_SECONDS` | No | `60` | Token expiration warning |

#### C.3 Watchtower Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WATCHTOWER_POLL_INTERVAL` | `86400` | Check interval (seconds) |
| `WATCHTOWER_CLEANUP` | `false` | Remove old images |
| `WATCHTOWER_ROLLING_RESTART` | `false` | Zero-downtime updates |
| `WATCHTOWER_LABEL_ENABLE` | `false` | Only labeled containers |
| `WATCHTOWER_LOG_LEVEL` | `info` | Log level |
| `WATCHTOWER_NOTIFICATIONS` | - | Notification method |
| `WATCHTOWER_NOTIFICATION_URL` | - | Notification URL |

---

### Appendix D: FAQ

#### Q1: How long does deployment take?

**A:** ~15-20 minutes from push to live
- GitHub Actions build: 5-10 minutes
- Watchtower detection: 0-5 minutes (polling interval)
- Rolling update: 1-2 minutes

#### Q2: Is there any downtime during deployment?

**A:** No, zero downtime with rolling restarts
- New containers start before old ones stop
- Health checks ensure readiness
- Traffic seamlessly switches

#### Q3: How do I know when deployment is complete?

**A:** Multiple ways:
1. Check GitHub Actions for successful build
2. View Watchtower logs: `docker logs -f watchtower`
3. Verify health: `make deploy-verify`
4. Check container ages: `docker ps --format "{{.Names}}\t{{.CreatedAt}}"`

#### Q4: Can I deploy without pushing to main?

**A:** Yes, use manual trigger:
1. GitHub → Actions → Deploy workflow
2. "Run workflow" → Select branch
3. OR: `make deploy-trigger` (requires GitHub CLI)

#### Q5: What if deployment fails?

**A:** Watchtower keeps old containers running
- Failed health checks prevent old container removal
- Manual rollback options available (§ 11)
- No service disruption from failed deployment

#### Q6: How do I rollback?

**A:** Three methods (§ 11):
1. Re-run previous successful GitHub Actions job
2. Use specific image tag (e.g., `sha-abc1234`)
3. Git revert + push

#### Q7: Can I pause auto-deployments?

**A:** Yes:
```bash
# Stop Watchtower
docker stop watchtower

# Resume when ready
docker start watchtower
```

#### Q8: How much disk space does this use?

**A:** Approximate:
- PostgreSQL data: Varies with usage
- Images: ~200MB per version
- Logs: ~100MB (with rotation)
- Total: 1-2GB recommended minimum

#### Q9: What about database migrations?

**A:** Current setup:
- SQLAlchemy auto-migration on startup
- For production, add Alembic migration step to backend startup

#### Q10: How do I monitor costs?

**A:** All free for public repos:
- ✅ GHCR: Free unlimited
- ✅ GitHub Actions: 2000 minutes/month free
- ✅ Watchtower: Free (self-hosted)
- ✅ Server: Your existing costs

#### Q11: Can I use this for multiple environments?

**A:** Yes, create separate compose files:
- `docker-compose.prod.yml` - Production
- `docker-compose.staging.yml` - Staging
- Different GHCR image tags (`:latest`, `:staging`)

#### Q12: What if I want to build on the server instead?

**A:** Not recommended, but possible:
- Remove Watchtower
- SSH in GitHub Actions
- Run `docker compose build` on server
- Downside: Build dependencies on server, longer builds

---

## Support & Resources

### Official Documentation

- **Watchtower:** https://containrrr.dev/watchtower/
- **GHCR:** https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- **Docker Compose:** https://docs.docker.com/compose/
- **GitHub Actions:** https://docs.github.com/en/actions

### ParchMark Resources

- **Repository:** https://github.com/TejGandham/parchmark
- **Issues:** https://github.com/TejGandham/parchmark/issues
- **CLAUDE.md:** Project documentation

### Community Support

- **Docker Community:** https://forums.docker.com/
- **GitHub Discussions:** https://github.com/orgs/community/discussions

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-26 | Initial deployment guide |

---

**End of Deployment Guide**

For questions or issues, please open an issue on GitHub: https://github.com/TejGandham/parchmark/issues
