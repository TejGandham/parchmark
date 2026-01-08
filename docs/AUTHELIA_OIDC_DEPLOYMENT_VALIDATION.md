# OIDC Deployment Validation Guide

Pre-deployment validation checklist and automated validation script for ensuring ParchMark OIDC implementation is production-ready.

---

## Overview

The `validate_oidc_deployment.py` script provides automated verification that:

- ✅ All required environment variables are configured
- ✅ All services are reachable and healthy
- ✅ Database connectivity is working
- ✅ OIDC provider is properly configured
- ✅ API endpoints are accessible
- ✅ Performance metrics are acceptable
- ✅ Security settings are appropriate for the environment

---

## Quick Start

### Run Validation

```bash
# For development
make validate-oidc-dev

# For staging
make validate-oidc-staging

# For production
make validate-oidc-prod

# Direct usage
cd backend && uv run python scripts/validate_oidc_deployment.py --environment production
```

### Expected Output

```
======================================================================
     ParchMark OIDC Deployment Validation (PRODUCTION)
======================================================================

Environment Variables
---------------------
✓ DATABASE_URL is set
✓ SECRET_KEY is set
✓ ALGORITHM is set
✓ ACCESS_TOKEN_EXPIRE_MINUTES is set
✓ ALLOWED_ORIGINS is set
✓ AUTH_MODE is set
✓ OIDC_ISSUER_URL is set
✓ OIDC_AUDIENCE is set
✓ OIDC_USERNAME_CLAIM is set
✓ SECRET_KEY is strong (32+ chars)
✓ AUTH_MODE is valid (hybrid)

...more checks...

======================================================================
                     Validation Summary
======================================================================

...check results...

✓ ALL CHECKS PASSED (45/45)
✓ Deployment is ready for PRODUCTION
```

---

## Validation Checks

### 1. Environment Variables

Verifies all required environment variables are set:

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | postgresql://user:pass@host/db |
| `SECRET_KEY` | JWT signing key | (32+ characters) |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | 30 |
| `ALLOWED_ORIGINS` | CORS origins | https://notes.engen.tech |
| `AUTH_MODE` | Auth method | hybrid |
| `OIDC_ISSUER_URL` | OIDC provider | https://auth.engen.tech |
| `OIDC_AUDIENCE` | OIDC client ID | parchmark-web |
| `OIDC_USERNAME_CLAIM` | Username claim | preferred_username |

**Checks**:
- All variables are present
- SECRET_KEY is 32+ characters
- AUTH_MODE is valid (hybrid/oidc/local)

---

### 2. Service Connectivity

Verifies all services are reachable:

- **Backend API**: Health endpoint responds
- **OIDC Provider**: Discovery endpoint accessible
- **Network**: Services can communicate

**Checks**:
- Backend `/api/health` returns 200
- OIDC discovery endpoint returns 200
- No connection timeouts

---

### 3. Database Connectivity

Verifies database configuration and connectivity:

- **URL**: DATABASE_URL is configured
- **Type**: PostgreSQL detected
- **Location**: Warning if localhost in production
- **Access**: Can connect to database

**Checks**:
- DATABASE_URL is set
- PostgreSQL is configured
- Production deploys not on localhost

---

### 4. OIDC Configuration

Verifies OIDC provider is properly configured:

- **Issuer URL**: Valid and reachable
- **Client ID**: Configured
- **Discovery**: Discovery endpoint works
- **Scopes**: Required scopes (openid, profile, email) available
- **HTTPS**: Production uses HTTPS

**Checks**:
- OIDC_ISSUER_URL is set and formatted correctly
- OIDC_AUDIENCE is set
- OIDC_USERNAME_CLAIM is set
- Discovery endpoint is accessible
- Required scopes are supported
- Production uses HTTPS for issuer

---

### 5. Health Checks

Verifies services are healthy:

- **API**: `/api/health` endpoint responds
- **Database**: Database connection is active
- **Status**: Services report healthy status

**Checks**:
- Backend health returns 200
- Database status is "connected"
- Service metadata is present

---

### 6. Performance Metrics

Verifies performance is acceptable:

- **API Response**: < 100ms average
- **OIDC Response**: < 200ms average
- **Network**: No significant latency

