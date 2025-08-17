# ParchMark Production Deployment Guide

This guide provides step-by-step instructions for deploying ParchMark to a production server using Docker Compose and Nginx Proxy Manager on Debian.

## Overview

**Frontend URL:** `https://notes.engen.tech`  
**Backend API URL:** `https://assets-api.engen.tech`

**Architecture:**
- Frontend: React app served via Nginx container
- Backend: FastAPI application with SQLite database
- Nginx Proxy Manager: SSL termination and reverse proxy
- Docker Network: `proxiable` (shared with NPM)

## Prerequisites

- Debian server with Docker and Docker Compose installed
- Nginx Proxy Manager running on `proxiable` network
- DNS records pointing both domains to your server IP
- Access to Nginx Proxy Manager web interface

## Step 1: Generate Production Secret Key

Generate a secure JWT secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save this key - you'll need it in Step 3.

## Step 2: DNS Configuration

Create A records pointing to your server IP:
- `notes.engen.tech` → Your server IP
- `assets-api.engen.tech` → Your server IP

Wait for DNS propagation (can take up to 24 hours).

## Step 3: Environment Configuration

The following files have been created for production:

### Backend Environment (`.env.production`)
```env
# ParchMark Backend Production Configuration

# JWT Configuration - CHANGE THESE IN PRODUCTION!
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=CHANGE_THIS_SECRET_KEY_IN_PRODUCTION
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration
DATABASE_URL=sqlite:///./data/parchmark.db

# Application Configuration
APP_NAME=ParchMark API
APP_VERSION=1.0.0
DEBUG=false

# CORS Configuration - Production domains
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
```

**⚠️ IMPORTANT:** Replace `CHANGE_THIS_SECRET_KEY_IN_PRODUCTION` with the key generated in Step 1.

### Frontend Environment (`.env.production`)
```env
# ParchMark Frontend Production Configuration

# Set to "false" since Nginx Proxy Manager handles SSL
USE_HTTPS=false
```

## Step 4: Docker Compose Configuration

The production compose file (`docker-compose.prod.yml`) has been created with:

- Both services connected to `proxiable` network for NPM integration
- Internal network for frontend-backend communication
- Persistent volume for database storage
- Proper container naming and restart policies

## Step 5: Nginx Proxy Manager Configuration

### Frontend Proxy Host (notes.engen.tech)

1. **Go to Proxy Hosts → Add Proxy Host**

2. **Details Tab:**
   ```
   Domain Names: notes.engen.tech
   Scheme: http
   Forward Hostname/IP: parchmark-frontend
   Forward Port: 80
   ```

3. **Advanced Tab:**
   ```
   ☑️ Cache Assets
   ☑️ Block Common Exploits  
   ☑️ Websockets Support
   ☐ Access List (None)
   
   Custom Nginx Configuration: (leave empty)
   ```

4. **SSL Tab:**
   ```
   ☑️ SSL Certificate
   ☑️ Force SSL
   ☑️ HTTP/2 Support
   ☑️ HSTS Enabled
   ☐ HSTS Subdomains

   Certificate: Request a new SSL Certificate
   Provider: Let's Encrypt
   Email Address: your-email@domain.com
   Domain Names: notes.engen.tech
   ☑️ Use a DNS Challenge
   ☑️ I Agree to the Let's Encrypt Terms of Service
   ```

### Backend Proxy Host (assets-api.engen.tech)

1. **Add Proxy Host (second one)**

2. **Details Tab:**
   ```
   Domain Names: assets-api.engen.tech
   Scheme: http
   Forward Hostname/IP: parchmark-backend
   Forward Port: 8000
   ```

3. **Advanced Tab:**
   ```
   ☐ Cache Assets (APIs shouldn't cache)
   ☑️ Block Common Exploits
   ☐ Websockets Support (not needed for API)
   ☐ Access List (None)
   
   Custom Nginx Configuration: (leave empty)
   ```

4. **SSL Tab:**
   ```
   ☑️ SSL Certificate
   ☑️ Force SSL
   ☑️ HTTP/2 Support
   ☑️ HSTS Enabled
   ☐ HSTS Subdomains

   Certificate: Request a new SSL Certificate
   Provider: Let's Encrypt
   Email Address: your-email@domain.com
   Domain Names: assets-api.engen.tech
   ☑️ Use a DNS Challenge
   ☑️ I Agree to the Let's Encrypt Terms of Service
   ```

## Security Hardening (TODO)

To protect the application against brute-force login attacks and other common threats, apply the following custom Nginx configurations in the "Advanced" tab for the respective proxy hosts.

### Backend Hardening (`assets-api.engen.tech`)

This configuration applies rate limiting specifically to the `/token` authentication endpoint to prevent brute-force attacks.

