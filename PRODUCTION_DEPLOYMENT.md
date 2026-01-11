# ParchMark Production Deployment Guide

This guide provides comprehensive instructions for deploying and maintaining ParchMark in production.

## Overview

**Frontend URL:** `https://notes.engen.tech`
**Backend API URL:** `https://assets-api.engen.tech`
**API Docs:** `https://assets-api.engen.tech/docs`

**Architecture:**
- Frontend: React app served via Nginx container (proxies `/api/*` to backend)
- Backend: FastAPI application with PostgreSQL database
- Database: PostgreSQL 17.2 running in Docker container
- Nginx Proxy Manager: SSL termination and reverse proxy
- Docker Network: `proxiable` (shared with NPM)
- Images: Pre-built and stored in GitHub Container Registry (GHCR)

## Deployment Process

### How Deployments Work

1. **Push to `main` branch** triggers GitHub Actions workflow
2. **GitHub Actions** runs tests, builds Docker images, and pushes to GHCR
3. **Manual deployment** via SSH using the update script

### Quick Deploy

```bash
ssh deploy@<server-ip>
cd /home/deploy/parchmark
git pull origin main        # Get latest config (if changed)
./deploy/update.sh          # Pull images and restart services
```

The update script handles: GHCR authentication (optional for public images), pulling latest images, restarting containers, health checks, and cleanup.

---

## Prerequisites

### Server Requirements
- Docker & Docker Compose v2.20+
- `proxiable` Docker network (shared with Nginx Proxy Manager)
- SSH access to production server

### Required Files on Server

```
/home/deploy/parchmark/
├── docker-compose.prod.yml      # Production compose configuration
├── .env.db                      # PostgreSQL credentials (gitignored)
├── .env.deploy                  # GHCR credentials (optional for public images)
├── backend/.env.production      # Backend environment variables
├── ui/.env.production           # Frontend environment variables
├── ui/nginx.http.conf           # Nginx config with API proxy
└── deploy/
    └── update.sh                # Deployment script
```

---

## Environment Configuration

### Database Environment (`.env.db`)

```env
POSTGRES_USER=parchmark_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=parchmark_db
```

### Backend Environment (`backend/.env.production`)

```env
# Database - use container name, NOT localhost
DATABASE_URL=postgresql://parchmark_user:<password>@parchmark-postgres-prod:5432/parchmark_db

# JWT Configuration
SECRET_KEY=<generate-with: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
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

### Frontend Environment (`ui/.env.production`)

```env
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60
```

---

## Deployment Steps

### Option 1: Using the Update Script (Recommended)

```bash
ssh deploy@<server-ip>
cd /home/deploy/parchmark
git pull origin main        # Get latest config changes
./deploy/update.sh          # Automated deployment
```

The script will:
- Pull latest Docker images from GHCR
- Restart containers with new images
- Wait for health checks to pass
- Clean up old images

### Option 2: Manual Deployment

```bash
ssh deploy@<server-ip>
cd /home/deploy/parchmark

# Pull latest code (for compose file changes)
git pull origin main

# Pull latest Docker images
docker compose -f docker-compose.prod.yml pull postgres backend frontend

# Restart services
docker compose -f docker-compose.prod.yml up -d postgres backend frontend

# Verify deployment
docker ps --filter "name=parchmark"
curl -sf http://127.0.0.1:8000/api/health
```

### Running Database Migrations

Migrations are NOT automatically run by the update script (alembic is not configured in the container). Run migrations manually when needed:

```bash
docker run --rm --network proxiable \
  -v $(pwd)/backend:/app -w /app \
  -e DATABASE_URL=postgresql://parchmark_user:<password>@parchmark-postgres-prod:5432/parchmark_db \
  astral/uv:python3.13-bookworm \
  uv run alembic upgrade head
```

### Verify Deployment

```bash
# Check containers are running
docker ps --filter "name=parchmark"

# Test backend health
curl -sf http://127.0.0.1:8000/api/health