**Checks**:
- API responds in < 100ms
- OIDC provider responds in < 200ms
- Performance acceptable for production

**Interpretation**:
- ✓ Green: Performance acceptable
- ⚠ Yellow: Performance adequate but could improve
- ✗ Red: Performance below acceptable threshold

---

### 7. Security Configuration

Verifies security settings are appropriate:

- **Environment**: Set to "production" in prod
- **CORS Origins**: No localhost in production
- **HTTPS**: Production origins use HTTPS
- **SSL/TLS**: Certificates are valid

**Checks**:
- ENVIRONMENT is set to "production" for prod
- ALLOWED_ORIGINS excludes localhost in prod
- Production origins use HTTPS

---

### 8. API Endpoints

Verifies all critical endpoints are accessible:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | Local login |
| `/api/auth/refresh` | POST | Token refresh |
| `/api/auth/me` | GET | Current user |
| `/api/auth/logout` | POST | Logout |
| `/api/notes` | GET | List notes |
| `/docs` | GET | API docs |

**Checks**:
- All endpoints are accessible (HTTP < 404)
- Required endpoints respond properly

---

## Usage Guide

### Development Validation

```bash
# Check development environment
make validate-oidc-dev

# Direct command
cd backend && uv run python scripts/validate_oidc_deployment.py --environment development
```

**Notes**:
- Localhost is acceptable
- HTTP is acceptable
- Less strict checks

---

### Staging Validation

```bash
# Check staging environment
make validate-oidc-staging

# Direct command
cd backend && uv run python scripts/validate_oidc_deployment.py --environment staging
```

**Notes**:
- Same checks as production
- Can fail with warnings
- Useful for pre-production testing

---

### Production Validation

```bash
# Check production environment BEFORE deployment
make validate-oidc-prod

# Direct command
cd backend && uv run python scripts/validate_oidc_deployment.py --environment production
```

**Must Pass All Checks**:
- ✓ All environment variables required
- ✓ Services must be reachable
- ✓ Database must be connected
- ✓ OIDC must be HTTPS
- ✓ ALLOWED_ORIGINS must use HTTPS
- ✓ No localhost allowed
- ✓ Performance must be good

---

## Error Interpretation

### Common Errors and Solutions

#### ✗ DATABASE_URL is set

**Error**:
```
✗ Database URL configured: DATABASE_URL not set
```

**Solution**:
1. Set DATABASE_URL environment variable
2. Use PostgreSQL connection string
3. Example: `postgresql://user:password@host:5432/db`

---

#### ✗ Backend API reachable

**Error**:
```
✗ Backend API reachable: Connection refused
```

**Solution**:
1. Verify backend is running: `docker ps | grep backend`
2. Check backend logs: `docker logs parchmark-backend`
3. Verify port 8000 is accessible
4. Restart backend: `docker restart parchmark-backend`

---

#### ✗ OIDC provider reachable

**Error**:
```
✗ OIDC provider reachable: Connection timeout
```

**Solution**:
1. Verify Authelia is running: `docker ps | grep authelia`
2. Check OIDC_ISSUER_URL is correct
3. Verify network connectivity
4. Restart Authelia: `docker restart authelia`

---

#### ✗ Database connection healthy

**Error**:
```
✗ Database connection healthy: Status: disconnected
```

**Solution**:
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check DATABASE_URL credentials
3. Verify database exists
4. Restart PostgreSQL: `docker restart postgres`

---

#### ✗ OIDC_ISSUER_URL uses HTTPS

**Error** (production):
```
✗ OIDC_ISSUER_URL uses HTTPS: Production must use HTTPS
```

**Solution**:
1. Change OIDC_ISSUER_URL to use HTTPS
2. Example: `https://auth.engen.tech` (not `http://`)
3. Ensure SSL certificate is valid
4. Restart backend with new config

---

#### ✗ API response time < 100ms

**Error**:
```
⚠ API response time < 100ms: Average: 245.3ms
```

**Solution**:
1. Check backend logs for errors
2. Monitor CPU/memory usage
3. Check database query performance
4. Increase backend resources if needed

---

## Pre-Deployment Checklist

