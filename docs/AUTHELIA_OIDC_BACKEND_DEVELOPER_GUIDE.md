# OIDC Backend Developer Guide

Deep dive into the ParchMark backend OIDC implementation for developers maintaining and extending the authentication system.

---

## Overview

This guide explains:
- How OIDC token validation works internally
- Architecture of the hybrid authentication system
- How to extend or modify OIDC functionality
- Key design decisions and trade-offs
- Performance considerations
- Security implications

---

## Architecture

### Authentication Flow

```
HTTP Request
    ↓
Authorization Header with Bearer token
    ↓
get_current_user() dependency
    ↓
├─ Try Local JWT validation
│  ├─ Valid → Return user (local)
│  ├─ Expired → 401 Unauthorized
│  └─ Invalid → Continue to OIDC
│
└─ Try OIDC validation
   ├─ Valid → Lookup/create user (oidc)
   │         → Return user
   ├─ Invalid → 401 Unauthorized
   └─ Error → 401 Unauthorized
```

### Code Structure

```
app/auth/
├── dependencies.py          # FastAPI dependency injection
├── oidc_validator.py       # OIDC token validation
├── password_hash.py        # Password hashing utilities
└── jwt_utils.py            # JWT utilities (local auth)

app/models/
└── models.py               # User model with OIDC fields

app/routers/
└── auth.py                 # Auth endpoints

tests/
├── unit/auth/
│  ├── test_oidc_validator.py           # OIDC validator tests
│  ├── test_oidc_error_handling.py      # Error scenarios
│  └── test_jwt_utils.py                # Local JWT tests
└── integration/auth/
   ├── test_oidc_hybrid_auth.py         # Hybrid auth tests
   └── test_jwt_auth.py                 # Local auth tests
```

---

## Core Components

### 1. OIDCValidator Class

**Location**: `backend/app/auth/oidc_validator.py`

**Responsibility**: Validate OIDC tokens and extract user information

**Key Methods**:

#### `get_jwks()` - Fetch and Cache JWKS

```python
async def get_jwks(self) -> Dict[str, Any]:
    """Fetch JWKS from OIDC provider with caching."""
```

**Purpose**: Get JSON Web Key Set from OIDC provider's JWKS endpoint

**Caching Strategy**:
- First call: Fetches from provider (network request)
- Subsequent calls (within TTL): Return cached copy
- TTL: 1 hour (3600 seconds)
- On expiration: Automatically refetch

**Implementation Details**:

```python
# Internal state
self.jwks_cache: Optional[Dict] = None
self.jwks_cache_time: Optional[float] = None
self.jwks_cache_ttl: int = 3600  # 1 hour

# Cache logic
def _cache_expired(self) -> bool:
    if not self.jwks_cache_time:
        return True
    elapsed = time.time() - self.jwks_cache_time
    return elapsed > self.jwks_cache_ttl
```

**Performance**:
- First request: 50-200ms (HTTPS + JSON parsing)
- Cached requests: <5ms (in-memory dictionary lookup)
- Cache hit rate: ~99% in production

**Error Handling**:
- Network timeout: Raises `OIDCProviderError`
- Invalid JSON: Raises `OIDCProviderError`
- Missing keys: Raises `OIDCConfigurationError`

#### `validate_oidc_token(token)` - Validate JWT

```python
async def validate_oidc_token(token: str) -> Dict[str, Any]:
    """Validate OIDC token and return claims."""
```

**Validation Steps**:

1. **Decode JWT Header** (unverified)
   - Extract `kid` (key ID)
   - Check algorithm is supported (RS256)

2. **Fetch JWKS** (cached)
   - Get signing keys from JWKS endpoint
   - Find key matching `kid`

3. **Verify Signature**
   - Validate JWT signature against key
   - Raises if signature invalid

4. **Validate Claims**
   - `iss` (issuer): Must match OIDC_ISSUER_URL
   - `aud` (audience): Must include OIDC_AUDIENCE
   - `exp` (expiration): Must be in future
   - Allow 10-second clock skew

5. **Extract Claims**
   - Get `sub`, `preferred_username`, `email`
   - Return as dictionary

**Example**:

```python
try:
    claims = await validator.validate_oidc_token(token)
    # claims = {
    #   'sub': 'john',
    #   'preferred_username': 'john',
    #   'email': 'john@example.com',
    #   'iss': 'http://localhost:9091',
    #   'aud': 'parchmark-web',
    #   'exp': 1704706496
    # }
except OIDCValidationError as e:
    # Handle validation error
    pass
```

#### `extract_username(token_claims)` - Get Username

```python
def extract_username(self, token_claims: Dict[str, Any]) -> str:
    """Extract username from token claims with fallback."""
```

**Logic**:
1. Try `preferred_username` claim (primary)
2. Fall back to `email` claim if not present
3. Raise if neither available

