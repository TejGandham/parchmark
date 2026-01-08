# AUTHELIA_OIDC_PLAN.md - Implementation Guide

**Purpose**: Step-by-step implementation guide to deploy the OIDC system to production
**Audience**: DevOps/SRE engineers performing the deployment
**Time**: ~30 minutes for complete deployment
**Date**: January 8, 2026

---

## Pre-Deployment Checklist

Before starting, ensure you have:
- ✅ Access to Authelia configuration
- ✅ SSH access to production servers
- ✅ DNS management access for auth.engen.tech, notes.engen.tech, assets-api.engen.tech
- ✅ Docker/container runtime access
- ✅ GitHub repository access

---

## Step 1: Authelia Configuration (OIDC Client Setup)

### 1.1 Update Authelia Configuration

**Location**: Authelia server configuration file (typically `authelia/configuration.yml`)

**Action**: Add the OIDC client configuration:

```yaml
identity_providers:
  oidc:
    clients:
      - client_id: parchmark-web
        client_name: ParchMark
        client_secret: "{{ env 'OIDC_CLIENT_SECRET' }}"  # Generate a secure secret
        public: true
        redirect_uris:
          - "https://notes.engen.tech/oidc/callback"
          - "http://localhost:5173/oidc/callback"  # Development
        scopes:
          - openid
          - profile
          - email
        grant_types:
          - authorization_code
          - refresh_token
        require_pkce: true
        pkce_challenge_method: S256
        response_types:
          - code
```

**Generate Client Secret** (if needed):
```bash
openssl rand -base64 32
```

### 1.2 Restart Authelia

```bash
# If using Docker
docker compose restart authelia

# If using systemd
sudo systemctl restart authelia

# Verify it's running
curl https://auth.engen.tech/.well-known/openid-configuration
```

**Expected Output**: JSON with OIDC metadata including `issuer`, `jwks_uri`, `authorization_endpoint`, `token_endpoint`

---

## Step 2: Backend Environment Configuration

### 2.1 Update Backend .env File

**Location**: `backend/.env` (production environment)

**Action**: Add these environment variables:

```bash
# OIDC Configuration
AUTH_MODE=hybrid
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark-web
OIDC_USERNAME_CLAIM=preferred_username

# Existing variables (keep these)
SECRET_KEY=<your-32-char-secret-key>
DATABASE_URL=postgresql://user:password@host:5432/dbname
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech
```

### 2.2 Verify Backend Configuration

```bash
# SSH into backend server
ssh user@assets-api.engen.tech

# Test OIDC validator can reach Authelia
curl https://auth.engen.tech/.well-known/openid-configuration

# Check environment variables are set
grep OIDC /path/to/.env
```

---

## Step 3: Frontend Environment Configuration

### 3.1 Update Frontend .env File

**Location**: `ui/.env` (production environment)

**Action**: Add these environment variables:

```bash
# OIDC Configuration
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login

# Existing variables (keep these)
VITE_API_URL=https://assets-api.engen.tech/api
```

### 3.2 Verify Frontend Configuration

```bash
# SSH into frontend server
ssh user@notes.engen.tech

# Check environment variables are set
grep VITE_OIDC /path/to/.env

# Verify build includes OIDC config
grep -r "VITE_OIDC" /app/dist/ || echo "Build may need refresh"
```

---

## Step 4: Database Schema Migration

### 4.1 Apply User Model Changes

**Location**: Production database

**Action**: Run database migrations (automatic via SQLAlchemy):

```bash
# SSH into backend server
ssh user@assets-api.engen.tech

# The app will auto-migrate on startup
# To manually apply (if needed):
cd /path/to/backend

# Backup database first
pg_dump postgresql://user:password@host:5432/dbname > backup.sql

# Run app (will auto-migrate)
python -m uvicorn app.main:app
```

**Expected Schema Changes**:
- Add `oidc_sub` column (unique, nullable)
- Add `email` column (nullable)
- Add `auth_provider` column (default: 'local')
- Make `password_hash` nullable

