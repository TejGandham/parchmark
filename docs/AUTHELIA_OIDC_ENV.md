# Authelia OIDC Environment Variables

This guide documents all environment variables needed for Authelia OIDC integration with ParchMark.

## Backend Configuration

Add the following environment variables to your backend `.env` file:

```bash
# Existing variables (keep as is)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# New OIDC variables
AUTH_MODE=hybrid                                    # "local", "oidc", or "hybrid"
OIDC_ISSUER_URL=https://auth.engen.tech           # Authelia OIDC issuer URL
OIDC_AUDIENCE=parchmark-web                        # OIDC client ID (must match Authelia config)
OIDC_USERNAME_CLAIM=preferred_username             # Primary username claim (fallback to email)
```

### Variable Descriptions

- **AUTH_MODE**: Determines which authentication methods are enabled
  - `local`: Only local username/password authentication
  - `oidc`: Only OIDC-based authentication
  - `hybrid`: Both local and OIDC authentication (recommended)

- **OIDC_ISSUER_URL**: The base URL of your Authelia instance
  - Discovery endpoint: `{OIDC_ISSUER_URL}/.well-known/openid-configuration`

- **OIDC_AUDIENCE**: The OIDC client ID registered in Authelia (must match exactly)

- **OIDC_USERNAME_CLAIM**: The JWT claim to use for username extraction
  - Tries `preferred_username` first, falls back to `email` if not present

## Frontend Configuration

Add the following environment variables to your frontend `.env` file:

```bash
# Existing variables (keep as is)
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60

# New OIDC variables
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login
```

### Variable Descriptions

- **VITE_OIDC_ISSUER_URL**: The Authelia OIDC issuer URL (public URL)

- **VITE_OIDC_CLIENT_ID**: The OIDC client ID registered in Authelia (public client)

- **VITE_OIDC_REDIRECT_URI**: The callback URL where Authelia redirects after successful authentication
  - Must match exactly with Authelia OIDC client configuration
  - For production: `https://notes.engen.tech/oidc/callback`
  - For development: `http://localhost:5173/oidc/callback`

- **VITE_OIDC_LOGOUT_REDIRECT_URI**: Where to redirect after OIDC logout
  - For production: `https://notes.engen.tech/login`
  - For development: `http://localhost:5173/login`

## Development vs Production

### Development Environment

```bash
# Backend (.env.dev)
AUTH_MODE=hybrid
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark-web
OIDC_USERNAME_CLAIM=preferred_username
```

```bash
# Frontend (.env.dev)
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=http://localhost:5173/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=http://localhost:5173/login
```

### Production Environment

```bash
# Backend (.env.production)
AUTH_MODE=hybrid
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark-web
OIDC_USERNAME_CLAIM=preferred_username
```

```bash
# Frontend (.env.production)
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login
```

## Docker Compose Configuration

For Docker deployments, set environment variables in `.env.docker` or directly in `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      AUTH_MODE: hybrid
      OIDC_ISSUER_URL: https://auth.engen.tech
      OIDC_AUDIENCE: parchmark-web
      OIDC_USERNAME_CLAIM: preferred_username

  frontend:
    environment:
      VITE_OIDC_ISSUER_URL: https://auth.engen.tech
      VITE_OIDC_CLIENT_ID: parchmark-web
      VITE_OIDC_REDIRECT_URI: http://localhost:8080/oidc/callback  # for dev
      VITE_OIDC_LOGOUT_REDIRECT_URI: http://localhost:8080/login
```

## Verification Checklist

After setting environment variables:

1. **Backend OIDC Endpoints**: Verify Authelia is reachable
   ```bash
   curl https://auth.engen.tech/.well-known/openid-configuration
   ```

2. **Backend Health Check**: Should include database connectivity
   ```bash
   curl https://assets-api.engen.tech/api/health
   ```

3. **Frontend SSO Button**: Should appear on login page
   - Click "Sign In with SSO" button
   - Should redirect to Authelia login

4. **Callback Handling**: After Authelia login, should redirect to notes
   - Callback URL: `https://notes.engen.tech/oidc/callback`
   - Should store OIDC token in auth store
   - Should redirect to `/notes` page

## Troubleshooting

### "OIDC configuration not found" error
- Verify `VITE_OIDC_ISSUER_URL` and `VITE_OIDC_CLIENT_ID` are set correctly
- Check that Authelia is running and reachable

### "Invalid client_id" error
- Verify `VITE_OIDC_CLIENT_ID` matches Authelia OIDC client configuration exactly
- Check that the client is registered in `authelia/configuration.yml`

### "Redirect URI mismatch" error
- Verify `VITE_OIDC_REDIRECT_URI` matches exactly in Authelia OIDC client config
- Check for protocol (http vs https) and port differences

### Backend cannot validate OIDC tokens
- Verify `OIDC_ISSUER_URL` is reachable from backend container
- Check that `OIDC_AUDIENCE` matches the client ID
- Verify JWKS endpoint is accessible: `{OIDC_ISSUER_URL}/.well-known/openid-configuration/jwks`

### Users not auto-created after OIDC login
- Check that `OIDC_USERNAME_CLAIM` is set to a claim that exists in Authelia tokens
- Verify database migrations have been applied (new columns: `oidc_sub`, `email`, `auth_provider`)
- Check backend logs for errors during user creation

## Security Notes

1. **Never commit `.env` files** with real values to git
2. **PKCE is enabled** by default for public OIDC clients
3. **Tokens are validated** against Authelia's JWKS (public keys)
4. **OIDC-created users** have no password (OIDC-only authentication)
5. **Mixed authentication** is supported (same user can use local or OIDC)

## Additional Resources

- [Authelia OIDC Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/)
- [oidc-client-ts Documentation](https://github.com/IdentityModel/oidc-client-ts)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
