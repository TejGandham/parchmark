# Authelia OIDC Implementation Summary

This document summarizes the complete implementation of Authelia OIDC authentication for ParchMark, enabling hybrid authentication (local + SSO).

## Overview

ParchMark now supports federated authentication via Authelia OIDC while maintaining backward compatibility with local username/password authentication. Users can sign in using either method.

## Changes Summary

### Backend Changes

#### 1. New OIDC Validator Module (`backend/app/auth/oidc_validator.py`)
- **Purpose**: Validates JWT tokens issued by Authelia
- **Key Features**:
  - JWKS caching with 1-hour TTL to reduce provider requests
  - Automatic discovery endpoint fetching
  - Handles token expiration validation
  - Extracts user claims (preferred_username, email, sub)
  - Error logging for debugging

**Key Functions**:
- `get_jwks()`: Fetches and caches JWKS from discovery endpoint
- `validate_oidc_token(token)`: Validates OIDC JWT and returns claims
- `extract_username(claims)`: Extracts username with email fallback
- `extract_user_info(claims)`: Extracts complete user information

#### 2. Updated User Model (`backend/app/models/models.py`)
```python
# New fields for OIDC support
oidc_sub: Optional[str]          # OIDC subject claim (unique)
email: Optional[str]              # User email from OIDC provider
auth_provider: str                # "local" or "oidc"
password_hash: Optional[str]      # Now nullable for OIDC-only users
```

**Migration Required**: Schema changes must be applied via database migrations

#### 3. Hybrid Authentication Dependencies (`backend/app/auth/dependencies.py`)
- **Updated `get_current_user()`**: Now async, supports both local JWT and OIDC tokens
  - Attempts local JWT validation first
  - Falls back to OIDC validation if local JWT fails
  - Auto-creates users on first OIDC login
  - Stores OIDC metadata (oidc_sub, email)

- **New Helper**: `get_user_by_oidc_sub()` for OIDC user lookups

**Async Change**: `get_current_user` and `get_current_active_user` are now async to support OIDC validation

#### 4. Dependencies (`backend/pyproject.toml`)
- Added `httpx>=0.26.0` for async HTTP requests to OIDC provider

### Frontend Changes

#### 1. OIDC Configuration (`ui/src/config/oidc.ts`)
- Centralized OIDC configuration from environment variables
- Supports development and production URLs
- PKCE (S256) enabled by default for public clients
- Endpoint configuration for authorization, token, userinfo, end_session

#### 2. OIDC Utilities (`ui/src/features/auth/utils/oidcUtils.ts`)
- UserManager initialization for complete OIDC flow
- Functions:
  - `startOIDCLogin()`: Initiates redirect to Authelia
  - `handleOIDCCallback()`: Exchanges authorization code for tokens
  - `getOIDCUser()`: Retrieves current OIDC user
  - `renewOIDCToken()`: Silent token renewal
  - `logoutOIDC()`: Redirects to Authelia end_session endpoint

#### 3. Updated Auth Store (`ui/src/features/auth/store/auth.ts`)
- **New Type**: `TokenSource = 'local' | 'oidc'` to distinguish authentication method
- **New State**: `tokenSource` field tracking auth method
- **New Actions**:
  - `loginWithOIDC()`: Starts OIDC login flow
  - `handleOIDCCallbackFlow()`: Processes callback and stores OIDC tokens
- **Updated `refreshTokens()`**: Different refresh logic for OIDC vs local tokens
- **Updated `logout()`**: Calls Authelia end_session if OIDC user

#### 4. OIDC Callback Component (`ui/src/features/auth/components/OIDCCallback.tsx`)
- Handles redirect from Authelia after authentication
- Displays loading spinner during token exchange
- Auto-redirects to protected route or `/notes` on success
- Handles errors gracefully with redirect to login

#### 5. Updated Login Form (`ui/src/features/auth/components/LoginForm.tsx`)
- New "Sign In with SSO" button below local login form
- Uses outline variant with blue color to differentiate from local login
- Shows loading state during OIDC redirect
- Divider between local and SSO options

#### 6. Router Updates (`ui/src/App.tsx`)
- Added `/oidc/callback` route for handling Authelia redirects
- Lazy-loaded OIDCCallback component

#### 7. Dependencies (`ui/package.json`)
- Added `oidc-client-ts@^3.0.1` for complete OIDC client functionality

### Testing

#### Backend Tests

**Unit Tests** (`backend/tests/unit/auth/test_oidc_validator.py`):
- JWKS fetch and caching
- Discovery endpoint handling
- Token claim extraction
- Username fallback logic (preferred_username → email)
- Token validation success/failure cases
- Expired token handling

**Integration Tests** (`backend/tests/integration/auth/test_oidc_hybrid_auth.py`):
- Hybrid auth with existing local user
- OIDC token validation for existing OIDC user
- Auto-creation of new users on first OIDC login
- Email fallback when preferred_username missing
- Both auth methods failing gracefully
- OIDC subject lookup helper

