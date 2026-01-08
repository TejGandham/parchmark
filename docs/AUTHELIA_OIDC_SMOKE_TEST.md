# Authelia OIDC Smoke Test Guide

This guide provides step-by-step instructions for testing the Authelia OIDC integration end-to-end.

## Prerequisites

- Authelia configured and running at `https://auth.engen.tech`
- ParchMark backend running at `https://assets-api.engen.tech` or `http://localhost:8000`
- ParchMark frontend running at `https://notes.engen.tech` or `http://localhost:5173`
- OIDC client "parchmark-web" registered in Authelia

## Pre-Test Checklist

Before running smoke tests, verify:

```bash
# 1. Backend health endpoint includes database
curl -X GET https://assets-api.engen.tech/api/health
# Expected response:
# {"status": "healthy", "database": "connected", "service": "ParchMark API", "version": "1.0.0"}

# 2. Authelia OIDC discovery endpoint
curl -X GET https://auth.engen.tech/.well-known/openid-configuration
# Should return OIDC configuration

# 3. Frontend loads
curl -X GET https://notes.engen.tech/
# Should return HTML with login form

# 4. CORS headers are set correctly
curl -I -X GET https://assets-api.engen.tech/api/health -H "Origin: https://notes.engen.tech"
# Should have Access-Control-Allow-Origin header
```

## Test Scenarios

### Scenario 1: Local Login Still Works

**Steps**:
1. Navigate to login page: `https://notes.engen.tech/login` (or `http://localhost:5173/login`)
2. Enter local username and password
3. Click "Sign In" button

**Expected Results**:
- Successfully authenticated
- Redirected to `/notes` page
- Auth store shows `tokenSource: 'local'`
- Notes list displays (even if empty)

**Verification**:
```bash
# Check localStorage
localStorage.getItem('auth-store')
# Should contain: "tokenSource":"local"
```

### Scenario 2: SSO Button Displays

**Steps**:
1. Navigate to login page
2. Look for "Sign In with SSO" button below the local login form

**Expected Results**:
- Button is visible
- Button is distinct from "Sign In" button (different color)
- Divider with "OR" text separates login methods

### Scenario 3: OIDC Login Flow - New User

**Prerequisites**:
- Test user doesn't exist in Authelia
- Authelia is configured with test users

**Steps**:
1. Navigate to login page
2. Click "Sign In with SSO" button
3. Get redirected to Authelia login
4. Enter Authelia credentials (create test user if needed)
5. Authorize ParchMark to access your profile
6. Get redirected back to app

**Expected Results**:
- Redirected to `/notes` page
- User is authenticated with OIDC token
- User profile displays in header
- Backend auto-created user in database

**Verification**:
```bash
# Check auth store
localStorage.getItem('auth-store')
# Should contain: "tokenSource":"oidc"

# Check backend database
psql postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SELECT * FROM users WHERE auth_provider='oidc';
# Should show newly created user with oidc_sub populated
```

### Scenario 4: OIDC Login Flow - Existing User

**Prerequisites**:
- OIDC user already created from Scenario 3

**Steps**:
1. Logout from session
2. Click "Sign In with SSO" button
3. Login with same Authelia account
4. Get redirected back to app

**Expected Results**:
- Successfully authenticated
- Same user profile loads
- Auth store shows same user data

### Scenario 5: Logout from OIDC Session

**Prerequisites**:
- Logged in via OIDC

**Steps**:
1. Click user profile dropdown (top right)
2. Click "Logout" button
3. Observe redirect behavior

**Expected Results**:
- Logged out from ParchMark (auth store cleared)
- Redirected to login page
- OIDC session may also be cleared at Authelia

**Verification**:
```bash
# Check localStorage is cleared
localStorage.getItem('auth-store')
# Should return: null or empty object
```

### Scenario 6: Token Refresh with OIDC

**Prerequisites**:
- Logged in via OIDC
- Authelia token expiration is soon

**Steps**:
1. Stay logged in and wait for token expiration monitor
2. Check browser console for token refresh attempts
3. Perform action that requires API call (view notes)

**Expected Results**:
- Token refresh happens silently
- User remains authenticated
- No interruption to user experience

**Verification**:
```bash
# Check console logs
console.log('Token refresh attempted at', new Date().toISOString())
```

### Scenario 7: Create/Edit Note as OIDC User

**Prerequisites**:
- Logged in via OIDC

**Steps**:
1. Click "New Note" button
2. Enter note title
3. Add markdown content
4. Click Save

**Expected Results**:
- Note is created successfully
- Note appears in sidebar
- Note contains user's content

**API Request Verification**:
```bash
# Check network tab
# POST /api/notes/ should have:
# Headers: Authorization: Bearer <oidc_token>
# Body: {"title": "...", "content": "..."}
```

### Scenario 8: Mixed Auth - Local and OIDC

**Prerequisites**:
- System has both local and OIDC users

**Steps**:
1. Test local user login with local credentials
2. Logout
3. Test OIDC user login with SSO
4. Logout
5. Test different local user

**Expected Results**:
- Each login uses appropriate auth method
- Users only see their own notes
- No crosstalk between auth methods

### Scenario 9: 401 Error Handling