```nginx
# --- ParchMark Backend Security ---

# 1. Rate Limiting Zone
# Creates a 10MB shared memory zone named 'login_limit_zone' to store IP addresses.
# Allows an average of 10 requests per minute (r/m) per IP address.
limit_req_zone $binary_remote_addr zone=login_limit_zone:10m rate=10r/m;

# 2. Apply Rate Limiting to the Login Endpoint
# Any requests to the /token path will be subject to the rate limit.
location /token {
    # Apply the 'login_limit_zone' limit.
    # 'burst=20' allows a short burst of up to 20 requests before throttling.
    # 'nodelay' ensures legitimate requests in the burst are not delayed.
    limit_req zone=login_limit_zone burst=20 nodelay;

    # Standard proxy settings (NPM adds these, but explicit is safer)
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://parchmark-backend:8000;
}
```

### Frontend Hardening (`notes.engen.tech`)

This configuration adds general rate limiting and important security headers to protect against scraping and common browser-based attacks.

```nginx
# --- ParchMark Frontend Security ---

# 1. General Rate Limiting
# Creates a zone to limit all visitors to 60 requests per minute.
# This is a general protection against scraping or simple DoS attacks.
limit_req_zone $binary_remote_addr zone=frontend_limit_zone:10m rate=60r/m;
limit_req zone=frontend_limit_zone burst=100 nodelay;

# 2. Security Headers
# Adds headers to protect against common web vulnerabilities.
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

## Step 6: Deployment

1. **Upload/Clone your code to the server:**
   ```bash
   cd /path/to/your/parchmark
   ```

2. **Update the backend secret key:**
   ```bash
   nano backend/.env.production
   # Replace CHANGE_THIS_SECRET_KEY_IN_PRODUCTION with your generated key
   ```

3. **Build and start containers:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Verify containers are running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

5. **Check logs if needed:**
   ```bash
   # Frontend logs
   docker compose -f docker-compose.prod.yml logs frontend
   
   # Backend logs
   docker compose -f docker-compose.prod.yml logs backend
   ```

## Step 7: Testing

1. **Frontend:** Visit `https://notes.engen.tech`
   - Should load the ParchMark application
   - Should redirect HTTP to HTTPS

2. **Backend API Documentation:** Visit `https://assets-api.engen.tech/docs`
   - Should load FastAPI Swagger documentation
   - Should redirect HTTP to HTTPS

3. **Health Check:** Visit `https://assets-api.engen.tech/health`
   - Should return JSON: `{"status": "healthy", "service": "ParchMark API", "version": "1.0.0"}`

## Architecture Notes

### Why Both Frontend and Backend?
- **Frontend:** Serves the React application and handles routing
- **Backend:** Provides JWT authentication, note storage, and API endpoints
- **Database:** SQLite database persisted in Docker volume for user data

### Network Communication
- **External Access:** Nginx Proxy Manager → Frontend/Backend containers
- **Internal API Calls:** Frontend container → Backend container (Docker network)
- **Database:** Stored in Docker volume, accessed by backend only

### Security
- SSL certificates automatically managed by Let's Encrypt
- CORS configured for production domains only  
- JWT tokens for API authentication
- Database isolated within Docker network

## Troubleshooting

### Container Issues
```bash
# View all logs
docker compose -f docker-compose.prod.yml logs

# Restart services
docker compose -f docker-compose.prod.yml restart

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build --force-recreate
```

### SSL Certificate Issues
- Ensure DNS records are propagated
- Check Nginx Proxy Manager logs for Let's Encrypt errors
- Verify email address is valid for Let's Encrypt notifications

### Database Issues
```bash
# Check database volume
docker volume ls | grep parchmark

# Access backend container
docker exec -it parchmark-backend bash

# View database location
ls -la /app/data/
```

### Network Issues
```bash
# Verify proxiable network exists
docker network ls | grep proxiable

# Check container network connections
docker network inspect proxiable
```

## Maintenance

### Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Backups
```bash
# Backup database volume
docker run --rm -v parchmark-data:/source -v $(pwd):/backup alpine tar czf /backup/parchmark-backup-$(date +%Y%m%d).tar.gz -C /source .

# Restore database volume
docker run --rm -v parchmark-data:/target -v $(pwd):/backup alpine tar xzf /backup/parchmark-backup-YYYYMMDD.tar.gz -C /target
```

## Manual User Management

A script is provided to manually manage users from the command line. Use this for creating admin users, resetting passwords, or deleting accounts.

**Note:** Run these commands from the root of the project directory.

### Create a User
```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py create <username> '<password>'
```

### Update a User's Password
```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py update-password <username> '<new_password>'
```

### Delete a User
```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py delete <username>
```

---

**Note:** This setup provides a production-ready deployment with SSL, proper networking, and data persistence. Both the frontend application and backend API are required for full functionality.