## Configuration

### Environment Variables

**Backend** (new variables):
```bash
AUTH_MODE=hybrid                          # "local", "oidc", or "hybrid"
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark-web
OIDC_USERNAME_CLAIM=preferred_username
```

**Frontend** (new variables):
```bash
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark-web
VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login
```

See `docs/AUTHELIA_OIDC_ENV.md` for detailed configuration guide.

## Implementation Flow

### Login with OIDC

```
User clicks "Sign In with SSO"
  ↓
Frontend initiates OIDC Authorization Code flow
  ↓
User redirected to Authelia login page
  ↓
User authenticates with Authelia
  ↓
Authelia redirects to /oidc/callback with authorization code
  ↓
Frontend exchanges code for tokens
  ↓
Frontend stores OIDC token and tokenSource='oidc'
  ↓
Frontend navigates to /notes
  ↓
API receives request with OIDC access token
  ↓
Backend validates token against Authelia JWKS
  ↓
Backend auto-creates user if first login (stores oidc_sub)
  ↓
User authenticated and can access notes
```

### Token Refresh

**For Local Auth**:
- Uses existing `/auth/refresh` endpoint with refresh token

**For OIDC**:
- Uses `renewOIDCToken()` for silent renewal
- Falls back to re-authentication if renewal fails

### Logout

**For Local Auth**:
- Clears auth store, tokens removed from localStorage

**For OIDC**:
- Clears auth store
- Redirects to Authelia end_session endpoint
- Authelia redirects back to app after logout

## Security Considerations

1. **PKCE Support**: Public client protection enabled with S256 challenge method
2. **Token Validation**: All OIDC tokens validated against Authelia's public JWKS
3. **Issuer Validation**: Token issuer claim must match configured OIDC_ISSUER_URL
4. **Audience Validation**: Token audience must include configured OIDC_AUDIENCE
5. **Expiration Validation**: Expired tokens are rejected
6. **No Password Storage**: OIDC-created users have NULL password_hash
7. **User Isolation**: Each user only accesses their own notes (backend enforces)

## Database Migrations

Required schema changes:
```sql
ALTER TABLE users ADD COLUMN oidc_sub VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN email VARCHAR(255);
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
```

Note: Auto-migration via SQLAlchemy will apply these changes on backend startup

## Known Limitations & Future Enhancements

1. **Token Revocation**: Not yet implemented. Consider Redis-based blacklist for future.
2. **Multi-Language**: Authelia username claims hardcoded to English
3. **Account Linking**: Cannot yet link local and OIDC accounts for same user
4. **Email Verification**: No email verification for OIDC users
5. **Metadata Refresh**: User metadata not updated on subsequent OIDC logins

## Files Modified/Created

**Modified**:
- `backend/app/auth/dependencies.py` - Hybrid auth implementation
- `backend/app/models/models.py` - OIDC support fields
- `backend/pyproject.toml` - Added httpx dependency
- `ui/package.json` - Added oidc-client-ts
- `ui/src/App.tsx` - Added callback route
- `ui/src/features/auth/components/LoginForm.tsx` - Added SSO button
- `ui/src/features/auth/store/auth.ts` - OIDC token support

**Created**:
- `backend/app/auth/oidc_validator.py` - OIDC validation module
- `backend/tests/unit/auth/test_oidc_validator.py` - Unit tests
- `backend/tests/integration/auth/test_oidc_hybrid_auth.py` - Integration tests
- `ui/src/config/oidc.ts` - OIDC configuration
- `ui/src/features/auth/utils/oidcUtils.ts` - OIDC utilities
- `ui/src/features/auth/components/OIDCCallback.tsx` - Callback handler
- `docs/AUTHELIA_OIDC_ENV.md` - Environment variable guide

## Deployment Steps

1. **Configure Authelia OIDC Client**:
   - Register "parchmark-web" as public OIDC client
   - Set redirect URIs (development + production)
   - Enable authorization_code and refresh_token grant types
   - Enable PKCE with S256

2. **Backend Deployment**:
   - Update `.env` with OIDC variables
   - Run database migrations
   - Restart backend service

3. **Frontend Deployment**:
   - Update `.env` with OIDC variables
   - Rebuild and deploy frontend

4. **Testing**:
   - Verify health endpoint: `GET /api/health`
   - Test local login still works
   - Test SSO login with Authelia
   - Verify auto-user creation on first OIDC login

## Next Steps

1. Apply database migrations
2. Update Authelia configuration with parchmark-web OIDC client
3. Set environment variables in production
4. Run test suite to verify all tests pass
5. Deploy backend first, then frontend
6. Test complete authentication flow end-to-end

## Documentation

- `docs/AUTHELIA_OIDC_PLAN.md` - High-level implementation plan
- `docs/AUTHELIA_OIDC_ENV.md` - Environment variable configuration guide
- `docs/AUTHELIA_OIDC_IMPLEMENTATION.md` - This file