**Verify Migration**:
```bash
# Connect to database
psql postgresql://user:password@host:5432/dbname

# Check new columns exist
\d "user"

# Should show:
# oidc_sub      | character varying(255)
# email         | character varying(255)
# auth_provider | character varying(50)
# password_hash | character varying(255) -- nullable
```

---

## Step 5: Build and Deploy Backend

### 5.1 Build Backend Docker Image

```bash
# From project root
cd backend

# Build with production Dockerfile
docker build -f Dockerfile.prod -t parchmark-backend:oidc-ready .

# Tag for registry
docker tag parchmark-backend:oidc-ready ghcr.io/yourusername/parchmark-backend:oidc-ready
```

### 5.2 Deploy Backend

```bash
# Push to container registry
docker push ghcr.io/yourusername/parchmark-backend:oidc-ready

# Update production deployment
# Option A: Docker Compose
cd /path/to/production
# Update docker-compose.prod.yml to use new image tag
docker compose -f docker-compose.prod.yml up -d

# Option B: Kubernetes
kubectl set image deployment/parchmark-backend \
  parchmark-backend=ghcr.io/yourusername/parchmark-backend:oidc-ready

# Option C: Manual SSH deployment
ssh user@assets-api.engen.tech
docker pull ghcr.io/yourusername/parchmark-backend:oidc-ready
docker stop parchmark-backend
docker run -d --name parchmark-backend \
  --env-file /path/to/.env \
  -p 8000:8000 \
  ghcr.io/yourusername/parchmark-backend:oidc-ready
```

### 5.3 Verify Backend Health

```bash
# Check health endpoint
curl https://assets-api.engen.tech/api/health

# Check logs for OIDC configuration
docker logs parchmark-backend | grep -i oidc
```

---

## Step 6: Build and Deploy Frontend

### 6.1 Build Frontend Docker Image

```bash
# From project root
cd ui

# Build with production Dockerfile
docker build -f Dockerfile.prod -t parchmark-frontend:oidc-ready .

# Tag for registry
docker tag parchmark-frontend:oidc-ready ghcr.io/yourusername/parchmark-frontend:oidc-ready
```

### 6.2 Deploy Frontend

```bash
# Push to container registry
docker push ghcr.io/yourusername/parchmark-frontend:oidc-ready

# Update production deployment
# Option A: Docker Compose
cd /path/to/production
# Update docker-compose.prod.yml to use new image tag
docker compose -f docker-compose.prod.yml up -d

# Option B: Kubernetes
kubectl set image deployment/parchmark-frontend \
  parchmark-frontend=ghcr.io/yourusername/parchmark-frontend:oidc-ready

# Option C: Manual SSH deployment
ssh user@notes.engen.tech
docker pull ghcr.io/yourusername/parchmark-frontend:oidc-ready
docker stop parchmark-frontend
docker run -d --name parchmark-frontend \
  --env-file /path/to/.env \
  -p 80:8080 \
  -p 443:8443 \
  ghcr.io/yourusername/parchmark-frontend:oidc-ready
```

### 6.3 Verify Frontend Health

```bash
# Check frontend loads
curl https://notes.engen.tech/

# Check for SSO button
curl https://notes.engen.tech/ | grep -i "sign in with sso"
```

---

## Step 7: Verify DNS and CORS

### 7.1 Verify DNS Resolution

```bash
# From any machine
nslookup auth.engen.tech
nslookup notes.engen.tech
nslookup assets-api.engen.tech

# Should all resolve correctly
```

### 7.2 Verify CORS Configuration

```bash
# Check CORS headers from backend
curl -i -H "Origin: https://notes.engen.tech" \
  https://assets-api.engen.tech/api/health

# Should include:
# Access-Control-Allow-Origin: https://notes.engen.tech
```

---

## Step 8: Run Deployment Validation

### 8.1 Run Automated Validation Script

```bash
# From project root
cd backend

# Run validation script
python scripts/validate_oidc_deployment.py \
  --issuer https://auth.engen.tech \
  --audience parchmark-web \
  --frontend-url https://notes.engen.tech \
  --api-url https://assets-api.engen.tech

# Expected output: All checks passing
```

