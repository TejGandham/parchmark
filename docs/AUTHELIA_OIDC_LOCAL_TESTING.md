# Authelia OIDC Local Testing Guide

Complete end-to-end testing of ParchMark OIDC authentication locally using Docker Compose with pre-configured Authelia.

---

## Quick Start (5 minutes)

### Prerequisites
- Docker and Docker Compose installed
- ParchMark repository cloned
- Backend and frontend built (images available locally)

### Start Everything

```bash
# From project root
docker compose -f docker-compose.oidc-test.yml up -d

# Wait for services to be healthy (usually 30-60 seconds)
docker compose -f docker-compose.oidc-test.yml ps

# Expected output: all services with "healthy" status
```

### Access Services

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Authelia**: http://localhost:9091
- **API Docs**: http://localhost:8000/docs

### Stop Everything

```bash
docker compose -f docker-compose.oidc-test.yml down

# Remove volumes if you want to reset database
docker compose -f docker-compose.oidc-test.yml down -v
```

---

## Test Users

Pre-configured OIDC users in Authelia (all use same password):

| Username | Email | Password | Notes |
|----------|-------|----------|-------|
| john | john@example.com | password123 | Standard OIDC user |
| jane | jane@example.com | password123 | Standard OIDC user |
| admin | admin@example.com | password123 | Admin user |

### Create Additional Users

Edit `authelia-users-database.yml` to add more users. Generate password hashes with:

```bash
# Generate Argon2id hash for a password
docker run authelia/authelia:latest authelia crypto hash generate argon2id --password yourpassword

# Copy the hash to authelia-users-database.yml
```

---

## Service Architecture

### Docker Compose Setup

```
┌─────────────────────────────────────────────┐
│         Docker Compose Network              │
│     (parchmark_oidc - bridge network)       │
└─────────────────────────────────────────────┘
        │                  │                │
        ▼                  ▼                ▼
    PostgreSQL         Authelia        ParchMark
    (port 5432)      (port 9091)    Backend + Frontend
                                     (port 8000+8080)
```

### Service Details

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| PostgreSQL | 5432 | Docker internal | Database for all services |
| Authelia | 9091 | http://localhost:9091 | OIDC provider |
| Backend | 8000 | http://localhost:8000 | ParchMark API |
| Frontend | 8080 | http://localhost:8080 | ParchMark UI |

---

## Test Scenarios

### Scenario 1: OIDC Login (New User)

**Objective**: Verify OIDC login creates new user automatically

**Steps**:

1. Open http://localhost:8080 in browser
2. Click "Sign In with SSO"
3. Get redirected to Authelia login
4. Enter credentials:
   - Username: `john`
   - Password: `password123`
5. Click "Sign In"
6. Get redirected back to ParchMark notes page
7. Verify you can create a note

**Verification**:

```bash
# Check user was created in database
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db \
  -c "SELECT username, auth_provider, oidc_sub, email FROM users WHERE auth_provider='oidc';"

# Expected output:
# username | auth_provider | oidc_sub |       email
# john     | oidc          | john     | john@example.com
```

**Backend Logs**:

```bash
docker compose -f docker-compose.oidc-test.yml logs backend | grep -i "oidc\|creating\|auto-create"
```

### Scenario 2: OIDC Login (Existing User)

**Objective**: Verify returning OIDC user logs in without duplicate creation

**Steps**:

1. Logout from previous session or use incognito browser
2. Open http://localhost:8080
3. Click "Sign In with SSO"
4. Login with same user (john / password123)
5. Verify no new user created

**Verification**:

```bash
# Count OIDC users
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db \
  -c "SELECT COUNT(*) FROM users WHERE auth_provider='oidc';"

# Should be 1 (or same number as before)
```

### Scenario 3: Local Login Still Works

**Objective**: Verify hybrid auth - local login not broken

**Steps**:

1. Create a local user:
```bash
docker compose -f docker-compose.oidc-test.yml exec backend \
  python scripts/manage_users.py create localuser SecurePassword123
```

2. Open http://localhost:8080
3. Click "Sign In" (local login)
4. Enter: localuser / SecurePassword123
5. Verify access to notes

**Verification**:

```bash
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db \
  -c "SELECT username, auth_provider FROM users WHERE auth_provider='local';"
```

### Scenario 4: Token Refresh

**Objective**: Verify OIDC token refresh works correctly