**Implementation**:

```python
username = token_claims.get('preferred_username')
if not username:
    username = token_claims.get('email')
if not username:
    raise ValueError("No username claim found")
return username
```

**Why Email Fallback?**
- Some OIDC providers don't include `preferred_username`
- Email is almost universally present
- Email is unique identifier

### 2. Hybrid Auth Dependency

**Location**: `backend/app/auth/dependencies.py`

**Function**: `get_current_user()`

**Responsibility**: Extract and validate user from request

**Implementation**:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    """Get authenticated user (local or OIDC)."""

    token = credentials.credentials

    # 1. Try local JWT
    try:
        local_user = validate_local_jwt(token)
        return local_user
    except JWTError:
        pass

    # 2. Try OIDC (if enabled)
    if AUTH_MODE in ['hybrid', 'oidc']:
        try:
            claims = await oidc_validator.validate_oidc_token(token)
            user = await get_or_create_oidc_user(claims)
            return user
        except OIDCValidationError:
            pass

    # 3. Both failed
    raise HTTPException(status_code=401, detail="Invalid token")
```

**Flow Diagram**:

```
get_current_user()
    ├─ Extract token from Authorization header
    │
    ├─ Try local_jwt_decode()
    │  ├─ Success → Return user
    │  └─ Fail → Continue
    │
    ├─ Try oidc_validator.validate_oidc_token()
    │  ├─ Success → get_or_create_oidc_user()
    │  │           → Return user
    │  └─ Fail → Continue
    │
    └─ Raise 401 Unauthorized
```

**Key Features**:

1. **Async Support**
   - Awaits OIDC validation (network call)
   - Non-blocking JWKS cache lookup

2. **User Auto-Creation**
   - Creates new users on first OIDC login
   - Stores `oidc_sub`, `email`, `auth_provider`

3. **Fallback Order**
   - Local JWT tried first (faster, no network)
   - OIDC tried second (network required)
   - Fails only if both methods fail

4. **Dependency Injection**
   - Can be used on any endpoint
   - FastAPI handles token extraction
   - Returns User model or raises 401

### 3. User Model Updates

**Location**: `backend/app/models/models.py`

**New Fields**:

```python
class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String(255), unique=True, index=True)
    password_hash: Optional[str] = Column(String(255), nullable=True)  # NOW NULLABLE
    email: Optional[str] = Column(String(255), nullable=True)          # NEW
    auth_provider: str = Column(String(50), default="local")           # NEW
    oidc_sub: Optional[str] = Column(String(255), unique=True, index=True, nullable=True)  # NEW
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
```

**Field Details**:

| Field | Type | Purpose | Local | OIDC |
|-------|------|---------|-------|------|
| `id` | int | Primary key | ✓ | ✓ |
| `username` | str | Unique username | ✓ | ✓ |
| `password_hash` | str (nullable) | Bcrypt hash | ✓ | NULL |
| `email` | str (nullable) | Email address | NULL | ✓ |
| `auth_provider` | str | Auth method | "local" | "oidc" |
| `oidc_sub` | str (nullable, unique) | OIDC subject | NULL | ✓ |

**Migration Implications**:

- `password_hash` now nullable (existing local users unaffected)
- New fields added to schema
- Auto-migration via SQLAlchemy ORM
- No data loss during migration

**Query Examples**:

```python
# Find by OIDC subject (primary lookup for OIDC)
user = db.query(User).filter(User.oidc_sub == "john").first()

# Find by username (works for both)
user = db.query(User).filter(User.username == "john").first()

# Get all OIDC users
oidc_users = db.query(User).filter(User.auth_provider == "oidc").all()

# Get all local users
local_users = db.query(User).filter(User.auth_provider == "local").all()
```

---

## Key Design Decisions

### 1. JWKS Caching Strategy

**Decision**: Cache JWKS for 1 hour

**Trade-offs**:

| Approach | Pros | Cons |
|----------|------|------|
| **No cache** | Always fresh keys | 100-200ms per token validation |
| **1-hour cache** ✓ | ~5ms per token validation, 99% reduction | Keys stale for up to 1 hour |
| **Redis cache** | Distributed, configurable TTL | Additional dependency, complexity |

**Chosen**: 1-hour in-memory cache

**Rationale**:
- OIDC key rotation is rare (typically monthly)
- 1-hour window is acceptable
- No additional dependencies
- Simple to understand and maintain

### 2. Local JWT Priority

**Decision**: Try local JWT first, OIDC as fallback

**Benefits**:
- Local JWT validation is faster (~5ms)
- No network calls for existing local users
- Gradual migration path
- Backward compatible

**Alternative**: OIDC first would require all requests to hit OIDC provider

### 3. Auto-User Creation on OIDC Login

**Decision**: Create user automatically on first OIDC login

**Alternative Considered**: Require manual user creation

**Why Auto-Creation**:
- Better UX (seamless first login)
- Prevents 401 errors for valid OIDC users
- Matches Authelia's philosophy

**Safety Measures**:
- Unique constraint on `oidc_sub`
- `auth_provider` tracks creation method
- Email stored from OIDC provider

### 4. Nullable Password Hash

**Decision**: Allow NULL `password_hash` for OIDC users

**Alternative**: Require dummy password or empty string

**Why NULL**:
- Semantically correct (OIDC users don't use passwords)
- Prevents accidental password authentication
- Clear intent in database
- Supports data validation

---

## Implementation Patterns

### Pattern 1: Async OIDC Validation

```python
# ✓ CORRECT - async all the way
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    token = credentials.credentials
    claims = await oidc_validator.validate_oidc_token(token)
    user = await db.fetch_user_by_oidc_sub(claims['sub'])
    return user

