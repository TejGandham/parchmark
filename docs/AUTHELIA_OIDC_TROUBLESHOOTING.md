# Authelia OIDC Troubleshooting Guide

This guide helps diagnose and resolve common issues with Authelia OIDC integration.

## Table of Contents
1. [Frontend Issues](#frontend-issues)
2. [Backend Issues](#backend-issues)
3. [Authentication Flow Issues](#authentication-flow-issues)
4. [Token Issues](#token-issues)
5. [Database Issues](#database-issues)
6. [Network Issues](#network-issues)
7. [Debugging Tips](#debugging-tips)

---

## Frontend Issues

### Issue: "Sign In with SSO" button not appearing

**Symptoms**:
- Login page displays but SSO button is missing
- No divider or "OR" text visible

**Root Causes**:
1. Frontend environment variables not set
2. OIDC configuration not loading
3. Component rendering error

**Diagnostic Steps**:
```javascript
// Open browser console and run:
console.log('VITE_OIDC_ISSUER_URL:', import.meta.env.VITE_OIDC_ISSUER_URL);
console.log('VITE_OIDC_CLIENT_ID:', import.meta.env.VITE_OIDC_CLIENT_ID);
console.log('VITE_OIDC_REDIRECT_URI:', import.meta.env.VITE_OIDC_REDIRECT_URI);

// Check if component is mounted
console.log('LoginForm rendered:', document.querySelector('[data-testid="sso-login-button"]'));
```

**Solutions**:
1. Verify `.env` file has all OIDC variables:
   ```bash
   cat ui/.env
   # Should include VITE_OIDC_* variables
   ```

2. Rebuild frontend if env vars changed:
   ```bash
   cd ui
   npm run build
   # Then restart frontend server or redeploy
   ```

3. Clear browser cache:
   ```javascript
   // In console
   location.reload(true);
   ```

4. Check for console errors:
   - Open DevTools → Console tab
   - Look for red error messages
   - Check for CORS errors

---

### Issue: SSO button click does nothing

**Symptoms**:
- Button is visible and clickable
- Clicking does nothing (no redirect to Authelia)
- No error in console

**Root Causes**:
1. OIDC UserManager not initialized
2. Network request blocked
3. JavaScript error in click handler

**Diagnostic Steps**:
```javascript
// Check UserManager
console.log('UserManager:', window.userManager);

// Check network in DevTools
// Network tab → Look for requests to auth.engen.tech

// Check for errors
console.log('Auth store:', useAuthStore.getState());
```

**Solutions**:
1. Verify Authelia is reachable:
   ```bash
   curl -I https://auth.engen.tech/.well-known/openid-configuration
   # Should return 200 OK
   ```

2. Check CORS in browser:
   - DevTools → Network tab
   - Click SSO button
   - Look for requests to `auth.engen.tech`
   - Check response headers for `Access-Control-Allow-Origin`

3. Check browser console for errors:
   ```javascript
   // Test UserManager directly
   await userManager.signinRedirect();
   ```

---

### Issue: Redirected to SSO but nothing happens

**Symptoms**:
- Redirected to Authelia login
- Login successful
- No redirect back to app
- Browser stuck on Authelia

**Root Causes**:
1. Redirect URI mismatch
2. OIDC client not registered correctly
3. Network issue

**Diagnostic Steps**:
```javascript
// Check configured redirect URI
console.log('VITE_OIDC_REDIRECT_URI:', import.meta.env.VITE_OIDC_REDIRECT_URI);

// Check current URL
console.log('Current URL:', window.location.href);
```

**Solutions**:
1. Verify redirect URI matches Authelia config:
   ```bash
   # In Authelia config, check:
   # redirect_uris:
   #   - "https://notes.engen.tech/oidc/callback"

   # Must match EXACTLY with:
   echo $VITE_OIDC_REDIRECT_URI
   ```

2. Check for protocol/port mismatches:
   - `http` vs `https`
   - Port 80 vs 443 vs custom port
   - Trailing slash differences

3. Verify Authelia can redirect:
   - Check Authelia logs: `docker logs authelia`
   - Look for redirect errors
   - Check firewall rules

---

### Issue: "Invalid client_id" error from Authelia

**Symptoms**:
- Error message displayed on Authelia login
- Cannot proceed with authentication

**Root Causes**:
1. `VITE_OIDC_CLIENT_ID` doesn't match Authelia config
2. OIDC client not registered in Authelia
3. Case sensitivity issue

**Solutions**:
1. Verify client ID in Authelia:
   ```bash
   # Check authelia configuration.yml
   grep -A 20 "parchmark-web" authelia/configuration.yml
   # Should show "parchmark-web" OIDC client configuration
   ```

2. Verify environment variable:
   ```bash
   echo $VITE_OIDC_CLIENT_ID
   # Should output: parchmark-web (exact match, case-sensitive)
   ```

3. Restart Authelia if config changed:
   ```bash
   docker restart authelia
   ```

---

## Backend Issues

### Issue: Backend health endpoint fails

**Symptoms**:
- `GET /api/health` returns error
- `GET /api/health` doesn't include database status

**Root Causes**:
1. Database not connected
2. OIDC configuration issue
3. Backend not started

**Diagnostic Steps**:
```bash
# Check backend is running
curl -X GET http://localhost:8000/api/health

# Check backend logs
docker logs parchmark-backend | tail -50

# Check environment variables
docker exec parchmark-backend env | grep -i oidc
```

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   # Should show postgres container running
   ```

2. Check backend environment:
   ```bash
   docker exec parchmark-backend python -c "import os; print(os.getenv('OIDC_ISSUER_URL'))"
   ```

3. Restart backend:
   ```bash
   docker restart parchmark-backend
   ```

---

### Issue: OIDC token validation fails

**Symptoms**:
- Login successful in frontend
- API calls return 401 Unauthorized
- Backend logs show "Token validation failed"

**Root Causes**:
1. `OIDC_ISSUER_URL` mismatch
2. `OIDC_AUDIENCE` mismatch
3. JWKS fetch failure
4. Token expired

**Diagnostic Steps**:
```bash
# Check backend configuration
docker exec parchmark-backend env | grep -E "OIDC_ISSUER_URL|OIDC_AUDIENCE|OIDC_USERNAME_CLAIM"

# Check backend can reach JWKS
docker exec parchmark-backend curl -I "https://auth.engen.tech/.well-known/openid-configuration"

# Check backend logs for validation errors
docker logs parchmark-backend | grep -i "oidc\|validation"
```

**Solutions**:
1. Verify OIDC configuration matches Authelia:
   ```bash
   # Authelia OIDC issuer
   curl https://auth.engen.tech/.well-known/openid-configuration | jq .issuer

   # Should match:
   docker exec parchmark-backend python -c "import os; print(os.getenv('OIDC_ISSUER_URL'))"
   ```

2. Verify audience matches:
   ```bash
   # Check OIDC_AUDIENCE in backend
   docker exec parchmark-backend python -c "import os; print(os.getenv('OIDC_AUDIENCE'))"

   # Should be "parchmark-web" (or whatever registered in Authelia)
   ```

3. Test JWKS access:
   ```bash
   # From backend container
   docker exec parchmark-backend curl -I "https://auth.engen.tech/.well-known/openid-configuration/jwks"
   # Should return 200 OK
   ```

---

### Issue: User auto-creation fails

**Symptoms**:
- OIDC login successful in UI
- User not created in database
- Backend logs show user creation error

**Root Causes**:
1. Database schema not migrated
2. `OIDC_USERNAME_CLAIM` invalid
3. Duplicate username from Authelia

**Diagnostic Steps**:
```bash
# Check database schema
docker exec parchmark-backend python -c "
from app.database.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
cols = [col['name'] for col in inspector.get_columns('users')]
print('User columns:', cols)
"

# Check backend logs
docker logs parchmark-backend | grep -i "create\|user"
```

**Solutions**:
1. Verify database migration applied:
   ```bash
   # Check users table schema
   docker exec $(docker ps -q -f "ancestor=postgres") psql -U parchmark_user -d parchmark_db -c "\d users"

   # Should show columns: oidc_sub, email, auth_provider
   ```

2. Verify `OIDC_USERNAME_CLAIM`:
   ```bash
   docker exec parchmark-backend python -c "import os; print(os.getenv('OIDC_USERNAME_CLAIM'))"
   # Should be "preferred_username"
   ```

3. Check Authelia token includes the claim:
   ```javascript
   // After OIDC login, check token
   const user = await userManager.getUser();
   console.log('OIDC profile:', user.profile);
   // Should show preferred_username or email
   ```

---

## Authentication Flow Issues

### Issue: Local login broken after OIDC deployment

**Symptoms**:
- Local login fails with 401 error
- OIDC login works
- Existing local users cannot login

**Root Causes**:
1. Auth dependency not handling local JWT correctly
2. Configuration set to OIDC-only mode
3. Local JWT validation broken

**Diagnostic Steps**:
```bash
# Test local JWT generation
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Check response includes access_token
```

**Solutions**:
1. Verify `AUTH_MODE` is set to "hybrid":
   ```bash
   docker exec parchmark-backend python -c "import os; print(os.getenv('AUTH_MODE'))"
   # Should output: hybrid
   ```

2. Test with local credentials:
   ```bash
   # Create test user
   docker exec parchmark-backend python scripts/manage_users.py create testuser password123

   # Try local login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"password123"}'
   ```

3. Check dependencies haven't been modified:
   ```bash
   docker exec parchmark-backend python -c "from app.auth.dependencies import get_current_user; print('OK')"
   ```

---

### Issue: Both local and OIDC users can't login

**Symptoms**:
- All login attempts fail with 401
- Frontend shows "Could not validate credentials"
- Backend logs don't show errors

**Root Causes**:
1. Backend not starting
2. Authorization header not sent
3. Token being sent but validation fails

**Diagnostic Steps**:
```bash
# Check backend is responding
curl -X GET http://localhost:8000/health

# Check auth endpoint exists
curl -X POST http://localhost:8000/api/auth/login -v

# Check for auth middleware errors
docker logs parchmark-backend | tail -50
```

**Solutions**:
1. Restart backend:
   ```bash
   docker restart parchmark-backend
   docker logs parchmark-backend | tail -20
   ```

2. Verify auth dependencies are loaded:
   ```bash
   docker exec parchmark-backend python -c "from app.auth import dependencies; print('OK')"
   ```

3. Test with proper headers:
   ```bash
   # Make sure Bearer token is sent
   curl -X GET http://localhost:8000/api/notes \
     -H "Authorization: Bearer <your_token_here>"
   ```

---

## Token Issues

### Issue: Token refresh fails

**Symptoms**:
- After 30+ minutes, API returns 401
- User is logged out unexpectedly
- Token refresh not working

**Root Causes**:
1. Refresh token expired
2. OIDC refresh not configured
3. Authelia refresh endpoint issue

**Diagnostic Steps**:
```javascript
// Check token expiration
const user = await userManager.getUser();
console.log('Token expiration:', user.expires_at);
console.log('Current time:', Date.now() / 1000);

// Check refresh token exists
console.log('Has refresh token:', !!user.refresh_token);
```

**Solutions**:
1. For OIDC users, verify Authelia refresh token:
   - Authelia must issue refresh tokens
   - Check Authelia config: `grant_types: "authorization_code", "refresh_token"`

2. For local users, refresh endpoint should work:
   ```bash
   curl -X POST http://localhost:8000/api/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"<token>"}'
   ```

3. Manual re-login if refresh fails:
   - User should be prompted to login again
   - SSO or local login option available

---

### Issue: "Token expired" error immediately after login

**Symptoms**:
- Login successful
- Redirected to notes page
- Immediately shows "Token expired" and logs out
- Happens within seconds of login

**Root Causes**:
1. System clock skew between frontend/backend/Authelia
2. Token expiration set to very short duration
3. Token validation not accounting for clock skew

**Diagnostic Steps**:
```bash
# Check system time on all servers
date

# Check Authelia token expiration
docker logs authelia | grep -i "exp"

# Check backend token validation
docker logs parchmark-backend | grep -i "expired"
```

**Solutions**:
1. Sync system clocks:
   ```bash
   # On all servers
   sudo timedatectl set-ntp true
   ```

2. Adjust token expiration in Authelia:
   - Increase ACCESS_TOKEN_EXPIRE_MINUTES to 60+
   - Restart Authelia

3. Check clock skew protection:
   - Backend has 10-second buffer
   - Frontend has 60-second warning before logout
   - Verify this is working: `docker logs parchmark-backend | grep -i "skew"`

---

## Database Issues

### Issue: "User not found" error despite successful OIDC login

**Symptoms**:
- OIDC login successful in UI
- User created in database (can be verified)
- API calls return "user not found"

**Root Causes**:
1. User lookup using wrong field
2. OIDC_SUB not being set correctly
3. Database transaction not committed

**Diagnostic Steps**:
```bash
# Check database directly
docker exec postgres psql -U parchmark_user -d parchmark_db -c "SELECT * FROM users WHERE auth_provider='oidc';"

# Check oidc_sub values
docker exec postgres psql -U parchmark_user -d parchmark_db -c "SELECT username, oidc_sub, auth_provider FROM users;"
```

**Solutions**:
1. Verify user was created:
   ```bash
   # Check count of OIDC users
   docker exec postgres psql -U parchmark_user -d parchmark_db -c "SELECT COUNT(*) FROM users WHERE auth_provider='oidc';"
   ```

2. Verify oidc_sub is set:
   ```bash
   docker exec postgres psql -U parchmark_user -d parchmark_db -c "SELECT oidc_sub FROM users WHERE auth_provider='oidc' LIMIT 1;"
   # Should not be NULL
   ```

3. Check backend user lookup:
   ```bash
   # In backend, the dependency should query by oidc_sub
   docker exec parchmark-backend grep -n "oidc_sub" app/auth/dependencies.py
   ```

---

### Issue: "Duplicate key value violates unique constraint" on oidc_sub

**Symptoms**:
- User creation fails
- Error message mentions unique constraint on oidc_sub
- Only happens for OIDC users

**Root Causes**:
1. Same OIDC user logged in twice simultaneously
2. OIDC_SUB collision (very unlikely)
3. Database data corrupted

**Solutions**:
1. Check for duplicate entries:
   ```bash
   docker exec postgres psql -U parchmark_user -d parchmark_db -c "
   SELECT oidc_sub, COUNT(*)
   FROM users
   WHERE oidc_sub IS NOT NULL
   GROUP BY oidc_sub
   HAVING COUNT(*) > 1;"
   ```

2. If duplicates found, delete one:
   ```bash
   docker exec postgres psql -U parchmark_user -d parchmark_db -c "
   DELETE FROM users
   WHERE id IN (
     SELECT id FROM users
     WHERE oidc_sub = 'duplicate_sub'
     LIMIT 1
   );"
   ```

3. Verify constraint:
   ```bash
   docker exec postgres psql -U parchmark_user -d parchmark_db -c "\d users" | grep -i oidc_sub
   ```

---

## Network Issues

### Issue: "Cannot reach OIDC provider"

**Symptoms**:
- Backend logs show connection errors to Authelia
- JWKS fetch failing
- OIDC login fails immediately

**Diagnostic Steps**:
```bash
# From backend container
docker exec parchmark-backend curl -v https://auth.engen.tech/.well-known/openid-configuration

# Check DNS resolution
docker exec parchmark-backend nslookup auth.engen.tech

# Check network connectivity
docker exec parchmark-backend ping auth.engen.tech
```

**Solutions**:
1. Verify DNS:
   ```bash
   # Check if auth.engen.tech resolves
   nslookup auth.engen.tech
   # Should return IP address
   ```

2. Check firewall:
   ```bash
   # Test port 443 (HTTPS)
   docker exec parchmark-backend nc -zv auth.engen.tech 443
   ```

3. Verify TLS certificate:
   ```bash
   # Check if certificate is valid
   docker exec parchmark-backend curl -I https://auth.engen.tech/
   # Should return 2xx status
   ```

4. Check routing:
   ```bash
   # From backend host
   traceroute auth.engen.tech
   ```

---

### Issue: CORS error when calling API

**Symptoms**:
- Browser console shows CORS error
- Preflight request (OPTIONS) fails
- API request blocked

**Root Causes**:
1. `ALLOWED_ORIGINS` doesn't include frontend
2. CORS headers not set correctly
3. Nginx proxy not forwarding CORS headers

**Diagnostic Steps**:
```bash
# Check ALLOWED_ORIGINS
docker exec parchmark-backend python -c "import os; print(os.getenv('ALLOWED_ORIGINS'))"

# Make preflight request
curl -i -X OPTIONS https://assets-api.engen.tech/api/notes \
  -H "Origin: https://notes.engen.tech" \
  -H "Access-Control-Request-Method: GET"
```

**Solutions**:
1. Verify ALLOWED_ORIGINS includes frontend:
   ```bash
   # Should include https://notes.engen.tech
   echo $ALLOWED_ORIGINS | grep "notes.engen.tech"
   ```

2. Restart backend if config changed:
   ```bash
   docker restart parchmark-backend
   ```

3. Check Nginx proxy configuration:
   ```bash
   # Nginx should forward CORS headers
   grep -i "access-control" /etc/nginx/sites-enabled/parchmark-api.conf
   ```

---

## Debugging Tips

### Enable Verbose Logging

**Backend**:
```bash
# Set logging level
docker exec parchmark-backend python -c "
import logging
logging.getLogger('app.auth').setLevel(logging.DEBUG)
print('Debug logging enabled')
"
```

**Frontend**:
```javascript
// In browser console
localStorage.debug = 'app:*';
window.location.reload();
```

### Inspect Network Requests

**Browser DevTools**:
1. Open DevTools (F12)
2. Go to Network tab
3. Click SSO button
4. Look for requests to:
   - `auth.engen.tech` (OIDC flow)
   - `assets-api.engen.tech` (API calls)
5. Check response headers and body

**Backend Logs**:
```bash
docker logs -f parchmark-backend | grep -i "auth\|oidc"
```

### Test JWKS Directly

```bash
# Test JWKS endpoint
curl https://auth.engen.tech/.well-known/openid-configuration/jwks | jq .

# Verify public keys are present
curl https://auth.engen.tech/.well-known/openid-configuration/jwks | jq '.keys | length'
```

### Decode JWT Token

```javascript
// Decode token without verification (frontend only)
function decodeJWT(token) {
  const parts = token.split('.');
  const payload = JSON.parse(atob(parts[1]));
  return payload;
}

// Usage
const user = await userManager.getUser();
const decoded = decodeJWT(user.access_token);
console.log('Token payload:', decoded);
```

---

## Getting Help

If you've tried these solutions and still have issues:

1. **Check Logs**:
   - Backend: `docker logs parchmark-backend`
   - Authelia: `docker logs authelia`
   - Frontend: Browser DevTools → Console

2. **Verify Configuration**:
   - Run through `AUTHELIA_OIDC_DEPLOYMENT.md` checklist
   - Verify all environment variables
   - Check Authelia OIDC client configuration

3. **Run Smoke Tests**:
   - Follow `AUTHELIA_OIDC_SMOKE_TEST.md`
   - Verify each scenario step-by-step

4. **Contact Support**:
   - Provide error logs
   - Provide configuration (without secrets)
   - Provide steps to reproduce
