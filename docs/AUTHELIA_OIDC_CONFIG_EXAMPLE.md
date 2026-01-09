# Authelia OIDC Configuration Example

This document provides example Authelia configuration for registering ParchMark as an OIDC client.

## Overview

ParchMark is registered as a **public OIDC client** (no client secret) with:
- Authorization Code grant type
- PKCE support (S256)
- Refresh token support
- OpenID Connect scopes

## Configuration Snippet

Add this to your `authelia/configuration.yml` under `identity_providers.oidc.clients`:

```yaml
identity_providers:
  oidc:
    # ... other OIDC configuration ...
    clients:
      # Existing clients...

      # ParchMark OIDC Client
      - id: parchmark-web
        secret: ~  # Public client - no secret required
        public: true
        description: ParchMark Note-Taking Application

        # Redirect URIs - where Authelia redirects after successful login
        redirect_uris:
          # Production
          - https://notes.engen.tech/oidc/callback
          # Development (if needed)
          - http://localhost:5173/oidc/callback

        # OpenID Connect scopes
        scopes:
          - openid      # Required - provides 'sub' claim
          - profile     # Provides 'preferred_username', 'name', etc.
          - email       # Provides 'email' claim

        # Grant types
        grant_types:
          - authorization_code  # Required - OAuth2 code flow
          - refresh_token       # Optional - enables silent renewal

        # Response types
        response_types:
          - code  # Standard OAuth2 code flow

        # PKCE (Proof Key for Code Exchange)
        # Recommended for public clients
        require_pkce: true
        pkce_challenge_method: S256  # S256 or plain

        # User information signature
        # Use 'none' for simplicity, or RSA256 for security
        userinfo_signed_response_alg: none

        # Optional: Response modes
        # response_modes:
        #   - form_post
        #   - query
```

## Complete Authelia Configuration Template

Here's a more complete example with context:

```yaml
# authelia/configuration.yml

# ... other configuration ...

identity_providers:
  oidc:
    # Session timeout for OIDC provider
    session_expiration: 1h

    # Token lifetimes
    access_token_expiration: 1h        # Access token validity
    refresh_token_expiration: 7d       # Refresh token validity
    authorization_code_expiration: 10m # Auth code validity

    # Keys for signing tokens (auto-generated if not provided)
    # keys:
    #   - key_id: "my-key"
    #     use: sig

    # Enforce secure token handling
    enforce_pkce: optional  # or 'always' for strict PKCE

    clients:
      # Example: Existing client
      - id: my-existing-client
        secret: { cipher: "jOHN3x...", algorithm: "argon2id" }
        # ... rest of config ...

      # ParchMark - Production
      - id: parchmark-web
        description: ParchMark Note-Taking Application (Production)
        public: true
        secret: ~
        redirect_uris:
          - https://notes.engen.tech/oidc/callback
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
        userinfo_signed_response_alg: none

      # ParchMark - Development (optional)
      - id: parchmark-web-dev
        description: ParchMark Note-Taking Application (Development)
        public: true
        secret: ~
        redirect_uris:
          - http://localhost:5173/oidc/callback
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
        userinfo_signed_response_alg: none
```

## Verification Steps

After adding the configuration:

### 1. Restart Authelia
```bash
docker restart authelia
docker logs authelia | grep -i "oidc\|parchmark"
```

### 2. Check OIDC Discovery Endpoint
```bash
curl https://auth.engen.tech/.well-known/openid-configuration | jq .
```

Should return something like:
```json
{
  "issuer": "https://auth.engen.tech",
  "authorization_endpoint": "https://auth.engen.tech/authorization",
  "token_endpoint": "https://auth.engen.tech/token",
  "userinfo_endpoint": "https://auth.engen.tech/userinfo",
  "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
  "end_session_endpoint": "https://auth.engen.tech/end_session",
  "scopes_supported": ["openid", "profile", "email"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  ...
}
```

### 3. Verify JWKS Endpoint
```bash
curl https://auth.engen.tech/.well-known/openid-configuration/jwks | jq '.keys | length'
# Should return: 1 or more (number of keys)
```

### 4. Test OIDC Flow (Optional)
```bash
# Start OIDC login flow
curl -L "https://auth.engen.tech/authorization?client_id=parchmark-web&redirect_uri=http://localhost:5173/oidc/callback&response_type=code&scope=openid%20profile%20email&state=test123"

# Should redirect to Authelia login page
```

## Important Notes

### Public Client
- No client secret stored (safe for SPA)
- Uses PKCE S256 for security
- Must have valid redirect URIs

### Redirect URIs
- Must use HTTPS in production
- HTTP allowed for localhost development
- Must match exactly (no trailing slash differences)
- Cannot use wildcards

### PKCE
- Required for public clients
- S256 (SHA256) recommended over 'plain'
- Protects against authorization code interception

### Scopes
- `openid`: Enables OpenID Connect (required)
- `profile`: Includes preferred_username and name
- `email`: Includes email address

### Token Lifetimes
- Access token: 1 hour (configurable)
- Refresh token: 7 days (configurable)
- Auth code: 10 minutes (configurable)

## Troubleshooting

### Client Not Found Error
```
Error: client_id 'parchmark-web' not found
```
**Solution**: Verify the client ID in configuration matches exactly (case-sensitive)

### Redirect URI Mismatch
```
Error: The redirect_uri 'https://notes.engen.tech/oidc/callback' doesn't match registered redirect_uris
```
**Solution**: Check for typos, protocol differences (http vs https), port numbers

### OIDC Discovery Not Working
```
Error: Unable to reach OIDC discovery endpoint
```
**Solution**:
- Verify OIDC_ISSUER_URL is correct
- Check Authelia is running: `docker ps | grep authelia`
- Check Authelia logs: `docker logs authelia`
- Verify network connectivity

### JWKS Endpoint Fails
```
Error: Unable to fetch JWKS
```
**Solution**:
- Verify JWKS URI in discovery endpoint
- Check Authelia logs for errors
- Verify key generation is working

## Minimal Configuration (Quick Start)

For quick testing, use this minimal client configuration:

```yaml
identity_providers:
  oidc:
    clients:
      - id: parchmark-web
        description: ParchMark
        public: true
        redirect_uris:
          - https://notes.engen.tech/oidc/callback
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

## Security Best Practices

### For Production

1. **Use HTTPS only**
   - All OIDC endpoints must be HTTPS
   - Certificate should be valid and trusted

2. **Secure token storage**
   - Tokens stored in secure, HTTP-only cookies (handled by Authelia)
   - PKCE enabled for all public clients

3. **Session timeout**
   - Set appropriate session expiration
   - Recommend: 1-2 hours for access tokens

4. **Refresh tokens**
   - Keep refresh token expiration reasonable (7-14 days)
   - Implement token rotation if possible

5. **Redirect URI validation**
   - Only allow specific, trusted redirect URIs
   - No wildcard URIs
   - Always use HTTPS

### For Development

- Can use HTTP for localhost
- PKCE still recommended but not strictly required
- Token lifetime can be longer for testing

## Next Steps

1. **Add this configuration to Authelia**
2. **Restart Authelia** to apply changes
3. **Verify discovery endpoint** works
4. **Update ParchMark environment variables** (see `.env.example.oidc`)
5. **Test login flow** (see `AUTHELIA_OIDC_SMOKE_TEST.md`)

## References

- [Authelia OIDC Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [OpenID Connect Specification](https://openid.net/connect/)