# Check logs for errors
docker logs parchmark-backend --tail 50
docker logs parchmark-frontend --tail 50
```

---

## Nginx Configuration

The frontend container includes an nginx config that proxies `/api/*` requests to the backend. This is mounted as a volume in `docker-compose.prod.yml`:

### `ui/nginx.http.conf` (key section)

```nginx
location /api/ {
    proxy_pass http://parchmark-backend:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### `docker-compose.prod.yml` (frontend volume mount)

```yaml
frontend:
  volumes:
    - ./ui/nginx.http.conf:/etc/nginx/conf.d/nginx.http.conf:ro
```

**Why this matters:** The frontend is built with `VITE_API_URL=/api`, so all API calls go to `https://notes.engen.tech/api/*`. The nginx config proxies these to the backend container.

---

## Nginx Proxy Manager Configuration

### Frontend (`notes.engen.tech`)

| Setting | Value |
|---------|-------|
| Scheme | http |
| Forward Hostname | parchmark-frontend |
| Forward Port | 80 |
| SSL | Force SSL, HTTP/2, HSTS |

### Backend (`assets-api.engen.tech`)

| Setting | Value |
|---------|-------|
| Scheme | http |
| Forward Hostname | parchmark-backend |
| Forward Port | 8000 |
| SSL | Force SSL, HTTP/2, HSTS |

---

## User Management

### Create a User

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py create <username> '<password>'
```

### Update Password

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py update-password <username> '<new-password>'
```

### Delete User

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py delete <username>
```

### List Users

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/manage_users.py list
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs parchmark-backend
docker logs parchmark-frontend

# Check container status
docker ps -a --filter "name=parchmark"

# Restart all services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Database Connection Issues

```bash
# Check database is running and healthy
docker ps --filter "name=parchmark-postgres-prod"

# Test connection from backend container
docker exec parchmark-backend env | grep DATABASE_URL

# Verify database connectivity
docker exec parchmark-postgres-prod pg_isready -U parchmark_user -d parchmark_db
```

### 405 Method Not Allowed on Login

This usually means the API proxy isn't working:

1. Check `ui/nginx.http.conf` has the `/api/` location block
2. Verify the volume mount in `docker-compose.prod.yml`
3. Restart the frontend container: `docker restart parchmark-frontend`

### Migrations Fail

```bash
# Check current migration status
docker run --rm --network proxiable \
  -v $(pwd)/backend:/app -w /app \
  -e DATABASE_URL=postgresql://parchmark_user:<password>@parchmark-postgres-prod:5432/parchmark_db \
  astral/uv:python3.13-bookworm \
  uv run alembic current

# Show migration history
docker run --rm --network proxiable \
  -v $(pwd)/backend:/app -w /app \
  -e DATABASE_URL=postgresql://parchmark_user:<password>@parchmark-postgres-prod:5432/parchmark_db \
  astral/uv:python3.13-bookworm \
  uv run alembic history
```

### Network Issues

```bash
# Verify proxiable network exists
docker network ls | grep proxiable

# Check containers are on the network
docker network inspect proxiable | grep -A 5 parchmark

# Recreate network if needed
docker network create proxiable
```

---

## Rollback

To rollback to a previous version:

### 1. Find Available Image Tags

Visit: https://github.com/TejGandham?tab=packages

Or use gh CLI:
```bash
gh api user/packages/container/parchmark-backend/versions --jq '.[].metadata.container.tags[]'
```

### 2. Update Image Tags

Edit `docker-compose.prod.yml`:
```yaml
backend:
  image: ghcr.io/tejgandham/parchmark-backend:sha-<commit-sha>
frontend:
  image: ghcr.io/tejgandham/parchmark-frontend:sha-<commit-sha>
```

### 3. Pull and Restart

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

### 4. Revert docker-compose.prod.yml (optional)

After rollback, revert to `:latest` tags and commit:
```bash
git checkout docker-compose.prod.yml
```

---

## Backups

### Database Backup

```bash
# Create backup
docker exec parchmark-postgres-prod pg_dump -U parchmark_user parchmark_db | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore backup
gunzip -c backup-YYYYMMDD.sql.gz | docker exec -i parchmark-postgres-prod psql -U parchmark_user parchmark_db
```

### Configuration Backup

```bash
# Backup environment files (store securely!)
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  .env.db \
  backend/.env.production \
  ui/.env.production
```

---

## Maintenance

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail 100
```

### Check Disk Usage

```bash
# Docker disk usage
docker system df

# Clean up old images (keep last 7 days)
docker image prune -a --filter "until=168h"
```

### Restart Services

```bash
# Graceful restart
docker compose -f docker-compose.prod.yml restart backend frontend

# Full restart (brief downtime)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## Security Notes

- **Never commit** `.env.db`, `backend/.env.production`, or `ui/.env.production`
- **Rotate secrets** every 90 days (JWT SECRET_KEY, database password)
- **Keep images updated** - rebuild and deploy regularly
- **Monitor logs** for suspicious activity
- Database is isolated to Docker network (not exposed externally)
- SSL/HSTS enforced via Nginx Proxy Manager

---

## Quick Reference

### Container Names
| Service | Container Name |
|---------|---------------|
| Frontend | parchmark-frontend |
| Backend | parchmark-backend |
| Database | parchmark-postgres-prod |

### Ports (internal)
| Service | Port |
|---------|------|
| Frontend (nginx) | 80 |
| Backend (uvicorn) | 8000 |
| Database (postgres) | 5432 |

### Health Endpoints
| Service | Endpoint |
|---------|----------|
| Backend | `/api/health` |
| Frontend | `/` |

### GHCR Images
| Image | URL |
|-------|-----|
| Backend | `ghcr.io/tejgandham/parchmark-backend:latest` |
| Frontend | `ghcr.io/tejgandham/parchmark-frontend:latest` |
