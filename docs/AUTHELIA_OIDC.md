# Authelia OIDC Integration Guide

This guide covers registering ParchMark as an Authelia OIDC client and testing the backend's OIDC token validation.

## Overview

ParchMark's **backend** supports hybrid authentication:
- **Local auth**: Traditional username/password login (HS256 JWT)
- **OIDC auth**: Bearer tokens issued by Authelia (or any OIDC provider)

Both methods work simultaneously — the backend tries local JWT validation first, then falls back to OIDC. OIDC users are auto-created on first authenticated request.

**Scope note:** OIDC support is backend-only. The Vue frontend has no SSO button, no OIDC redirect/callback flow, and no `VITE_OIDC_*` configuration — the login screen is local username/password only. OIDC tokens reach the API from external clients (e.g. tools calling the API with an Authelia-issued access token).

## Token Validation Model

Authelia issues **opaque** access tokens (`authelia_at_...`) by default — these are not JWTs and cannot be decoded locally. The backend handles both formats:

- **Opaque tokens** (the primary path): validated by calling Authelia's **userinfo endpoint**; a valid response yields the user claims
- **JWT access tokens**: validated locally against Authelia's **JWKS** (RS256 public keys), fetched via OIDC discovery and cached

Discovery and JWKS responses are cached in-process. Backend env vars (`OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_USERNAME_CLAIM`, plus optional `OIDC_DISCOVERY_URL` and `OIDC_OPAQUE_TOKEN_PREFIX`) are documented in [`AGENTS.md`](../AGENTS.md#environment-variables); defaults live in `backend/app/auth/oidc_validator.py`. Two non-obvious knobs:

- `OIDC_DISCOVERY_URL` — separate URL for discovery/JWKS fetches, e.g. internal cluster DNS to bypass CDN bot challenges (Cloudflare JS challenges block non-browser clients) while `OIDC_ISSUER_URL` stays the public issuer
- `OIDC_OPAQUE_TOKEN_PREFIX` — optional required prefix (e.g. `authelia_at_`) so garbage tokens are rejected before an outbound userinfo call

## Registering the Client in Authelia

Add ParchMark as a public OIDC client in your `authelia/configuration.yml`. Production uses client id `parchmark`; the in-repo test rig uses `parchmark-web` (see `authelia-dev-config.yml` for the working example):

```yaml
identity_providers:
  oidc:
    clients:
      - id: parchmark            # must match backend OIDC_AUDIENCE
        description: ParchMark Note-Taking Application
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
```

Restart Authelia after editing, then point the backend at it via `OIDC_ISSUER_URL` / `OIDC_AUDIENCE` in `backend/.env`.

## Auto-User Creation

On a valid OIDC token, the backend (`backend/app/auth/dependencies.py`):

1. Extracts claims (from the JWT or the userinfo response)
2. Looks up the user by `oidc_sub`
3. If the token lacks user claims, fetches them from the userinfo endpoint
4. If no user exists: auto-creates one with `auth_provider='oidc'`, `oidc_sub` set, and `password_hash=NULL` (concurrent first requests are handled — the loser of the race re-fetches the winner's row)

The username comes from the claim named by `OIDC_USERNAME_CLAIM` (default `preferred_username`), falling back to `email`.

## Local Testing

The repo ships a self-contained OIDC test rig — `docker-compose.oidc-test.yml` (PostgreSQL + Authelia + backend, plus a frontend container on :8080; its `VITE_OIDC_*` env vars are vestigial — the UI does not read them) configured by `authelia-dev-config.yml`, with client id `parchmark-web`. `.env.example.oidc` is the annotated env template.

Start it with `make docker-oidc-test` (it prints the follow-up status/logs/stop targets; `make help` lists them all). `make test-backend-oidc` runs the backend OIDC unit + hybrid-auth integration tests without the rig. Against a live Authelia (running rig or real deployment), `make test-oidc-integration` exercises discovery, JWKS, and token validation end to end.

## Troubleshooting

### Token validation fails (401 errors)

```bash
# Test OIDC discovery endpoint
curl https://auth.engen.tech/.well-known/openid-configuration

# Check backend config
docker exec parchmark-backend env | grep OIDC
```

**Fix**: Verify `OIDC_ISSUER_URL` and `OIDC_AUDIENCE` match the Authelia client registration (case-sensitive). If `OIDC_OPAQUE_TOKEN_PREFIX` is set, confirm the tokens actually carry that prefix.

### User not created after OIDC login

```bash
# Check database schema
docker exec postgres psql -U parchmark_user -d parchmark_db -c "\d users"
# Should show: oidc_sub, email, auth_provider columns
```

**Fix**: Run database migrations: `cd backend && uv run alembic upgrade head`. If the schema is present, check backend logs — a token whose claims (and userinfo response) contain neither `preferred_username` nor `email` is rejected; adjust the Authelia client scopes/claims.

### Cannot reach OIDC provider

```bash
# Test from backend container
docker exec parchmark-backend curl -I https://auth.engen.tech/.well-known/openid-configuration
```

**Fix**: Check DNS, firewall rules, and TLS certificate validity. If the issuer sits behind a CDN that challenges non-browser clients, set `OIDC_DISCOVERY_URL` to an internal address.

## Security Notes

- ParchMark is registered as a **public OIDC client** — no client secret; **PKCE (S256)** required
- Opaque tokens are validated server-side via the **userinfo endpoint**; JWT access tokens against Authelia's **JWKS**
- OIDC users have no local password (`password_hash=NULL`)
- **HTTPS required** in production

## References

- [Authelia OIDC Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [OpenID Connect Specification](https://openid.net/connect/)