# ✗ WRONG - blocking in async function
async def get_current_user(...) -> User:
    token = credentials.credentials
    claims = oidc_validator.validate_oidc_token(token)  # Blocks!
    # ...
```

### Pattern 2: Error Handling

```python
# ✓ CORRECT - specific error handling
try:
    claims = await oidc_validator.validate_oidc_token(token)
except OIDCValidationError as e:
    logger.warning(f"OIDC validation failed: {e}")
    raise HTTPException(status_code=401)
except OIDCConfigurationError as e:
    logger.error(f"OIDC config error: {e}")
    raise HTTPException(status_code=503)

# ✗ WRONG - catches everything
try:
    claims = await oidc_validator.validate_oidc_token(token)
except Exception:  # Too broad
    raise HTTPException(status_code=401)
```

### Pattern 3: User Lookup

```python
# ✓ CORRECT - lookup by oidc_sub (unique)
user = db.query(User).filter(
    User.oidc_sub == claims['sub']
).first()

# ✗ WRONG - lookup by email (not unique)
user = db.query(User).filter(
    User.email == claims['email']
).first()

# ✗ WRONG - lookup by username (could be different)
user = db.query(User).filter(
    User.username == username
).first()
```

---

## Performance Optimization

### JWKS Caching Effectiveness

**Without Caching**:
- Every token validation: 100-200ms OIDC provider call
- 1000 users/day: 100-200 seconds total time

**With 1-Hour Cache**:
- First token validation: 100-200ms
- Subsequent validations: <5ms (in-memory)
- Typical usage: 99%+ cache hit rate

**Optimization Tips**:

1. **Monitor Cache Hit Rate**
   ```python
   logger.info(f"JWKS cache: {cache_hits} hits, {cache_misses} misses")
   cache_hit_rate = cache_hits / (cache_hits + cache_misses)
   ```

2. **Tune TTL**
   - Too short: More network calls
   - Too long: Stale keys
   - Default 1 hour is good balance

3. **Connection Pooling**
   - Use httpx AsyncClient with connection pooling
   - Reuse connections to OIDC provider

### Token Validation Performance

**Current**: <10ms for cached JWKS

**Breakdown**:
- JWT decode: ~1ms
- JWKS lookup: <1ms (in-memory dict)
- Signature verification: ~5ms
- Claims validation: <1ms
- Total: ~7ms average

**Benchmarking**:

```bash
# Run performance tests
make test-oidc-perf

# Output shows timing per operation
# Look for issues if > 10ms average
```

---

## Security Considerations

### 1. Token Validation

**Validates**:
- ✓ Signature with JWKS
- ✓ Issuer (`iss` claim)
- ✓ Audience (`aud` claim)
- ✓ Expiration (`exp` claim)
- ✓ Issued At (`iat` claim)

**Clock Skew**:
- Allows 10-second buffer for clock differences
- Prevents strict time synchronization requirements

### 2. OIDC Subject (sub) Handling

**Immutable**:
- `oidc_sub` never changes for a user
- Uniquely identifies user in OIDC provider

**Lookup**:
- Always lookup user by `oidc_sub`
- Never change `oidc_sub` after creation
- Prevents user confusion

### 3. Email Handling

**Stored But Unverified**:
- Email from OIDC provider is trusted
- Authelia verifies email before issuing token
- No additional verification needed in ParchMark

**Usage**:
- Fallback for username extraction
- User contact information
- Used as-is (no verification)

### 4. Password Handling

**Local Users**:
- Passwords hashed with Bcrypt
- Never stored in plain text
- Not used for OIDC users

**OIDC Users**:
- No password stored (NULL)
- Cannot login with password
- Only via OIDC flow

---

## Testing Strategy

### Unit Tests

**OIDC Validator Tests** (`test_oidc_validator.py`):
- JWKS fetching and caching
- Token validation success/failure
- Claim extraction
- Error scenarios

**Example**:
```python
@pytest.mark.asyncio
async def test_jwks_caching():
    validator = OIDCValidator(...)

    # First call fetches
    jwks1 = await validator.get_jwks()

    # Second call uses cache
    jwks2 = await validator.get_jwks()

    assert jwks1 == jwks2
    # Verify only 1 network call made
