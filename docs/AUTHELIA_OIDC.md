# Authelia OIDC Integration Guide

This guide covers setting up Authelia OIDC (Single Sign-On) with ParchMark.

## Overview

ParchMark supports hybrid authentication:
- **Local auth**: Traditional username/password login
- **OIDC auth**: Single Sign-On via Authelia (or any OIDC provider)

Both methods can be used simultaneously. OIDC users are auto-created on first login.

## Quick Start (10 minutes)

### Step 1: Authelia Configuration

Add ParchMark as an OIDC client in your `authelia/configuration.yml`:

```yaml
identity_providers:
  oidc:
    clients:
      - id: parchmark
        description: ParchMark Note-Taking Application
        public: true
        secret: ~
        redirect_uris:
          - https://notes.engen.tech/oidc/callback  # Production
          - http://localhost:5173/oidc/callback     # Development
        scopes:
          - openid
          - profile
          - email
        grant_types:
          - authorization_code
          - refresh_token
        response_types:
          - code
        require_pkce: true
        pkce_challenge_method: S256
```

Restart Authelia:
```bash
docker restart authelia
```

### Step 2: Backend Configuration

Add to `backend/.env`:

```bash
OIDC_ISSUER_URL=https://auth.engen.tech  # Your Authelia URL
OIDC_AUDIENCE=parchmark                   # Must match Authelia client id
OIDC_USERNAME_CLAIM=preferred_username    # Claim for username extraction
```

### Step 3: Frontend Configuration

Add to `ui/.env`:

```bash
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark
VITE_OIDC_REDIRECT_URI=http://localhost:5173/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=http://localhost:5173/login
```

### Step 4: Start Services

```bash
make docker-dev      # Start PostgreSQL
make dev-backend     # Start backend
make dev-ui          # Start frontend
```

### Step 5: Test

1. Open http://localhost:5173/login
2. Click "Sign In with SSO"
3. Login at Authelia
4. Should redirect back to notes page

## Configuration Reference

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OIDC_ISSUER_URL` | Authelia base URL | `https://auth.engen.tech` |
| `OIDC_AUDIENCE` | OIDC client ID (must match Authelia) | `parchmark` |
| `OIDC_USERNAME_CLAIM` | JWT claim for username | `preferred_username` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_OIDC_ISSUER_URL` | Authelia base URL | `https://auth.engen.tech` |
| `VITE_OIDC_CLIENT_ID` | OIDC client ID | `parchmark` |
| `VITE_OIDC_REDIRECT_URI` | Callback URL after login | `{origin}/oidc/callback` |
| `VITE_OIDC_LOGOUT_REDIRECT_URI` | Redirect after logout | `{origin}/login` |

### Production Configuration

**Backend** (`backend/.env.production`):
```bash
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark
OIDC_USERNAME_CLAIM=preferred_username
```

**Frontend** (`ui/.env.production`):
```bash
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark
VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login
```

## How It Works

### Authentication Flow

1. User clicks "Sign In with SSO"
2. Frontend redirects to Authelia authorization endpoint
3. User authenticates at Authelia
4. Authelia redirects back with authorization code
5. Frontend exchanges code for tokens (PKCE)
6. Frontend stores OIDC token in auth store
7. API requests include OIDC token in Authorization header
8. Backend validates token against Authelia JWKS

### Auto-User Creation

1. Backend receives OIDC token
2. Validates token against Authelia JWKS
3. Extracts user info from token claims
4. Looks up user by `oidc_sub`
5. If not found: auto-creates user with `auth_provider='oidc'`
6. Returns user for API request

### Database Schema

OIDC users have:
- `auth_provider='oidc'`
- `oidc_sub` set to unique OIDC subject identifier
- `password_hash=NULL` (OIDC-only authentication)

## Troubleshooting

### SSO button not appearing

```javascript
// Check frontend config in browser console
console.log('OIDC config:', import.meta.env.VITE_OIDC_ISSUER_URL);
```

**Fix**: Verify `.env` has OIDC variables, rebuild frontend if changed.

### "Invalid client_id" error

**Fix**: Ensure `VITE_OIDC_CLIENT_ID` exactly matches Authelia config (case-sensitive).

### Redirect URI mismatch

**Fix**: Ensure `VITE_OIDC_REDIRECT_URI` exactly matches Authelia's `redirect_uris` (protocol, port, path).

### Token validation fails (401 errors)

```bash
# Test OIDC discovery endpoint
curl https://auth.engen.tech/.well-known/openid-configuration

# Check backend config
docker exec parchmark-backend env | grep OIDC
```

**Fix**: Verify `OIDC_ISSUER_URL` and `OIDC_AUDIENCE` match Authelia configuration.

### User not created after OIDC login

```bash
# Check database schema
docker exec postgres psql -U parchmark_user -d parchmark_db -c "\d users"
# Should show: oidc_sub, email, auth_provider columns
```

**Fix**: Run database migrations: `cd backend && uv run alembic upgrade head`

### Cannot reach OIDC provider

```bash
# Test from backend container
docker exec parchmark-backend curl -I https://auth.engen.tech/.well-known/openid-configuration
```

**Fix**: Check DNS, firewall rules, and TLS certificate validity.

## Testing

```bash
# Run all tests (includes OIDC tests)
make test-all

# Or run OIDC-specific tests only (see `make help` for all targets)
make test-backend-oidc
make test-ui-oidc
```

## Security Notes

- ParchMark is a **public OIDC client** (browser SPA) - no client secret
- **PKCE (S256)** is required for security
- Tokens validated against Authelia's **JWKS** (public keys)
- OIDC users have no local password (OIDC-only auth)
- **HTTPS required** in production

## Verification Checklist

- [ ] Authelia OIDC client configured
- [ ] Backend starts without errors
- [ ] Frontend shows SSO button
- [ ] Local login still works
- [ ] OIDC login redirects to Authelia
- [ ] OIDC login creates user in database
- [ ] Token refresh works
- [ ] Logout clears session
- [ ] Tests pass: `make test-all`

## References

- [Authelia OIDC Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [OpenID Connect Specification](https://openid.net/connect/)
