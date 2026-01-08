# Authelia OIDC Integration Patterns Guide

Comprehensive guide for integrating ParchMark's OIDC infrastructure with other applications and systems.

---

## Table of Contents

1. [Overview](#overview)
2. [Service-to-Service Authentication](#service-to-service-authentication)
3. [Third-Party Application Integration](#third-party-application-integration)
4. [Mobile App Integration](#mobile-app-integration)
5. [Multi-Tenant OIDC](#multi-tenant-oidc)
6. [Account Linking & Delegation](#account-linking--delegation)
7. [Legacy Application Bridge](#legacy-application-bridge)
8. [API Gateway Integration](#api-gateway-integration)

---

## Overview

### Integration Scenarios

```
┌─────────────────────────────────────────────────────────────┐
│ Authelia OIDC Provider                                      │
│ (Central Authentication Source)                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┼────────────┬──────────────┐
        │         │            │              │
    ┌───▼──┐  ┌──▼──┐  ┌─────▼───┐  ┌──────▼───┐
    │Parch │  │Other│  │Mobile  │  │Legacy   │
    │Mark  │  │Web  │  │App     │  │System   │
    │      │  │App  │  │        │  │Bridge   │
    └──────┘  └─────┘  └────────┘  └─────────┘
```

### Common Integration Patterns

1. **Service-to-Service**: Microservices authenticating with each other
2. **Third-Party SaaS**: Integrating with external services via OAuth2
3. **Mobile Apps**: Native and React Native applications
4. **Multi-Tenant**: Supporting multiple organizations via Authelia
5. **Account Linking**: Federated identity across systems
6. **Legacy Bridge**: Authenticating old systems via OIDC

---

## Service-to-Service Authentication

### Backend Service Calling Another Service

**Scenario**: ParchMark backend needs to call an external service

**Implementation**:

```python
# backend/app/services/external_service.py
import httpx
from datetime import datetime, timedelta
import jwt

class ExternalServiceClient:
    def __init__(self, issuer_url: str, client_id: str, client_secret: str):
        self.issuer_url = issuer_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None

    async def get_access_token(self) -> str:
        # Return cached token if still valid
        if self.access_token and self.token_expires_at > datetime.utcnow():
            return self.access_token

        # Get new token via client credentials flow
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.issuer_url}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "openid profile email"
                }
            )

            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 10)

            return self.access_token

    async def call_service(self, endpoint: str, method: str = "GET", **kwargs) -> dict:
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {token}"
            kwargs["headers"] = headers

            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()

# Usage
external_service = ExternalServiceClient(
    issuer_url="https://auth.engen.tech",
    client_id="backend-service",
    client_secret=os.getenv("BACKEND_SERVICE_SECRET")
)

# Call external service
result = await external_service.call_service(
    "https://analytics-api.example.com/events",
    method="POST",
    json={"user_id": user.id, "action": "note_created"}
)
```

### Authelia Configuration for Service-to-Service

Add to `authelia/configuration.yml`:

```yaml
identity_providers:
  oidc:
    clients:
      - id: backend-service
        client_name: "Backend Service"
        kind: public  # Use private if backend is server-side
        consent_mode: implicit  # No user interaction needed
        grant_types:
          - client_credentials
          - refresh_token
        public: false  # Confidential client
        secret: "${BACKEND_SERVICE_SECRET}"  # Keep in secrets
        redirect_uris: []  # Not applicable for client_credentials
        scopes:
          - openid
          - profile
          - email
        token_endpoint_auth_method: client_secret_basic
```

---

## Third-Party Application Integration

### Generic OAuth2/OIDC SaaS Integration

**Example**: Integrating Zapier or other automation service

**Process**:

1. **Authelia Configuration**:
```yaml
identity_providers:
  oidc:
    clients:
      - id: zapier
        client_name: "Zapier Integration"
        public: true
        kind: public
        redirect_uris:
          - "https://zapier.com/oauth/callback"
        scopes:
          - openid
          - profile
          - email
        grant_types:
          - authorization_code
          - refresh_token
```

2. **Frontend Integration** (if needed):
```typescript
// Connect Zapier OAuth flow
const zapierAuthUrl = `${OIDC_ISSUER_URL}/authorization?
  client_id=zapier
  &redirect_uri=${encodeURIComponent('https://zapier.com/oauth/callback')}
  &response_type=code
  &scope=openid+profile+email
  &state=${generateState()}`;

window.location.href = zapierAuthUrl;
```

### Protected API with OIDC Token Validation

**Backend**:

```python
from fastapi import Depends, HTTPException
from app.auth.oidc_validator import OIDCValidator

oauth2_scheme = HTTPBearer()

async def verify_oidc_token(credentials: HTTPAuthCredentials = Depends(oauth2_scheme)):
    validator = OIDCValidator()
    try:
        claims = await validator.validate_oidc_token(credentials.credentials)
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/integrations/webhook")
async def webhook_handler(
    data: dict,
    claims: dict = Depends(verify_oidc_token)
):
    # Process webhook from authenticated third-party service
    return {"status": "processed", "user": claims.get("sub")}
```

---

## Mobile App Integration

### React Native / Flutter OIDC Flow

**Using `react-native-app-auth`**:

```typescript
// mobile/src/services/oidcAuth.ts
import * as AppAuth from 'react-native-app-auth';

const oidcConfig = {
  clientId: 'parchmark-mobile',
  clientSecret: 'mobile-secret',
  redirectUrl: 'com.parchmark.mobile://oauth/callback',
  discoveryUrl: 'https://auth.engen.tech/.well-known/openid-configuration',
  scopes: ['openid', 'profile', 'email', 'offline_access'],
  serviceConfiguration: {
    authorizationEndpoint: 'https://auth.engen.tech/authorization',
    tokenEndpoint: 'https://auth.engen.tech/token',
    revocationEndpoint: 'https://auth.engen.tech/revocation',
  }
};

export async function login() {
  try {
    const result = await AppAuth.authorize(oidcConfig);

    // Store tokens securely
    await SecureStore.setItemAsync('access_token', result.accessToken);
    await SecureStore.setItemAsync('refresh_token', result.refreshToken);
    await SecureStore.setItemAsync('id_token', result.idToken);

    return result;
  } catch (error) {
    console.error('OIDC login failed', error);
    throw error;
  }
}

export async function refreshToken() {
  const refreshToken = await SecureStore.getItemAsync('refresh_token');

  const result = await AppAuth.refresh(oidcConfig, {
    refreshToken
  });

  await SecureStore.setItemAsync('access_token', result.accessToken);

  return result;
}

export async function logout() {
  try {
    const idToken = await SecureStore.getItemAsync('id_token');

    await AppAuth.revoke(oidcConfig, {
      tokenToRevoke: idToken,
      isIdToken: true
    });
  } finally {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await SecureStore.deleteItemAsync('id_token');
  }
}
```

**Authelia Configuration**:

```yaml
identity_providers:
  oidc:
    clients:
      - id: parchmark-mobile
        client_name: "ParchMark Mobile"
        public: true
        kind: public
        redirect_uris:
          - "com.parchmark.mobile://oauth/callback"
          - "com.parchmark.mobile.dev://oauth/callback"  # Dev variant
        scopes:
          - openid
          - profile
          - email
          - offline_access  # For refresh tokens
        token_endpoint_auth_method: none  # Public client, no secret
        grant_types:
          - authorization_code
          - refresh_token
```

---

## Multi-Tenant OIDC

### Supporting Multiple Organizations

**Scenario**: ParchMark hosts multiple customer organizations

**Implementation**:

```python
# backend/app/models/tenant.py
from sqlalchemy import Column, String, Integer

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    oidc_client_id = Column(String, unique=True)
    oidc_issuer_url = Column(String)  # Custom issuer per tenant
    features = Column(JSON)  # Tenant-specific features

# backend/app/models/user.py
class User(Base):
    # ... existing fields ...
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tenant = relationship("Tenant")

# backend/app/auth/multi_tenant_oidc.py
class MultiTenantOIDCValidator:
    async def validate_oidc_token_for_tenant(
        self,
        token: str,
        tenant_id: int
    ) -> dict:
        tenant = await get_tenant(tenant_id)

        # Use tenant-specific OIDC config
        validator = OIDCValidator(
            issuer_url=tenant.oidc_issuer_url,
            client_id=tenant.oidc_client_id
        )

        return await validator.validate_oidc_token(token)

# backend/app/routers/auth.py
@app.post("/api/{tenant_id}/auth/login")
async def tenant_oidc_login(
    tenant_id: int,
    code: str,
    session_state: str = None
):
    multi_tenant_validator = MultiTenantOIDCValidator()

    # Exchange code for tokens using tenant's OIDC config
    token_response = await exchange_code(code, tenant_id)

    # Validate token
    claims = await multi_tenant_validator.validate_oidc_token_for_tenant(
        token_response['access_token'],
        tenant_id
    )

    # Create/find user in tenant
    user = await get_or_create_tenant_user(
        tenant_id=tenant_id,
        oidc_sub=claims['sub'],
        email=claims.get('email')
    )

    return {"access_token": create_local_jwt(user)}
```

**Frontend**:

```typescript
// ui/src/services/multiTenantAuth.ts
export async function getTenantOIDCConfig(tenantId: string) {
  const response = await fetch(`/api/${tenantId}/oidc/config`);
  return response.json();
}

export async function initTenantOIDC(tenantId: string) {
  const config = await getTenantOIDCConfig(tenantId);

  return new UserManager({
    authority: config.issuer_url,
    client_id: config.client_id,
    redirect_uri: `${window.location.origin}/oidc/callback/${tenantId}`,
    // ... other config
  });
}
```

---

## Account Linking & Delegation

### Linking OIDC Accounts to Existing Local Users

**Implementation**:

```python
# backend/app/routers/auth.py

@app.post("/api/auth/link-oidc-account")
async def link_oidc_account(
    current_user: User = Depends(get_current_active_user),
    token: str = Body(...)
):
    """Link an OIDC account to current local user"""

    # Validate OIDC token
    validator = OIDCValidator()
    claims = await validator.validate_oidc_token(token)

    # Check if OIDC account already linked
    existing = await db.query(User).filter(
        User.oidc_sub == claims['sub']
    ).first()

    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="OIDC account already linked")

    # Link account
    current_user.oidc_sub = claims['sub']
    current_user.email = claims.get('email', current_user.email)
    current_user.auth_provider = 'hybrid'

    db.commit()

    return {"status": "linked", "oidc_sub": claims['sub']}

@app.post("/api/auth/unlink-oidc-account")
async def unlink_oidc_account(
    current_user: User = Depends(get_current_active_user)
):
    """Unlink OIDC account, keep local auth"""

    if current_user.auth_provider != 'hybrid':
        raise HTTPException(status_code=400, detail="Account not linked")

    # Keep password_hash, just remove OIDC fields
    current_user.oidc_sub = None
    current_user.auth_provider = 'local'

    db.commit()

    return {"status": "unlinked"}
```

**Frontend**:

```typescript
// ui/src/features/account/components/LinkedAccounts.tsx
export function LinkedAccounts() {
  const { user } = useAuthStore();

  const handleLinkOIDC = async () => {
    try {
      // Start OIDC flow for linking
      await startOIDCLogin();

      // On callback, exchange for token
      const token = await getOIDCToken();

      // Send to backend
      await fetch('/api/auth/link-oidc-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      showSuccessMessage('Account linked');
    } catch (error) {
      showErrorMessage('Failed to link account');
    }
  };

  return (
    <Box>
      {user?.oidc_sub && (
        <Box>
          <Text>OIDC account linked</Text>
          <Button onClick={handleUnlink}>Unlink</Button>
        </Box>
      )}
      {!user?.oidc_sub && (
        <Button onClick={handleLinkOIDC}>Link OIDC Account</Button>
      )}
    </Box>
  );
}
```

---

## Legacy Application Bridge

### Bridging to Systems Without OIDC Support

**Pattern**: Legacy system with basic HTTP authentication

```python
# backend/app/integrations/legacy_bridge.py
from functools import wraps
import hashlib

class LegacyApplicationBridge:
    def __init__(self, legacy_system_url: str, api_key: str):
        self.legacy_system_url = legacy_system_url
        self.api_key = api_key

    async def authenticate_legacy_user(self, username: str, password: str) -> dict:
        """Authenticate against legacy system and provision in ParchMark"""

        async with httpx.AsyncClient() as client:
            # Call legacy authentication endpoint
            response = await client.post(
                f"{self.legacy_system_url}/api/auth/login",
                auth=(username, password)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user_data = response.json()

            # Provision user in ParchMark if not exists
            legacy_id = user_data['id']
            oidc_sub = f"legacy:{legacy_id}"

            user = await db.query(User).filter(
                User.oidc_sub == oidc_sub
            ).first()

            if not user:
                user = User(
                    username=user_data['username'],
                    email=user_data.get('email'),
                    oidc_sub=oidc_sub,
                    auth_provider='federated',
                    password_hash=None
                )
                db.add(user)
                db.commit()

            return user

# Usage in auth router
legacy_bridge = LegacyApplicationBridge(
    legacy_system_url="https://legacy-app.example.com",
    api_key=os.getenv("LEGACY_API_KEY")
)

@app.post("/api/auth/login-legacy")
async def login_legacy(request: LoginRequest):
    user = await legacy_bridge.authenticate_legacy_user(
        request.username,
        request.password
    )

    token = create_access_token(user)
    return {"access_token": token}
```

---

## API Gateway Integration

### Kong API Gateway with OIDC

**Kong Configuration**:

```yaml
# Kong service protecting backend
services:
  - name: parchmark-backend
    url: http://parchmark-backend:8000

routes:
  - name: backend-route
    service: parchmark-backend
    paths:
      - /api

plugins:
  - name: openid-connect
    service: parchmark-backend
    config:
      client_id: kong-gateway
      client_secret: ${KONG_CLIENT_SECRET}
      discovery: https://auth.engen.tech/.well-known/openid-configuration
      scopes:
        - openid
        - profile
        - email
      auth_methods:
        - authorization_code
        - bearer_token
      preserve_client_credentials: false
      use_pkce: true
      cache_ttl: 3600
```

### Nginx with OIDC

**Nginx configuration**:

```nginx
server {
    listen 80;
    server_name assets-api.engen.tech;

    location ~ ^/api/ {
        # Verify OIDC token
        proxy_pass http://parchmark-backend:8000;

        # Forward OIDC claims as headers
        proxy_set_header X-OIDC-Sub $oidc_claim_sub;
        proxy_set_header X-OIDC-Email $oidc_claim_email;
        proxy_set_header X-OIDC-Name $oidc_claim_name;
    }

    location / {
        # Public endpoints don't require auth
        proxy_pass http://parchmark-backend:8000;
    }
}
```

---

## Common Integration Patterns

### Pattern 1: Webhook to External Service

**ParchMark → External Service**:

```python
# When note is created, notify external service
@app.post("/api/notes")
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_active_user)
):
    note = Note(**note_data.dict(), user_id=current_user.id)
    db.add(note)
    db.commit()

    # Notify external service with OIDC token
    try:
        external_client = ExternalServiceClient(...)
        await external_client.call_service(
            "https://webhooks.example.com/note-created",
            method="POST",
            json={"note_id": note.id, "user": current_user.username}
        )
    except Exception as e:
        logger.error(f"Webhook notification failed: {e}")
        # Don't fail the note creation

    return note
```

### Pattern 2: Cross-Origin Token Exchange

**Frontend → Third-Party Service**:

```typescript
// Request ParchMark backend to exchange token for third-party
const response = await fetch('/api/auth/exchange-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    target_service: 'slack',
    scopes: ['chat:write']
  })
});

const { external_token } = await response.json();

// Use external token with third-party service
await fetch('https://slack.com/api/chat.postMessage', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${external_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ channel: 'C123', text: 'Hello' })
});
```

---

## Security Considerations

### Token Validation in Integrations

1. **Always validate token signature**
2. **Check expiration and not-before times**
3. **Verify issuer URL matches expected**
4. **Validate audience claim matches your service**
5. **Use HTTPS for all token exchanges**

### Secrets Management

```python
# Use environment variables or secrets manager
from decouple import config

EXTERNAL_SERVICE_SECRET = config('EXTERNAL_SERVICE_SECRET')
OIDC_CLIENT_SECRET = config('OIDC_CLIENT_SECRET')

# Never log or expose secrets
logger.info(f"Connecting to service: {service_url}")  # OK
logger.info(f"Using secret: {secret}")  # BAD - never log secrets
```

---

## See Also

- **AUTHELIA_OIDC_ADVANCED_SCENARIOS.md** - Advanced patterns
- **AUTHELIA_OIDC_API_REFERENCE.md** - API endpoints
- **AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md** - Backend implementation