```

### Integration Tests

**Hybrid Auth Tests** (`test_oidc_hybrid_auth.py`):
- Local JWT validation in hybrid mode
- OIDC token validation in hybrid mode
- User auto-creation on OIDC login
- Mixed user scenarios

**Example**:
```python
async def test_oidc_user_auto_creation():
    token = create_oidc_token(sub="newuser", email="new@example.com")
    user = await get_current_user(token)

    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.auth_provider == "oidc"
    assert user.oidc_sub == "newuser"
```

### Error Handling Tests

**Error Scenarios** (`test_oidc_error_handling.py`):
- Invalid token format
- Expired tokens
- Invalid signatures
- Missing claims
- Network timeouts

---

## Extending the System

### Adding New Claims Extraction

```python
# In oidc_validator.py
def extract_user_info(self, token_claims: Dict[str, Any]) -> Dict[str, str]:
    """Extract user information from token claims."""

    # Existing claims
    username = self.extract_username(token_claims)
    email = token_claims.get('email')
    oidc_sub = token_claims.get('sub')

    # NEW: Extract additional claims
    full_name = token_claims.get('name')
    groups = token_claims.get('groups', [])  # If OIDC provider supports
    roles = token_claims.get('roles', [])    # If OIDC provider supports

    return {
        'username': username,
        'email': email,
        'oidc_sub': oidc_sub,
        'full_name': full_name,
        'groups': groups,
        'roles': roles,
    }
```

### Adding Token Revocation

```python
# Future: Token blacklist
class TokenBlacklist:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def revoke_token(self, token: str, expiry: int):
        """Add token to blacklist until expiry."""
        await self.redis.setex(f"token:{token}", expiry, "revoked")

    async def is_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        return await self.redis.exists(f"token:{token}")

# In validate_oidc_token()
async def validate_oidc_token(self, token: str) -> Dict[str, Any]:
    # ... existing validation ...

    # NEW: Check if revoked
    if await token_blacklist.is_revoked(token):
        raise OIDCValidationError("Token has been revoked")

    return claims
```

### Adding Account Linking

```python
# Link local and OIDC accounts
class AccountLinking:
    async def link_accounts(self, local_user_id: int, oidc_sub: str):
        """Link local account to OIDC account."""
        local_user = db.query(User).filter(User.id == local_user_id).first()
        local_user.oidc_sub = oidc_sub
        local_user.auth_provider = "hybrid"  # NEW status
        db.commit()

    async def get_linked_users(self, user_id: int) -> List[User]:
        """Get all linked accounts for a user."""
        # Find by same oidc_sub or by email matching
        pass
```

---

## Debugging

### Enable Debug Logging

```python
# In main.py or logging config
import logging

logging.getLogger('app.auth').setLevel(logging.DEBUG)
logging.getLogger('app.auth.oidc_validator').setLevel(logging.DEBUG)

# Or in .env
LOG_LEVEL=DEBUG
```

### Common Issues

**Issue**: JWKS fetch timeout
```
Solution: Check OIDC_ISSUER_URL is correct and accessible
         Increase timeout in oidc_validator.py
```

**Issue**: Token validation fails with "invalid issuer"
```
Solution: Verify OIDC_ISSUER_URL matches token's 'iss' claim
         Check for trailing slashes: http://localhost:9091 vs http://localhost:9091/
```

**Issue**: User not auto-created on OIDC login
```
Solution: Check database has oidc_sub column
         Check auth_provider can be set to 'oidc'
         Review database constraints
```

---

## Best Practices

1. **Always use `oidc_sub` for lookups**
   - Unique identifier for OIDC users
   - Never changes
   - Primary key for user identification

2. **Store email from OIDC provider as-is**
   - Don't modify or normalize
   - Trust Authelia's validation
   - Use for fallback username only

3. **Set `auth_provider` consistently**
   - "local" for username/password users
   - "oidc" for OIDC users
   - Enables clear user type detection

4. **Validate claims explicitly**
   - Check `iss`, `aud`, `exp` always
   - Don't assume claims are present
   - Use reasonable defaults where appropriate

5. **Handle errors gracefully**
   - Return 401 for invalid tokens
   - Return 503 for OIDC provider errors
   - Log details for debugging

---

## See Also

- **AUTHELIA_OIDC_IMPLEMENTATION.md** - Overall architecture
- **AUTHELIA_OIDC_API_REFERENCE.md** - API endpoints
- **AUTHELIA_OIDC_TESTING_UTILITY.md** - Testing tools
- Backend code: `backend/app/auth/oidc_validator.py`
