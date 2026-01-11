# ParchMark Server Setup Guide

This guide covers setting up ParchMark on a production server with manual deployment triggers.

## Architecture Overview

```
GitHub Actions                          Production Server
     │                                        │
     │ push to main                           │
     ▼                                        │
┌─────────────────┐                           │
│  Run Tests      │                           │
│  Build Images   │                           │
│  Push to GHCR   │                           │
└─────────────────┘                           │
     │                                        │
     │ Images available                       │
     ▼                                        │
                                              │
     (When ready to deploy)                   │
     SSH to server ──────────────────────────►│
                                              │
                                    ┌─────────▼─────────┐
                                    │ ./deploy/update.sh│
                                    │                   │
                                    │ - Pull images     │
                                    │ - Restart services│
                                    │ - Run migrations  │
                                    └───────────────────┘
```

## Prerequisites

- Docker Engine 24.0+
- Docker Compose v2
- Git
- Access to GHCR (GitHub Container Registry)

## Initial Setup

### 1. Clone the Repository

```bash
cd /home/deploy
git clone https://github.com/TejGandham/parchmark.git
cd parchmark
```

### 2. Create the External Network

The application uses a shared network for Nginx Proxy Manager integration:

```bash
docker network create proxiable
```

### 3. Create Environment Files

#### Database credentials (`.env.db`)

```bash
cat > .env.db << 'EOF'
POSTGRES_USER=parchmark_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=parchmark_db
EOF
chmod 600 .env.db
```

#### Backend configuration (`backend/.env.production`)

```bash
cat > backend/.env.production << 'EOF'
# Database
DATABASE_URL=postgresql://parchmark_user:your_secure_password_here@postgres:5432/parchmark_db

# Security
SECRET_KEY=your_very_long_random_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=https://notes.engen.tech

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
EOF
chmod 600 backend/.env.production
```

#### Frontend configuration (`ui/.env.production`)

```bash
cat > ui/.env.production << 'EOF'
VITE_API_URL=/api
EOF
```

#### Deploy credentials (`.env.deploy`)

Create a GitHub Personal Access Token with `read:packages` scope, then:

```bash
cat > .env.deploy << 'EOF'
GHCR_USER=tejgandham
GHCR_TOKEN=ghp_your_token_here
EOF
chmod 600 .env.deploy
```

### 4. Make Scripts Executable

```bash
chmod +x deploy/update.sh
```

### 5. Initial Deployment

Run the update script to pull images and start services:

```bash
./deploy/update.sh
```

## Updating ParchMark

When you want to deploy new changes:

```bash
# SSH into the server
ssh deploy@your-server

# Navigate to the project
cd /home/deploy/parchmark

# Pull latest configuration changes (if any)
git pull origin main

# Run the update script
./deploy/update.sh
```

The update script will:
1. Authenticate with GHCR
2. Pull the latest Docker images
3. Recreate containers with new images
4. Wait for health checks to pass
5. Run database migrations
6. Clean up old images

## Viewing Logs

### Update Script Logs

```bash
# View all update logs
cat /home/deploy/parchmark/logs/update.log

# Follow logs in real-time
tail -f /home/deploy/parchmark/logs/update.log

# View last 50 lines
tail -n 50 /home/deploy/parchmark/logs/update.log
```

### Container Logs

```bash
cd /home/deploy/parchmark

# All services
docker compose -f docker-compose.prod.yml logs

# Follow logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs postgres
```

## Rollback

If an update causes issues, you can rollback to a previous image version.

### List Available Images

```bash
# View local images with SHA tags
docker images | grep parchmark

# Example output:
# ghcr.io/tejgandham/parchmark-backend   latest      abc123   2 hours ago
# ghcr.io/tejgandham/parchmark-backend   sha-def456  def456   1 day ago
```

### Rollback to a Specific Version

```bash
cd /home/deploy/parchmark

# Edit docker-compose.prod.yml to use a specific SHA tag
# Change: image: ghcr.io/tejgandham/parchmark-backend:latest
# To:     image: ghcr.io/tejgandham/parchmark-backend:sha-def456

# Or use environment variable override:
BACKEND_TAG=sha-def456 docker compose -f docker-compose.prod.yml up -d backend
```

### Rollback Database Migration

If a migration needs to be reverted:

```bash
# View migration history
docker compose -f docker-compose.prod.yml exec backend alembic history

# Rollback one migration
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# Rollback to specific revision
docker compose -f docker-compose.prod.yml exec backend alembic downgrade abc123
```

## Health Checks

### Verify Services Are Running

```bash
cd /home/deploy/parchmark

# Check container status
docker compose -f docker-compose.prod.yml ps

# Check backend health endpoint
curl -f https://assets-api.engen.tech/api/health

# Check frontend is serving
curl -f https://notes.engen.tech/
```

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs backend

# Check if image exists
docker images | grep parchmark-backend

# Try pulling the image manually
docker pull ghcr.io/tejgandham/parchmark-backend:latest
```

### GHCR Authentication Failed

```bash
# Test GHCR login manually
echo "$GHCR_TOKEN" | docker login ghcr.io -u tejgandham --password-stdin

# If token expired, create a new one at:
# https://github.com/settings/tokens
# Required scope: read:packages
```

### Database Connection Issues

```bash
# Check postgres is running
docker compose -f docker-compose.prod.yml ps postgres

# Check postgres logs
docker compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker compose -f docker-compose.prod.yml exec postgres psql -U parchmark_user -d parchmark_db -c "SELECT 1"
```

### Migrations Failed

```bash
# Check migration status
docker compose -f docker-compose.prod.yml exec backend alembic current

# View migration history
docker compose -f docker-compose.prod.yml exec backend alembic history

# Try running migrations manually
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Security Best Practices

### Token Security

1. **GHCR Token Scope**: Use a Classic Personal Access Token with **only** `read:packages` scope
   - Fine-grained tokens are NOT supported by GitHub Packages
   - Never use a token with write permissions on the production server

2. **Token Rotation Schedule**: Rotate the GHCR token every **90 days**
   - Set a calendar reminder for token expiration
   - Generate new token at: https://github.com/settings/tokens
   - Update `.env.deploy` with new token
   - Test with: `./deploy/update.sh`

3. **Consider GitHub App Tokens**: For enhanced security, consider using a GitHub App
   - More granular permissions than PATs
   - Automatic token rotation
   - Better audit logging
   - See: https://docs.github.com/en/apps/creating-github-apps

### File Permissions

1. **Environment files**: All `.env*` files should have `600` permissions
   ```bash
   chmod 600 .env.deploy .env.db backend/.env.production
   ```

2. **Never commit secrets**: Ensure `.env*` files are in `.gitignore`

### Access Control

1. **SSH access**: Use ED25519 key-based authentication only, no passwords
2. **Limit sudo access**: The deploy user should only have Docker permissions
3. **Firewall**: Ensure only necessary ports are exposed (80, 443)

## Directory Structure

```
/home/deploy/parchmark/
├── .env.db                    # Database credentials
├── .env.deploy                # GHCR credentials
├── backend/
│   └── .env.production        # Backend configuration
├── ui/
│   └── .env.production        # Frontend configuration
├── deploy/
│   ├── update.sh              # Update script
│   └── SERVER_SETUP.md        # This file
├── logs/
│   └── update.log             # Update script logs
├── docker-compose.prod.yml    # Production compose file
└── ...
```