**Steps**:

1. Login via OIDC (john)
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run:
```javascript
// Check current token
console.log('Token source:', JSON.parse(localStorage.getItem('auth-store')).tokenSource);

// Wait for token refresh (or trigger manually after ~30 mins)
// Token should auto-refresh without re-authentication

// After refresh, token should still work
console.log('After refresh:', JSON.parse(localStorage.getItem('auth-store')).token.substring(0, 50) + '...');
```

5. Create/edit a note - should work without logging in again

**Backend Logs**:

```bash
docker compose -f docker-compose.oidc-test.yml logs backend | grep -i "refresh\|token"
```

### Scenario 5: OIDC Logout

**Objective**: Verify OIDC logout clears session

**Steps**:

1. Login via OIDC
2. Click user menu (top right)
3. Click "Logout"
4. Get redirected to Authelia logout
5. Get redirected back to login page
6. Try accessing notes - should be redirected to login

**Verification**:

```bash
# Check localStorage was cleared
# Open browser DevTools → Application → Local Storage → http://localhost:8080
# Should see empty auth-store or no auth-store

# Check Authelia session was cleared
docker compose -f docker-compose.oidc-test.yml logs authelia | grep -i "logout\|session"
```

### Scenario 6: Mixed Users (Local + OIDC)

**Objective**: Verify system handles both local and OIDC users

**Steps**:

1. Create local user:
```bash
docker compose -f docker-compose.oidc-test.yml exec backend \
  python scripts/manage_users.py create alice MyPassword123
```

2. Test local login (alice / MyPassword123)
3. Create a note
4. Logout
5. Test OIDC login (john / password123)
6. Verify only john's notes are visible
7. Logout and login as alice
8. Verify only alice's notes are visible

**Database Verification**:

```bash
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db \
  -c "SELECT u.username, u.auth_provider, COUNT(n.id) as note_count
      FROM users u LEFT JOIN notes n ON u.id = n.user_id
      GROUP BY u.id, u.username, u.auth_provider;"
```

### Scenario 7: Token Expiration Handling

**Objective**: Verify graceful handling of expired tokens

**Steps**:

1. Login via OIDC
2. Wait for access token to expire (default: 1 hour, but in dev you can modify `ACCESS_TOKEN_EXPIRE_MINUTES` to 1 minute for testing)
3. Try to perform an action (create note)
4. Should auto-refresh or prompt to login

**Quick Test** (without waiting 1 hour):

```bash
# Edit docker-compose.oidc-test.yml and set ACCESS_TOKEN_EXPIRE_MINUTES=1
# Then: docker compose -f docker-compose.oidc-test.yml down && docker compose -f docker-compose.oidc-test.yml up -d

# Wait 1 minute and try to use app
# Token should expire and system should handle gracefully
```

### Scenario 8: OIDC Discovery Endpoint

**Objective**: Verify Authelia OIDC discovery endpoint is accessible

**Steps**:

```bash
# Test discovery endpoint
curl http://localhost:9091/.well-known/openid-configuration | jq .

# Should return:
# {
#   "issuer": "http://localhost:9091",
#   "authorization_endpoint": "http://localhost:9091/authorization",
#   "token_endpoint": "http://localhost:9091/token",
#   "userinfo_endpoint": "http://localhost:9091/userinfo",
#   "jwks_uri": "http://localhost:9091/.well-known/openid-configuration/jwks",
#   "end_session_endpoint": "http://localhost:9091/logout",
#   ...
# }

# Test JWKS endpoint
curl http://localhost:9091/.well-known/openid-configuration/jwks | jq .

# Should return signing keys
```

### Scenario 9: OIDC Client Registration

**Objective**: Verify parchmark-web client is registered in Authelia

**Steps**:

```bash
# Check Authelia logs for client registration
docker compose -f docker-compose.oidc-test.yml logs authelia | grep -i "parchmark"

# Should show client loaded successfully
```

### Scenario 10: API Health Checks

**Objective**: Verify all services are healthy

**Steps**:

```bash
# Check backend health
curl http://localhost:8000/api/health | jq .

# Expected:
# {
#   "status": "healthy",
#   "database": "connected",
#   "service": "ParchMark API",
#   "version": "1.0.0"
# }

# Check Authelia health
curl http://localhost:9091/api/health | jq .

# Should return 200 OK

# Check frontend
curl http://localhost:8080 | head -20

# Should return HTML
```

