# Authelia OIDC Quick Start Guide

Get Authelia OIDC working in 10 minutes.

## Prerequisites

- Docker and Docker Compose running
- ParchMark repository cloned
- Basic familiarity with environment variables

## Step 1: Authelia Configuration (2 minutes)

Add ParchMark OIDC client to `authelia/configuration.yml`:

```yaml
identity_providers:
  oidc:
    clients:
      - id: parchmark-web
        description: ParchMark
        public: true
        redirect_uris:
          - http://localhost:5173/oidc/callback
        scopes:
          - openid
          - profile
          - email
        grant_types:
          - authorization_code
        response_types:
          - code
        require_pkce: true
        pkce_challenge_method: S256
```

Restart Authelia:
```bash
docker restart authelia
docker logs authelia | grep -i parchmark
```

## Step 2: Backend Configuration (2 minutes)

Create/update `backend/.env`:

```bash
# Existing variables (keep them)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key
# ... other vars ...

# New OIDC variables
AUTH_MODE=hybrid
OIDC_ISSUER_URL=http://localhost:9091  # or your Authelia URL
OIDC_AUDIENCE=parchmark-web
OIDC_USERNAME_CLAIM=preferred_username
```

## Step 3: Frontend Configuration (2 minutes)

Create/update `ui/.env`:

```bash
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60
VITE_OIDC_ISSUER_URL=http://localhost:9091  # or your Authelia URL
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=http://localhost:5173/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=http://localhost:5173/login
```

## Step 4: Start Services (2 minutes)

```bash
# Terminal 1: PostgreSQL
make docker-dev

# Terminal 2: Backend
make dev-backend

# Terminal 3: Frontend
make dev-ui

# Terminal 4: Monitor Authelia
docker logs -f authelia
```

## Step 5: Test (2 minutes)

Open http://localhost:5173/login in browser

### Test 1: Local Login
1. Click "Sign In" (local login)
2. Enter local credentials
3. Should see notes page

### Test 2: OIDC Login
1. Click "Sign In with SSO"
2. Get redirected to Authelia
3. Login with Authelia credentials
4. Get redirected back to notes
5. New user should be created in database

### Test 3: Verify Database
```bash
docker exec $(docker ps -q -f "ancestor=postgres") \
  psql -U parchmark_user -d parchmark_db -c \
  "SELECT username, auth_provider, oidc_sub FROM users;"
```

Should show:
- Local user with auth_provider='local'
- OIDC user with auth_provider='oidc' and oidc_sub populated

## Troubleshooting

### "OIDC configuration not found"
```bash
# Check discovery endpoint
curl http://localhost:9091/.well-known/openid-configuration

# Should return JSON with issuer, token_endpoint, etc.
```

### "Invalid client_id"
```bash
# Verify OIDC_AUDIENCE matches Authelia config
docker logs authelia | grep -i "parchmark-web"

# Check backend env
docker exec parchmark-backend env | grep OIDC
```

### "Cannot reach OIDC provider"
```bash
# From backend container
docker exec parchmark-backend curl -I http://authelia:9091

# Should return 200/3xx, not connection refused
```

### User not created
```bash
# Check database schema
docker exec $(docker ps -q -f "ancestor=postgres") \
  psql -U parchmark_user -d parchmark_db -c "\d users"

# Should show: oidc_sub, email, auth_provider columns
```

## Next Steps

1. **Run full test suite**:
   ```bash
   make test-all
   make test-backend-oidc
   make test-ui-oidc
   ```

2. **Review documentation**:
   - `AUTHELIA_OIDC_ENV.md` - Environment variables
   - `AUTHELIA_OIDC_IMPLEMENTATION.md` - Technical details
   - `AUTHELIA_OIDC_SMOKE_TEST.md` - Comprehensive testing

3. **Read guides**:
   - `AUTHELIA_OIDC_DEPLOYMENT.md` - For production
   - `AUTHELIA_OIDC_TROUBLESHOOTING.md` - If issues occur

## Common Tasks

### Reset Everything
```bash
# Stop all services
make docker-dev-down

# Clear database (if needed)
docker volume rm parchmark_postgres_data

# Restart
make docker-dev
make dev-backend &
make dev-ui &
```

### Test Local Login Still Works
```bash
# Create local user
docker exec parchmark-backend python scripts/manage_users.py create testuser password123

# Login with: testuser / password123
# Should see auth_provider='local' in database
```

### Check Tokens
```javascript
// In browser console after login:
console.log('Auth state:', localStorage.getItem('auth-store'));
console.log('Token source:', JSON.parse(localStorage.getItem('auth-store')).tokenSource);
```

### View Backend Logs
```bash
docker logs parchmark-backend -f | grep -i "oidc\|auth"
```

### View Frontend Console
```
DevTools → Console tab
Look for any red errors related to OIDC or API
```

## Success Checklist

- [ ] Authelia OIDC client created
- [ ] Backend starts without errors
- [ ] Frontend loads and shows SSO button
- [ ] Local login works
- [ ] OIDC login redirects to Authelia
- [ ] OIDC login creates user in database
- [ ] Can create/edit notes as OIDC user
- [ ] Token refresh works
- [ ] Logout clears session
- [ ] Tests pass: `make test-all`

## Support

If stuck:

1. **Check logs**: `docker logs authelia`, `docker logs parchmark-backend`
2. **Verify config**: Run through configuration steps again
3. **Test endpoints**:
   ```bash
   curl http://localhost:9091/.well-known/openid-configuration
   curl http://localhost:8000/api/health
   ```
4. **Read troubleshooting**: `AUTHELIA_OIDC_TROUBLESHOOTING.md`

## What's Happening

### Local Login Flow
1. User enters credentials
2. Backend validates and returns JWT token
3. Frontend stores token in localStorage
4. API requests include token in Authorization header

### OIDC Login Flow
1. User clicks SSO button
2. Frontend redirects to Authelia authorization endpoint
3. User logs in at Authelia
4. Authelia redirects back with authorization code
5. Frontend exchanges code for tokens
6. Frontend stores OIDC token in localStorage
7. API requests include OIDC token in Authorization header
8. Backend validates token against Authelia JWKS

### Auto-User Creation
1. OIDC token arrives at backend
2. Backend validates token against Authelia JWKS
3. Backend extracts user info from token claims
4. Backend looks up user by oidc_sub
5. If not found: auto-creates user with oidc_sub, email, auth_provider='oidc'
6. Returns user for API request

## How to Learn More

- **Architecture**: `AUTHELIA_OIDC_IMPLEMENTATION.md`
- **Testing**: `AUTHELIA_OIDC_SMOKE_TEST.md`
- **Deployment**: `AUTHELIA_OIDC_DEPLOYMENT.md`
- **Troubleshooting**: `AUTHELIA_OIDC_TROUBLESHOOTING.md`
- **Code**: Check `backend/app/auth/oidc_validator.py` and frontend OIDC files

## Time Estimates

| Task | Time |
|------|------|
| Authelia config | 2 min |
| Backend env | 2 min |
| Frontend env | 2 min |
| Start services | 2 min |
| Test both flows | 2 min |
| **Total** | **10 min** |

Enjoy! 🚀