**Prerequisites**:
- Logged in via OIDC

**Steps**:
1. Let OIDC token expire (wait or manipulate time)
2. Perform API request (load notes, create note)

**Expected Results**:
- Backend returns 401 Unauthorized
- Frontend automatically attempts token refresh
- If refresh fails, user is logged out
- User is redirected to login page

**API Request Verification**:
```bash
# Check network tab for:
# 1. Initial request with expired token → 401
# 2. Refresh token request (if applicable)
# 3. Logout if refresh fails
```

### Scenario 10: OIDC Callback Error Handling

**Prerequisites**:
- Authelia OIDC callback URL misconfigured

**Steps**:
1. Click "Sign In with SSO"
2. Login to Authelia
3. Authelia fails to redirect back

**Expected Results**:
- Error message displayed
- User can retry login
- No application crash

## Backend Health Checks

Run these commands to verify backend OIDC readiness:

```bash
# 1. Verify OIDC configuration is loaded
docker logs parchmark-backend | grep -i "OIDC"
# Should show OIDC_ISSUER_URL, OIDC_AUDIENCE, etc.

# 2. Check API health with database
curl -X GET http://localhost:8000/api/health
# Response should include: "database": "connected"

# 3. Verify JWKS endpoint is reachable
curl -X GET https://auth.engen.tech/.well-known/openid-configuration/jwks
# Should return keys array

# 4. Check backend logs for OIDC validation
docker logs parchmark-backend | grep -i "oidc\|validation"
```

## Frontend Health Checks

Open browser developer tools and run:

```javascript
// 1. Check OIDC configuration
console.log('VITE_OIDC_ISSUER_URL:', import.meta.env.VITE_OIDC_ISSUER_URL);
console.log('VITE_OIDC_CLIENT_ID:', import.meta.env.VITE_OIDC_CLIENT_ID);

// 2. Check auth store state
console.log('Auth Store:', localStorage.getItem('auth-store'));

// 3. Check OIDC user manager initialization
console.log('UserManager initialized:', !!window.userManager);

// 4. Verify SSO button exists
console.log('SSO Button:', document.querySelector('[data-testid="sso-login-button"]'));
```

## Performance Checks

### JWKS Caching

1. Login via OIDC
2. Make multiple API requests
3. Check that JWKS is only fetched once (should be cached)

```bash
# Check backend logs
docker logs parchmark-backend | grep -c "Fetching JWKS"
# Should be 1 or 2 (not per-request)
```

### Token Validation Performance

1. Create 10 requests rapidly
2. Monitor backend response times

```bash
# Expected: < 50ms per request (JWKS cached)
# JWKS fetch adds ~100-200ms first time, then uses cache
```

## Troubleshooting

### "OIDC configuration not found"

**Check**:
- Verify `VITE_OIDC_ISSUER_URL` is set
- Verify Authelia OIDC discovery endpoint is accessible
- Check browser console for actual error

```javascript
fetch('https://auth.engen.tech/.well-known/openid-configuration')
  .then(r => r.json())
  .then(console.log)
```

### "Redirect URI mismatch"

**Check**:
- Verify `VITE_OIDC_REDIRECT_URI` matches Authelia config exactly
- Check for protocol (http vs https) differences
- Check for port number differences
- Verify trailing slashes match

### Backend token validation fails

**Check**:
```bash
# Verify OIDC_AUDIENCE matches Authelia client
echo $OIDC_AUDIENCE

# Verify OIDC_ISSUER_URL is correct
echo $OIDC_ISSUER_URL

# Check backend logs for validation errors
docker logs parchmark-backend | grep -i "token\|validation"
```

### User not auto-created

**Check**:
```bash
# Verify database schema has new columns
psql postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
\d users
# Should show: oidc_sub, email, auth_provider columns

# Check backend logs
docker logs parchmark-backend | grep -i "auto-create\|user created"
```

## Test Report Template

```markdown
# OIDC Smoke Test Report

**Date**: YYYY-MM-DD
**Environment**: Development/Production
**Tester**: Name

## Results

- [ ] Scenario 1: Local Login Works
- [ ] Scenario 2: SSO Button Displays
- [ ] Scenario 3: New OIDC User Creation
- [ ] Scenario 4: Existing OIDC User Login
- [ ] Scenario 5: OIDC Logout
- [ ] Scenario 6: Token Refresh
- [ ] Scenario 7: Note CRUD as OIDC User
- [ ] Scenario 8: Mixed Auth Works
- [ ] Scenario 9: 401 Error Handling
- [ ] Scenario 10: Callback Error Handling

## Issues Found

1. Issue: ...
   Severity: High/Medium/Low
   Steps to reproduce: ...
   Expected: ...
   Actual: ...

## Sign-Off

- [ ] All scenarios passed
- [ ] No critical issues found
- [ ] Ready for production deployment

Tester: ___________  Date: __________
```

## Automated Test Commands

Run these Makefile commands for automated testing:

```bash
# Test both UI and backend
make test-all

# Test only backend (includes OIDC tests)
make test-backend-all

# Test only frontend
make test-ui-all

# View test coverage
open backend/htmlcov/index.html
open ui/coverage/index.html
```