---

## Debugging

### View Logs

```bash
# All services
docker compose -f docker-compose.oidc-test.yml logs -f

# Specific service
docker compose -f docker-compose.oidc-test.yml logs -f backend
docker compose -f docker-compose.oidc-test.yml logs -f authelia
docker compose -f docker-compose.oidc-test.yml logs -f postgres

# Search for errors
docker compose -f docker-compose.oidc-test.yml logs | grep -i error
```

### Inspect Database

```bash
# Connect to PostgreSQL
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db

# Common queries
# List all users
\c parchmark_db
SELECT id, username, auth_provider, oidc_sub, email, created_at FROM users;

# List notes
SELECT n.id, n.title, u.username, n.created_at FROM notes n JOIN users u ON n.user_id = u.id;

# Check OIDC user details
SELECT * FROM users WHERE auth_provider = 'oidc';

# Exit
\q
```

### Inspect Network

```bash
# Check DNS resolution within containers
docker compose -f docker-compose.oidc-test.yml exec backend \
  ping authelia

# Should resolve to container IP

# Check port connectivity
docker compose -f docker-compose.oidc-test.yml exec backend \
  curl -I http://authelia:9091

# Should return HTTP response
```

### View Service Status

```bash
# Detailed status
docker compose -f docker-compose.oidc-test.yml ps -a

# Inspect specific container
docker inspect parchmark-backend-oidc | jq .[0].State

# Check resource usage
docker stats parchmark-*-oidc
```

---

## Troubleshooting

### "Cannot reach OIDC provider"

**Symptoms**: Backend can't connect to Authelia

**Diagnosis**:
```bash
docker compose -f docker-compose.oidc-test.yml logs backend | grep -i "cannot reach\|connection refused"
```

**Solution**:
1. Verify Authelia is running: `docker compose -f docker-compose.oidc-test.yml ps`
2. Check Authelia health: `curl http://localhost:9091/api/health`
3. Verify network: `docker compose -f docker-compose.oidc-test.yml exec backend ping authelia`
4. Restart Authelia: `docker compose -f docker-compose.oidc-test.yml restart authelia`

### "Invalid client_id"

**Symptoms**: Authelia rejects parchmark-web client

**Diagnosis**:
```bash
docker compose -f docker-compose.oidc-test.yml logs authelia | grep -i "parchmark\|client.*not found"
```

**Solution**:
1. Verify authelia-dev-config.yml has parchmark-web client
2. Check client ID matches: `VITE_OIDC_CLIENT_ID=parchmark-web`
3. Verify in backend env: `OIDC_AUDIENCE=parchmark-web`
4. Restart Authelia: `docker compose -f docker-compose.oidc-test.yml restart authelia`

### "Redirect URI mismatch"

**Symptoms**: "The redirect_uri doesn't match registered redirect_uris"

**Diagnosis**:
```bash
docker compose -f docker-compose.oidc-test.yml logs authelia | grep -i "redirect"
```

**Solution**:
1. Check registered URIs in authelia-dev-config.yml match your testing URL:
   - If testing from http://localhost:5173, must include that URI
   - If testing from http://localhost:8080, must include that URI
   - If testing with 127.0.0.1, must include that variant
2. All redirect URIs must be exact matches (including protocol, host, port, path)

### "OIDC configuration not found"

**Symptoms**: Frontend can't access discovery endpoint

**Diagnosis**:
```bash
curl http://localhost:9091/.well-known/openid-configuration
```

**Solution**:
1. Verify Authelia is running and healthy
2. Check `VITE_OIDC_ISSUER_URL=http://localhost:9091` is correct
3. Verify no firewalls blocking port 9091
4. Check Authelia logs: `docker compose -f docker-compose.oidc-test.yml logs authelia`

### Database not initializing

**Symptoms**: "ERROR: Unable to connect to database"

**Diagnosis**:
```bash
docker compose -f docker-compose.oidc-test.yml logs postgres
docker compose -f docker-compose.oidc-test.yml ps postgres
```

**Solution**:
1. Verify PostgreSQL is running: `docker compose -f docker-compose.oidc-test.yml ps`
2. Check database credentials match docker-compose.oidc-test.yml
3. Check DATABASE_URL in backend env
4. Reset database: `docker compose -f docker-compose.oidc-test.yml down -v && docker compose -f docker-compose.oidc-test.yml up -d`