### 8.2 Manual Health Checks

```bash
# 1. Check Authelia discovery endpoint
curl https://auth.engen.tech/.well-known/openid-configuration \
  | jq '.issuer, .jwks_uri'

# 2. Check backend health
curl https://assets-api.engen.tech/api/health

# 3. Check frontend loads
curl -I https://notes.engen.tech/

# 4. Check login page renders
curl https://notes.engen.tech/ | grep -i "sign in"
```

---

## Step 9: Test Authentication Flows

### 9.1 Test Local Login Flow

```bash
# 1. Open browser and navigate to https://notes.engen.tech/login
# 2. Click "Sign in with username and password"
# 3. Enter test user credentials (existing local user)
# 4. Verify successful login and redirect to notes page
# 5. Verify user info appears in sidebar

# In logs, should see:
# "Local JWT validated successfully"
```

### 9.2 Test OIDC Login Flow

```bash
# 1. Open browser and navigate to https://notes.engen.tech/login
# 2. Click "Sign in with SSO"
# 3. Redirect to Authelia login page
# 4. Enter Authelia credentials
# 5. Approve consent (if configured)
# 6. Redirect to /oidc/callback
# 7. Verify successful login and redirect to notes page
# 8. Verify user auto-created if first OIDC login

# In logs, should see:
# "OIDC token validation successful"
# "Auto-created OIDC user" (if first login)
```

### 9.3 Test Token Refresh

```bash
# 1. Login successfully (local or OIDC)
# 2. Wait for token expiration (or manually trigger via browser devtools)
# 3. Make an API request (e.g., list notes)
# 4. Verify 401 interceptor catches it
# 5. Verify token is refreshed
# 6. Verify API request retried and succeeds

# In logs, should see:
# "Token refresh initiated"
# "Token refreshed successfully"
```

### 9.4 Test Logout

```bash
# 1. Login successfully
# 2. Click logout button
# 3. If OIDC: Should redirect through Authelia end_session
# 4. Verify redirected to login page
# 5. Verify session cleared (localStorage empty)

# In logs, should see:
# "User logged out"
```

---

## Step 10: Enable Monitoring and Logging

### 10.1 Configure Application Logging

**Backend logging level** (increase during initial deployment):
```python
# backend/app/main.py or logging config
logging.basicConfig(level=logging.DEBUG)
# Watch for OIDC validation logs
```

### 10.2 Set Up Log Aggregation

```bash
# If using ELK, Loki, or similar
# Tag backend logs with: component=oidc-validator
# Tag frontend logs with: component=oidc-flow

# Watch for errors:
# - OIDC token validation failed
# - JWKS fetch failed
# - Issuer mismatch
# - Audience mismatch
```

### 10.3 Configure Alerts

Set up alerts for:
- OIDC validation errors (>5 per minute)
- JWKS fetch timeouts (>3 consecutive)
- Backend health check failures
- Frontend OIDC callback errors

---

## Step 11: Backup and Rollback Plan

### 11.1 Backup Current State

```bash
# Backup database
pg_dump postgresql://user:password@host:5432/dbname > backup_pre_oidc.sql

# Backup current container images
docker save parchmark-backend:current -o parchmark-backend-backup.tar
docker save parchmark-frontend:current -o parchmark-frontend-backup.tar

# Store in secure location
# aws s3 cp backup_pre_oidc.sql s3://backups/
# aws s3 cp parchmark-*-backup.tar s3://backups/
```

### 11.2 Rollback Procedure (if needed)

```bash
# Restore database
psql postgresql://user:password@host:5432/dbname < backup_pre_oidc.sql

# Restore backend
docker load < parchmark-backend-backup.tar
docker stop parchmark-backend
docker run -d --name parchmark-backend \
  --env-file /path/to/.env \
  -p 8000:8000 \
  parchmark-backend:current

# Restore frontend
docker load < parchmark-frontend-backup.tar
docker stop parchmark-frontend
docker run -d --name parchmark-frontend \
  --env-file /path/to/.env \
  -p 80:8080 \
  parchmark-frontend:current

# Remove OIDC env vars from .env files
# Restart services
```

