# OIDC API Endpoint Reference

Complete API reference for ParchMark authentication endpoints with local and OIDC support.

---

## Overview

ParchMark supports **two authentication methods**:

1. **Local Authentication**: Traditional username/password with JWT tokens
2. **OIDC Authentication**: Federated authentication via Authelia with OIDC tokens

Both methods can coexist (hybrid mode) and use the same API endpoints.

---

## Base URLs

| Environment | URL | Notes |
|-------------|-----|-------|
| Development | http://localhost:8000 | Local dev server |
| Docker Dev | http://backend:8000 | Docker Compose |
| Production | https://assets-api.engen.tech | Production server |

All examples use `http://localhost:8000` (development).

---

## Authentication Methods

### Local Authentication

**Flow**:
1. User submits username/password to `/api/auth/login`
2. Backend returns JWT tokens (access + refresh)
3. Client stores tokens
4. Client includes access token in API requests

**Token Format**: JWT (HS256 signed)

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### OIDC Authentication

**Flow**:
1. User clicks "Sign In with SSO"
2. Client redirects to Authelia authorization endpoint
3. User authenticates at Authelia
4. Authelia redirects back with authorization code
5. Client exchanges code for tokens (via OIDC client library)
6. Client stores tokens
7. Client includes access token in API requests

**Token Format**: JWT (RS256 signed by Authelia)

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## API Endpoints

### POST /api/auth/login

**Purpose**: Authenticate with username and password

**Authentication**: None required

**Request**:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "password123"
  }'
```

**Request Body**:

```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**:

```json
// 401 Unauthorized - Invalid credentials
{
  "detail": "Incorrect username or password"
}

// 422 Unprocessable Entity - Missing fields
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Username (required) |
| `password` | string | Password (required) |
| `access_token` | string | JWT token for API requests |
| `refresh_token` | string | JWT token for refresh |
| `token_type` | string | Always "bearer" |
| `expires_in` | integer | Seconds until expiration |

**Notes**:

- Only for **local authentication**
- OIDC users use Authelia's `/authorization` endpoint instead
- Credentials must be exact match
- Account must exist in local database

---

### POST /api/auth/refresh

**Purpose**: Refresh access token using refresh token

**Authentication**: None required

**Request**:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Request Body**:

```json
{
  "refresh_token": "string"
}
```

**Success Response (200)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**:

```json
// 401 Unauthorized - Invalid refresh token
{
  "detail": "Invalid refresh token"
}