Use this checklist before deploying to production:

```bash
# 1. Run validation
make validate-oidc-prod

# 2. Fix any ✗ errors
# (see error interpretation guide)

# 3. Run again to verify all pass
make validate-oidc-prod

# 4. Run OIDC tests
make test-oidc-integration

# 5. Run full test suite
make test-all

# 6. Run smoke tests
cd backend && uv run pytest tests/integration/auth/ -v

# 7. Performance testing
make test-oidc-perf

# 8. Manual verification
# - Test local login in staging
# - Test OIDC login in staging
# - Create/edit/delete notes as OIDC user
# - Verify token refresh works
# - Test logout

# 9. Database backup
# - Backup production database
# - Store securely

# 10. Have rollback plan
# - Know previous working image SHA
# - Have rollback commands ready
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/pre-deploy.yml
name: Pre-Deployment Validation

on: workflow_dispatch

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate Development
        run: make validate-oidc-dev

      - name: Validate Staging
        run: make validate-oidc-staging
        env:
          API_URL: https://api-staging.engen.tech
          OIDC_ISSUER_URL: https://auth-staging.engen.tech

      - name: Validate Production
        run: make validate-oidc-prod
        env:
          API_URL: https://assets-api.engen.tech
          OIDC_ISSUER_URL: https://auth.engen.tech
```

### Pre-Push Hook

```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running pre-deployment validation..."
make validate-oidc-prod

if [ $? -ne 0 ]; then
  echo "✗ Validation failed - push aborted"
  exit 1
fi

echo "✓ Validation passed - ready to push"
exit 0
```

---

## Performance Benchmarks

### Expected Performance

| Metric | Expected | Acceptable | Warning |
|--------|----------|------------|---------|
| API Health | < 50ms | < 100ms | > 100ms |
| OIDC Discovery | < 100ms | < 200ms | > 200ms |
| JWKS Fetch | < 50ms | < 100ms | > 100ms |
| Database Query | < 10ms | < 50ms | > 50ms |

### Performance Optimization

If performance is slow:

1. **Check Database**:
   - Connection pool size
   - Query performance
   - Indexes on frequently queried columns

2. **Check Network**:
   - Latency to OIDC provider
   - Network bandwidth
   - DNS resolution time

3. **Check Backend**:
   - CPU usage
   - Memory usage
   - Concurrent requests

4. **Enable Caching**:
   - JWKS caching (1 hour TTL)
   - Response caching
   - Token caching

---

## Exit Codes

```
0 = Validation passed, ready to deploy
1 = Validation failed, do not deploy
```

Use in scripts:

```bash
make validate-oidc-prod
if [ $? -eq 0 ]; then
  echo "✓ Ready for deployment"
  git push origin main
else
  echo "✗ Fix validation errors first"
  exit 1
fi
```

---

## Troubleshooting Validation Issues

### Validation Script Fails to Run

```bash
# Verify Python is available
python --version

# Verify dependencies
cd backend && uv --version

# Run with verbose output
cd backend && uv run python scripts/validate_oidc_deployment.py --environment dev 2>&1 | head -50
```

### Timeouts During Validation

```bash
# Services might be slow to start
# Wait a bit longer
sleep 30
make validate-oidc-dev

# Or increase timeout in script (edit validate_oidc_deployment.py)
# Change: timeout=10
# To: timeout=30
```

### Network Connectivity Issues

```bash
# Test specific service
curl -I http://localhost:8000/api/health

# Test OIDC provider
curl -I http://localhost:9091/.well-known/openid-configuration

# Check Docker network
docker network ls
docker network inspect parchmark_default
```

---

## See Also

- **AUTHELIA_OIDC_DEPLOYMENT.md** - Full deployment checklist
- **AUTHELIA_OIDC_LOCAL_TESTING.md** - Local testing guide
- **AUTHELIA_OIDC_TESTING_UTILITY.md** - Integration testing utility
- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Problem diagnosis

---

## Support

For validation issues:

1. Check specific error message in script output
2. Review error interpretation guide above
3. Check service logs: `docker logs <service>`
4. Verify environment variables: `env | grep OIDC`
5. Contact DevOps team if issues persist