---

## Post-Deployment Verification (Day 1)

### Checklist

- ✅ Local login still works
- ✅ OIDC login works
- ✅ User auto-creation works
- ✅ Token refresh works
- ✅ Logout works
- ✅ No errors in logs
- ✅ Health checks passing
- ✅ API endpoints responding
- ✅ Frontend loads quickly
- ✅ CORS headers correct
- ✅ DNS resolving correctly
- ✅ SSL certificates valid

### Performance Baseline

Document these metrics:
- Auth success rate: _____% (target: >99%)
- Token validation latency: _____ms (target: <10ms)
- OIDC provider latency: _____ms (target: <200ms)
- API response time: _____ms (target: <300ms)

---

## Post-Deployment Verification (Week 1)

### Monitoring Checklist

- ✅ Zero OIDC validation errors in logs
- ✅ User auto-creation working correctly
- ✅ Token refresh happening as expected
- ✅ No database issues
- ✅ JWKS cache working (1-hour TTL)
- ✅ No concurrent request issues
- ✅ Performance stable
- ✅ User adoption metrics collected

### Security Review

- ✅ No sensitive data in logs
- ✅ PKCE S256 enforced
- ✅ CORS restricted correctly
- ✅ No auth bypass vulnerabilities
- ✅ Rate limiting functional (if configured)

---

## Troubleshooting

### Issue: "Invalid client_id"

**Cause**: Authelia configuration not reloaded or client not registered
**Solution**:
```bash
# Verify client in Authelia config
grep -A 20 "parchmark-web" /path/to/authelia/configuration.yml

# Restart Authelia
docker compose restart authelia

# Check discovery endpoint
curl https://auth.engen.tech/.well-known/openid-configuration
```

### Issue: "OIDC token validation failed: issuer mismatch"

**Cause**: `OIDC_ISSUER_URL` doesn't match token's `iss` claim
**Solution**:
```bash
# Check token's iss claim
jwt_cli decode --token <token> | grep iss

# Verify OIDC_ISSUER_URL in backend .env
grep OIDC_ISSUER_URL /path/to/.env

# Should match exactly (including https://)
```

### Issue: "JWKS fetch failed: timeout"

**Cause**: Network issue or Authelia JWKS endpoint down
**Solution**:
```bash
# Test connectivity
curl -v https://auth.engen.tech/.well-known/openid-configuration

# Check Authelia status
docker ps | grep authelia

# Check firewall rules
sudo iptables -L -n | grep 9091  # Authelia internal port
```

### Issue: "User auto-creation failed: IntegrityError"

**Cause**: Concurrent requests both trying to create same user
**Solution**: Already handled in code - check logs for recovery
```bash
# Verify user was created
SELECT * FROM "user" WHERE oidc_sub = '<oidc_sub>';

# Should exist (race condition recovery worked)
```

---

## Success Criteria

Deployment is successful when:

1. ✅ Both local and OIDC login flows work
2. ✅ New OIDC users auto-created on first login
3. ✅ Token refresh works for both auth types
4. ✅ Logout clears session properly
5. ✅ No authentication errors in logs
6. ✅ Health checks passing
7. ✅ Performance metrics within targets
8. ✅ Users can navigate and use notes
9. ✅ Zero data loss or corruption
10. ✅ Rollback plan verified and ready

---

## Support and Escalation

**If issues occur**:
1. Check `AUTHELIA_OIDC_TROUBLESHOOTING.md`
2. Review logs from all components
3. Run validation script again
4. Consult `AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md`
5. Contact security team if auth-related
6. Prepare for rollback if needed

---

## Next: Operations and Monitoring

After successful deployment, transition to:
- Daily health checks (see `AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md`)
- Weekly security review
- Monthly performance optimization
- Quarterly disaster recovery drills

---

**Document**: AUTHELIA_OIDC_PLAN_IMPLEMENTATION_GUIDE.md
**Version**: 1.0
**Status**: Production Ready
**Last Updated**: January 8, 2026