// 422 Unprocessable Entity - Missing field
{
  "detail": [
    {
      "loc": ["body", "refresh_token"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `refresh_token` | string | Valid refresh token (required) |
| `access_token` | string | New access token |
| `expires_in` | integer | Seconds until new token expires |

**Auth Method**:

| Method | Behavior |
|--------|----------|
| **Local** | Uses provided refresh token, returns new access token |
| **OIDC** | Backend can use this, or client can use OIDC client renewal |

**Notes**:

- Valid refresh tokens only
- Expired refresh tokens return 401
- Returns only access token (not refresh token)
- OIDC users can also use OIDC client's `renewToken()` method

---

### GET /api/auth/me

**Purpose**: Get current authenticated user information

**Authentication**: Required (Bearer token)

**Request**:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Success Response (200)**:

**Local User**:

```json
{
  "id": 1,
  "username": "john",
  "email": null,
  "auth_provider": "local",
  "oidc_sub": null,
  "created_at": "2025-01-08T12:34:56Z"
}
```

**OIDC User**:

```json
{
  "id": 2,
  "username": "john@example.com",
  "email": "john@example.com",
  "auth_provider": "oidc",
  "oidc_sub": "john",
  "created_at": "2025-01-08T12:35:10Z"
}
```

**Error Responses**:

```json
// 401 Unauthorized - No token or invalid token
{
  "detail": "Not authenticated"
}

// 401 Unauthorized - Token expired
{
  "detail": "Token expired"
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User ID |
| `username` | string | Username |
| `email` | string (nullable) | User email (OIDC users only) |
| `auth_provider` | string | "local" or "oidc" |
| `oidc_sub` | string (nullable) | OIDC subject (OIDC users only) |
| `created_at` | ISO 8601 | Account creation timestamp |

**Notes**:

- Requires valid access token
- Works with both local and OIDC tokens
- Different response format for each auth method
- OIDC users have email, local users don't

---

### POST /api/auth/logout

**Purpose**: Logout current user

**Authentication**: Required (Bearer token)

**Request**:

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Success Response (200)**:

```json
{
  "message": "Logged out successfully"
}
```

**Error Responses**:

```json
// 401 Unauthorized
{
  "detail": "Not authenticated"
}
```

**Notes**:

- Backend clears session (if implemented)
- Client must also clear token from localStorage
- OIDC users should also call Authelia end_session endpoint:
  ```
  https://auth.engen.tech/logout?redirect_uri=http://localhost:5173/login
  ```

---

## Token Structure

### Local JWT (HS256)

**Header**:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload**:
```json
{
  "sub": "1",
  "username": "john",
  "iat": 1704702896,
  "exp": 1704704696,
  "token_type": "access"
}
```

**Example**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJqb2huIiwiaWF0IjoxNzA0NzAyODk2LCJleHAiOjE3MDQ3MDQ2OTZ9.xxxxx
```

**Verification**:
```bash
# Decode (without verification)
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...." | jq -R 'split(".") | .[1] | @base64d | fromjson'

# Output
# {
#   "sub": "1",
#   "username": "john",
#   "iat": 1704702896,
#   "exp": 1704704696
# }
```

---

### OIDC JWT (RS256)

**Header**:
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-1"
}
```

**Payload**:
```json
{
  "sub": "john",
  "preferred_username": "john",
  "email": "john@example.com",
  "iss": "http://localhost:9091",
  "aud": "parchmark-web",
  "iat": 1704702896,
  "exp": 1704706496
}
```

**Example**:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0xIn0.eyJzdWIiOiJqb2huIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiam9obiIsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6OTA5MSIsImF1ZCI6InBhcmNobWFyay13ZWIiLCJpYXQiOjE3MDQ3MDI4OTYsImV4cCI6MTcwNDcwNjQ5Nn0.xxxxx
```

**Key Differences**:

| Aspect | Local | OIDC |
|--------|-------|------|
| Algorithm | HS256 (symmetric) | RS256 (asymmetric) |
| Issuer | ParchMark backend | Authelia |
| Signing key | Backend secret | Authelia private key |
| User ID claim | `sub` (numeric) | `sub` (string) |
| Username claim | `username` | `preferred_username` |
| Email claim | Not included | `email` (if requested) |
| Validation | Compare signature with secret | Verify against JWKS |

---

## Common API Workflows

### Workflow 1: Local Login → API Request → Refresh Token

**Step 1: Login**

```bash
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "password123"
  }')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

echo "Access token: $ACCESS_TOKEN"
echo "Refresh token: $REFRESH_TOKEN"
```

**Step 2: Make Authenticated Request**

```bash
curl -X GET http://localhost:8000/api/notes \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Step 3: Refresh When Token Expires**

```bash
REFRESH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }")

NEW_ACCESS_TOKEN=$(echo $REFRESH_RESPONSE | jq -r '.access_token')
echo "New access token: $NEW_ACCESS_TOKEN"
```

---

### Workflow 2: OIDC Callback → Token Storage → API Request

**Step 1: Authelia Redirects Back**

Frontend receives callback at `/oidc/callback?code=AUTH_CODE&state=STATE`

**Step 2: Exchange Code for Tokens** (handled by oidc-client-ts)

```javascript
const manager = new UserManager(OIDC_CONFIG);
const user = await manager.signinCallback();
// user.access_token is the OIDC token
```

**Step 3: Make Authenticated Request**

```javascript
const headers = {
  'Authorization': `Bearer ${user.access_token}`
};
const response = await fetch('/api/notes', { headers });
```

**Step 4: Automatic Token Refresh** (handled by oidc-client-ts)

```javascript
// Automatic silent renewal
const renewedUser = await manager.signinSilent();
// New access token available
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing/invalid token or credentials |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Validation Error | Invalid input data |
| 500 | Server Error | Backend error |
| 503 | Service Unavailable | Backend down or overloaded |

### Error Response Format

```json
{
  "detail": "string describing error"
}

// Or for validation errors:
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

---

## Token Expiration Handling

### Access Token Expiration

**Default TTL**: 30 minutes

**Behavior**:
1. Token expires after 30 minutes
2. API returns 401 Unauthorized
3. Client should use refresh token to get new access token
4. Frontend auto-refreshes before expiration (60-second warning)

**Example**:
```bash
# Token valid
curl -X GET http://localhost:8000/api/notes \
  -H "Authorization: Bearer VALID_TOKEN"
# Returns 200

# Token expired (after 30 minutes)
curl -X GET http://localhost:8000/api/notes \
  -H "Authorization: Bearer EXPIRED_TOKEN"
# Returns 401: "Token expired"

# Refresh and try again
REFRESH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN"}')
NEW_TOKEN=$(echo $REFRESH_RESPONSE | jq -r '.access_token')

# Retry with new token
curl -X GET http://localhost:8000/api/notes \
  -H "Authorization: Bearer $NEW_TOKEN"
# Returns 200
```

### Refresh Token Expiration

**Default TTL**: 7 days

**Behavior**:
1. Refresh token expires after 7 days
2. API returns 401 Unauthorized on refresh attempt
3. User must login again

---

## Authentication Comparison

### Local vs OIDC

| Feature | Local | OIDC |
|---------|-------|------|
| **Endpoint** | `/api/auth/login` | Authelia `/authorization` |
| **Credentials** | Username/password | Browser SSO |
| **Token Algorithm** | HS256 (symmetric) | RS256 (asymmetric) |
| **Token Issuer** | ParchMark backend | Authelia |
| **Validation** | Compare signature | Verify JWKS |
| **User Creation** | Manual via script | Auto on first login |
| **Token Format** | JWT with `username` | JWT with `preferred_username` |
| **Refresh Method** | `/api/auth/refresh` | OIDC client renewal or endpoint |
| **Email** | Optional field | Included in token |

---

## API Security

### Token Storage

**Recommended for SPA**:
- Access token: localStorage or memory
- Refresh token: secure cookie (HttpOnly) or localStorage

**ParchMark uses**:
- Both in localStorage for development/testing
- Consider secure cookies for production

### Token Transmission

**Always use**:
```
Authorization: Bearer <token>
```

**Never use**:
- URL query parameter
- Cookie (unless specifically set as HttpOnly)
- Custom headers

### CORS Headers

```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Credentials: true
```

---

## Rate Limiting

**Current Status**: Not implemented

**Recommendations for Production**:

```bash
# Per IP per minute
/api/auth/login: 5 requests/minute
/api/auth/refresh: 10 requests/minute
/api/notes: 60 requests/minute
```

---

## Testing Endpoints

### Health Check

```bash
curl -X GET http://localhost:8000/api/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "ParchMark API",
  "version": "1.0.0"
}
```

### OpenAPI Documentation

```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
http://localhost:8000/openapi.json  # OpenAPI spec
```

---

## Example Requests

### cURL

```bash
# Login locally
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"password123"}' | jq .

# Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# List notes
curl -X GET http://localhost:8000/api/notes \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
```

### JavaScript/Fetch

```javascript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john',
    password: 'password123'
  })
});
const data = await response.json();
const accessToken = data.access_token;

// Get current user
const userResponse = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
const user = await userResponse.json();
console.log(user);
```

### Python/Requests

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'john',
    'password': 'password123'
})
data = response.json()
access_token = data['access_token']

# Get current user
headers = {'Authorization': f'Bearer {access_token}'}
user_response = requests.get('http://localhost:8000/api/auth/me', headers=headers)
user = user_response.json()
print(user)
```

---

## See Also

- **AUTHELIA_OIDC_IMPLEMENTATION.md** - Technical implementation details
- **AUTHELIA_OIDC_LOCAL_TESTING.md** - Local testing guide
- **AUTHELIA_OIDC_TESTING_UTILITY.md** - Testing utility documentation
- **API Documentation**: http://localhost:8000/docs
