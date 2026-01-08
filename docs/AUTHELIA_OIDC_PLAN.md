# Authelia OIDC + Local Auth Implementation Plan

## Problem Description
ParchMark currently supports only local username/password authentication using app-issued JWTs. The goal is to add Authelia OIDC-based SSO while preserving the existing local login flow, so users can either sign in with username/password or with Authelia.

## What We Are Trying to Solve
- Enable federated authentication via Authelia OIDC for the ParchMark UI and API.
- Keep the existing local auth flow fully functional (hybrid auth).
- Maintain current UX patterns (protected routes, centralized error handling) while adding a clear “Sign in with SSO” entry point.
- Ensure backend accepts both local JWTs and Authelia-issued access tokens safely.

## Requirements and Constraints
- Authelia is already hosted at "https://auth.engen.tech".
- UI is hosted at "https://notes.engen.tech".
- API is hosted at "https://assets-api.engen.tech".
- Nginx Proxy Manager is already routing these hosts.
- OIDC flow must use Authorization Code + PKCE (SPA public client).
- Authelia OIDC client uses "preferred_username" as the primary username claim.
- Users should be auto-created on first OIDC login.
- Keep local JWT login/refresh endpoints available.

## Task-Based Implementation Plan

### 1) Authelia Configuration (OIDC Client)
1. Update "authelia/configuration.yml":
   - Add OIDC client "parchmark-web" with:
     - "public: true"
     - "redirect_uris":
       - "https://notes.engen.tech/oidc/callback"
       - "http://localhost:5173/oidc/callback"
     - "scopes": "openid", "profile", "email"
     - "grant_types": "authorization_code", "refresh_token"
     - "require_pkce: true", "pkce_challenge_method: S256"
2. Restart Authelia.
3. Verify discovery endpoint:
   - "https://auth.engen.tech/.well-known/openid-configuration"
4. Record OIDC metadata values:
   - "issuer"
   - "jwks_uri"
   - "authorization_endpoint"
   - "token_endpoint"
   - "end_session_endpoint" (for logout redirect)

### 2) Backend: OIDC Token Validation (Hybrid Auth)
1. Add backend env vars:
   - "AUTH_MODE=hybrid"
   - "OIDC_ISSUER_URL=https://auth.engen.tech"
   - "OIDC_AUDIENCE=parchmark-web"
   - "OIDC_USERNAME_CLAIM=preferred_username"
2. Add an OIDC validator module:
   - Fetch JWKS from "jwks_uri" (cache keys in memory with TTL).
   - Validate JWT:
     - "iss" equals "OIDC_ISSUER_URL"
     - "aud" includes "OIDC_AUDIENCE"
     - "exp" not expired
     - signature matches JWKS
   - Extract "sub" and "preferred_username" claim.
   - Fallback to "email" if "preferred_username" is missing.
3. Update auth dependency "get_current_user":
   - Attempt to validate as local JWT (current logic).
   - If local JWT fails and "AUTH_MODE" allows OIDC:
     - Validate as OIDC JWT.
     - Lookup user by "oidc_sub" and create if missing.
4. Update User model to support OIDC:
   - Add fields:
     - "oidc_sub" (unique, nullable for local users)
     - "email" (nullable)
     - "auth_provider" (e.g., ""local"" or ""oidc"")
   - Make "password_hash" nullable for OIDC users.
5. Add migration (Alembic or existing auto-migration approach):
   - Schema updates for new columns and nullable "password_hash".
6. Update "/auth/me" behavior:
   - Should return user info for either local or OIDC token.
7. Keep local "/auth/login" and "/auth/refresh" unchanged.

### 3) Frontend: OIDC Flow + UI Changes
1. Add frontend env vars:
   - "VITE_OIDC_ISSUER_URL=https://auth.engen.tech"
   - "VITE_OIDC_CLIENT_ID=parchmark-web"
   - "VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback"
   - "VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login"
2. Add OIDC client library (e.g., "oidc-client-ts").
3. Add “Sign in with SSO” button in "LoginForm":
   - Start OIDC login redirect (authorization endpoint).
4. Add "/oidc/callback" route:
   - Handle code exchange via OIDC client.
   - Store access token in auth store.
   - Navigate to "/notes" (or stored "from" route).
5. Update auth store to support OIDC token:
   - Distinguish token source: "local" vs "oidc".
   - If token source is "oidc", use OIDC client for renew/refresh.
6. Update token refresh logic:
   - For local auth: keep current "/auth/refresh" flow.
   - For OIDC: use silent renew or refresh token if issued by Authelia.
7. Update logout flow:
   - Clear local auth state.
   - If OIDC session, redirect to Authelia end-session endpoint (optional but recommended).

### 4) API Client Behavior
1. Keep "Authorization: Bearer <token>" header.
2. On 401:
   - If local auth: attempt "/auth/refresh".
   - If OIDC: attempt OIDC renew or logout to force re-auth.

### 5) Test Plan
1. Backend tests:
   - OIDC token validation success path with JWKS mock.
   - Invalid "iss"/"aud"/"exp" rejection.
   - Auto-create user on first OIDC request.
2. Frontend tests:
   - Login form renders SSO button.
   - OIDC callback sets auth state and redirects.
   - Local login still works.
3. Integration smoke test:
   - Log in with Authelia, view notes, create note, logout.
   - Log in locally, view notes, refresh token, logout.

### 6) Deployment Checklist
1. Apply backend and UI env updates in production.
2. Ensure NPM hosts resolve:
   - "auth.engen.tech" → "authelia:9091"
   - "notes.engen.tech" → "parchmark-frontend:80"
   - "assets-api.engen.tech" → "parchmark-backend:8000"
3. Run health checks:
   - "https://auth.engen.tech/.well-known/openid-configuration"
   - "https://assets-api.engen.tech/api/health"
   - "https://notes.engen.tech"
4. Verify CORS allows "https://notes.engen.tech".
5. Monitor logs for OIDC validation errors.

## Open Decisions (If Needed Later)
- Whether to enforce Authelia logout ("end_session_endpoint") or only clear app state.
- Whether to support email-only identities or require "preferred_username".
- Whether to disable local login in production in the future.