### User not being created on OIDC login

**Symptoms**: Login succeeds but user not in database

**Diagnosis**:
```bash
docker compose -f docker-compose.oidc-test.yml logs backend | grep -i "auto-create\|creating user"
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db \
  -c "SELECT * FROM users WHERE auth_provider='oidc';"
```

**Solution**:
1. Verify backend receives OIDC token: check logs for "Validating OIDC token"
2. Verify token validation succeeds: check for "OIDC token validation success"
3. Check database permissions: user creation queries should succeed
4. Verify `OIDC_USERNAME_CLAIM=preferred_username` is set correctly

---

## Performance Testing

### Load Testing OIDC Token Validation

```bash
# Test backend health under load
docker compose -f docker-compose.oidc-test.yml exec backend \
  uv run pytest tests/unit/auth/test_oidc_validator.py -v

# Measure token validation performance
docker compose -f docker-compose.oidc-test.yml logs backend | grep "latency"
```

### Monitor Resource Usage

```bash
# Watch container stats
docker stats parchmark-*-oidc --no-stream

# Expected for idle services:
# - Backend: <100MB memory, <5% CPU
# - Authelia: <100MB memory, <5% CPU
# - PostgreSQL: 50-150MB memory, <5% CPU
```

### Token Refresh Performance

1. Login via OIDC
2. Monitor refresh endpoint:
```bash
# Watch token refresh requests
docker compose -f docker-compose.oidc-test.yml logs backend -f | grep "refresh"

# Should complete in <100ms
```

---

## Production Testing

Before deploying to production, use this local setup to verify:

- [ ] All 10 test scenarios pass
- [ ] No errors in logs
- [ ] Database queries execute correctly
- [ ] Token expiration/refresh works
- [ ] Logout clears session properly
- [ ] Mixed local/OIDC users work together
- [ ] Health endpoints return 200
- [ ] OIDC discovery endpoint works
- [ ] JWKS endpoint serves valid keys
- [ ] API accepts both local and OIDC tokens

---

## Cleanup

### Stop Services

```bash
docker compose -f docker-compose.oidc-test.yml down
```

### Remove Data

```bash
# Remove volumes (database data)
docker compose -f docker-compose.oidc-test.yml down -v

# Remove containers and networks
docker compose -f docker-compose.oidc-test.yml down --remove-orphans
```

### Reset Everything

```bash
# Complete reset (remove containers, volumes, networks)
docker compose -f docker-compose.oidc-test.yml down -v --remove-orphans

# Rebuild containers (if Dockerfile changed)
docker compose -f docker-compose.oidc-test.yml build --no-cache

# Start fresh
docker compose -f docker-compose.oidc-test.yml up -d
```

---

## Quick Reference

```bash
# Quick start
docker compose -f docker-compose.oidc-test.yml up -d

# View status
docker compose -f docker-compose.oidc-test.yml ps

# View logs
docker compose -f docker-compose.oidc-test.yml logs -f

# Run tests
docker compose -f docker-compose.oidc-test.yml exec backend make test-backend-oidc

# Create local user
docker compose -f docker-compose.oidc-test.yml exec backend \
  python scripts/manage_users.py create testuser testpass

# Access database
docker compose -f docker-compose.oidc-test.yml exec postgres psql \
  -U parchmark_user -d parchmark_db

# Stop everything
docker compose -f docker-compose.oidc-test.yml down

# Stop and reset
docker compose -f docker-compose.oidc-test.yml down -v
```

---

## Support

For issues:

1. **Check logs**: `docker compose -f docker-compose.oidc-test.yml logs`
2. **Verify services**: `docker compose -f docker-compose.oidc-test.yml ps`
3. **Test endpoints**: `curl http://localhost:8000/api/health`
4. **Review documentation**: `docs/AUTHELIA_OIDC_*.md`

---

## See Also

- **AUTHELIA_OIDC_QUICKSTART.md** - 10-minute setup
- **AUTHELIA_OIDC_CONFIG_EXAMPLE.md** - Authelia configuration
- **AUTHELIA_OIDC_SMOKE_TEST.md** - Comprehensive test scenarios
- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Problem diagnosis
- **AUTHELIA_OIDC_MONITORING.md** - Production monitoring
