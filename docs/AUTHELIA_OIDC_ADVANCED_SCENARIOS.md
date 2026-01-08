# OIDC Advanced Scenarios

Advanced usage patterns and extensions for ParchMark OIDC implementation.

---

## Overview

This guide covers:
- Custom claim extraction
- Multi-provider support (future)
- Group-based authorization
- Custom username generation
- Token revocation
- Session management
- Advanced caching strategies
- Custom OIDC flows

---

## Advanced Scenario 1: Custom Claim Extraction

### Extracting Custom Claims from OIDC Token

**Use Case**: Access additional user attributes from OIDC provider

**Implementation**:

```python
# backend/app/auth/oidc_validator.py

class OIDCValidator:
    def extract_custom_claims(self, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Extract custom claims from OIDC token."""

        # Standard claims already validated
        username = self.extract_username(token_claims)

        # Custom claims extraction
        custom = {
            # Department/Organization
            'department': token_claims.get('department'),
            'organization': token_claims.get('org_id'),

            # Groups for authorization
            'groups': token_claims.get('groups', []),
            'roles': token_claims.get('roles', []),

            # Metadata
            'phone': token_claims.get('phone_number'),
            'display_name': token_claims.get('name'),
            'locale': token_claims.get('locale'),

            # Custom attributes
            'employee_id': token_claims.get('employee_id'),
            'cost_center': token_claims.get('cost_center'),
        }

        return custom

    async def validate_and_enrich_user(
        self, token_claims: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate token and enrich with custom claims."""

        # Standard validation
        claims = await self.validate_oidc_token(token_claims)

        # Extract custom claims
        custom = self.extract_custom_claims(claims)

        return {
            'username': self.extract_username(claims),
            'email': claims.get('email'),
            'oidc_sub': claims.get('sub'),
            'custom': custom,
        }
```

### Storing Custom Attributes

```python
# Extend User model
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...

    # Custom attributes
    department: Optional[str] = Column(String(255), nullable=True)
    organization: Optional[str] = Column(String(255), nullable=True)
    phone: Optional[str] = Column(String(20), nullable=True)
    display_name: Optional[str] = Column(String(255), nullable=True)
    employee_id: Optional[str] = Column(String(50), unique=True, nullable=True)
    cost_center: Optional[str] = Column(String(50), nullable=True)

    # JSON for flexible custom data
    custom_attributes: dict = Column(JSON, default={})
```

### Updating on Each Login

```python
async def get_or_create_oidc_user(
    db: Session, user_info: Dict[str, Any]
) -> User:
    """Get or create OIDC user with custom attributes."""

    user = db.query(User).filter(
        User.oidc_sub == user_info['oidc_sub']
    ).first()

    if user:
        # Update custom attributes on each login
        user.department = user_info['custom'].get('department')
        user.organization = user_info['custom'].get('organization')
        user.phone = user_info['custom'].get('phone')
        user.display_name = user_info['custom'].get('display_name')
        user.employee_id = user_info['custom'].get('employee_id')
        user.custom_attributes = user_info['custom']
        db.commit()
    else:
        # Create new user with custom attributes
        user = User(
            username=user_info['username'],
            email=user_info['email'],
            oidc_sub=user_info['oidc_sub'],
            auth_provider='oidc',
            password_hash=None,
            department=user_info['custom'].get('department'),
            organization=user_info['custom'].get('organization'),
            phone=user_info['custom'].get('phone'),
            display_name=user_info['custom'].get('display_name'),
            employee_id=user_info['custom'].get('employee_id'),
            custom_attributes=user_info['custom'],
        )
        db.add(user)
        db.commit()

    return user
```

---

## Advanced Scenario 2: Group-Based Authorization

### Using OIDC Groups for Access Control

**Use Case**: Grant access to features based on OIDC groups

**Authelia Configuration**:

```yaml
# authelia/configuration.yml
identity_providers:
  oidc:
    clients:
      - id: parchmark-web
        # ... other config ...

        # Include groups in token
        scope_mappings:
          groups:
            - groups  # Include 'groups' claim from LDAP/directory
```

**Implementation**:

```python
# backend/app/auth/authorization.py

class AuthorizationService:
    @staticmethod
    def check_group_permission(
        user: User,
        required_group: str
    ) -> bool:
        """Check if user is in required group."""
        user_groups = user.custom_attributes.get('groups', [])
        return required_group in user_groups

    @staticmethod
    def check_any_group(
        user: User,
        allowed_groups: List[str]
    ) -> bool:
        """Check if user is in any of the allowed groups."""
        user_groups = user.custom_attributes.get('groups', [])
        return any(g in user_groups for g in allowed_groups)

    @staticmethod
    def check_all_groups(
        user: User,
        required_groups: List[str]
    ) -> bool:
        """Check if user is in all required groups."""
        user_groups = user.custom_attributes.get('groups', [])
        return all(g in user_groups for g in required_groups)
```

### Using Groups in Endpoints

```python
# backend/app/routers/admin.py

from app.auth.authorization import AuthorizationService

@app.get("/api/admin/users")
async def list_users(current_user: User = Depends(get_current_user)):
    """Admin endpoint - requires admin group."""

    if not AuthorizationService.check_group_permission(
        current_user,
        "admin"
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    # ... return user list ...

@app.get("/api/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    """Analytics endpoint - requires analytics or admin group."""

    if not AuthorizationService.check_any_group(
        current_user,
        ["analytics", "admin"]
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    # ... return analytics ...
```

### Frontend Authorization

```typescript
// ui/src/features/auth/hooks/useAuthorization.ts

export function useAuthorization() {
  const { user } = useAuthStore();

  const hasGroup = (group: string): boolean => {
    return user?.custom_attributes?.groups?.includes(group) ?? false;
  };

  const hasAnyGroup = (groups: string[]): boolean => {
    return groups.some(g => user?.custom_attributes?.groups?.includes(g));
  };

  return { hasGroup, hasAnyGroup };
}

// Usage in components
export function AdminPanel() {
  const { hasGroup } = useAuthorization();

  if (!hasGroup('admin')) {
    return <div>Access denied</div>;
  }

  return <AdminDashboard />;
}
```

---

## Advanced Scenario 3: Custom Username Generation

### Dynamic Username from Claims

**Use Case**: Generate usernames from various OIDC claims

**Implementation**:

```python
class UsernameGenerator:
    """Generate usernames from various claim combinations."""

    @staticmethod
    def from_email(email: str) -> str:
        """Extract username from email."""
        return email.split('@')[0]

    @staticmethod
    def from_given_family_name(given: str, family: str) -> str:
        """Generate from given and family name."""
        return f"{given.lower()}.{family.lower()}"

    @staticmethod
    def from_employee_id(emp_id: str) -> str:
        """Use employee ID as username."""
        return f"emp_{emp_id}"

    @staticmethod
    def from_preferred_username(preferred: str) -> str:
        """Use preferred_username claim."""
        return preferred.lower()

    @staticmethod
    def generate(
        claims: Dict[str, Any],
        strategy: str = "preferred_username"
    ) -> str:
        """Generate username based on strategy."""

        strategies = {
            "preferred_username": lambda: claims.get(
                'preferred_username', 'unknown'
            ).lower(),
            "email": lambda: UsernameGenerator.from_email(
                claims.get('email', 'unknown')
            ),
            "given_family": lambda: UsernameGenerator.from_given_family_name(
                claims.get('given_name', 'user'),
                claims.get('family_name', 'unknown')
            ),
            "employee_id": lambda: UsernameGenerator.from_employee_id(
                claims.get('employee_id', 'unknown')
            ),
        }

        generator = strategies.get(strategy, strategies["preferred_username"])
        return generator()

    @staticmethod
    def make_unique(base_username: str, db: Session) -> str:
        """Ensure username is unique by appending number if needed."""
        username = base_username
        counter = 1

        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1

        return username
```

### Integration

```python
async def get_or_create_oidc_user(
    db: Session,
    user_info: Dict[str, Any],
    username_strategy: str = "preferred_username"
) -> User:
    """Create user with strategy-based username."""

    # Generate username using strategy
    base_username = UsernameGenerator.generate(
        user_info,
        strategy=username_strategy
    )

    # Make unique if needed
    username = UsernameGenerator.make_unique(base_username, db)

    # Create user
    user = User(
        username=username,
        email=user_info.get('email'),
        oidc_sub=user_info['oidc_sub'],
        auth_provider='oidc',
        password_hash=None,
    )
    db.add(user)
    db.commit()

    return user
```

---

## Advanced Scenario 4: Token Revocation with Redis

### Implementing Token Blacklist

**Use Case**: Revoke tokens before expiration

**Implementation**:

```python
# backend/app/auth/token_revocation.py

import redis
from datetime import datetime

class TokenRevocationService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def revoke_token(self, token: str, expiry_seconds: int) -> bool:
        """Add token to revocation blacklist."""
        key = f"revoked_token:{token[:50]}"  # Use token prefix to limit key size
        try:
            await self.redis.setex(key, expiry_seconds, "revoked")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def is_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        key = f"revoked_token:{token[:50]}"
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check token revocation: {e}")
            return False

    async def revoke_user_tokens(self, user_id: int) -> int:
        """Revoke all tokens for a user."""
        pattern = f"revoked_token:user_{user_id}:*"
        cursor = 0
        revoked_count = 0

        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern)
            for key in keys:
                await self.redis.delete(key)
                revoked_count += 1

            if cursor == 0:
                break

        return revoked_count
```

### Integration in Validation

```python
# In OIDCValidator
async def validate_oidc_token(self, token: str) -> Dict[str, Any]:
    """Validate OIDC token including revocation check."""

    # Check if revoked
    if await token_revocation_service.is_revoked(token):
        raise OIDCValidationError("Token has been revoked")

    # ... proceed with normal validation ...
    claims = jwt.decode(token, ...)

    return claims
```

### Logout Endpoint Enhancement

```python
@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout - revoke token immediately."""

    token = get_token_from_request()
    expiry = get_token_expiry(token)

    # Revoke token
    await token_revocation_service.revoke_token(token, expiry)

    return {"message": "Logged out successfully"}

    # Optional: Revoke all user tokens
    # await token_revocation_service.revoke_user_tokens(current_user.id)
```

---

## Advanced Scenario 5: Session Management with Redis

### Tracking Active Sessions

**Use Case**: Know which devices/sessions a user has active

**Implementation**:

```python
# backend/app/auth/session_manager.py

class SessionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def create_session(
        self,
        user_id: int,
        token: str,
        device_info: str,
        ip_address: str
    ) -> str:
        """Create new session for user."""

        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user_id,
            'token': token,
            'device': device_info,
            'ip': ip_address,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
        }

        key = f"session:{session_id}"
        await self.redis.setex(
            key,
            7 * 24 * 3600,  # 7 days
            json.dumps(session_data)
        )

        # Add to user's session list
        await self.redis.sadd(f"user_sessions:{user_id}", session_id)

        return session_id

    async def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for user."""

        session_ids = await self.redis.smembers(f"user_sessions:{user_id}")
        sessions = []

        for session_id in session_ids:
            key = f"session:{session_id.decode()}"
            session_data = await self.redis.get(key)
            if session_data:
                sessions.append(json.loads(session_data))

        return sessions

    async def revoke_session(self, user_id: int, session_id: str) -> bool:
        """Revoke specific session."""

        await self.redis.delete(f"session:{session_id}")
        await self.redis.srem(f"user_sessions:{user_id}", session_id)
        return True

    async def revoke_all_sessions(self, user_id: int) -> int:
        """Revoke all sessions for user."""

        session_ids = await self.redis.smembers(f"user_sessions:{user_id}")
        for session_id in session_ids:
            await self.redis.delete(f"session:{session_id.decode()}")

        await self.redis.delete(f"user_sessions:{user_id}")
        return len(session_ids)
```

### Frontend Session List

```typescript
// UI to show and manage sessions
export function SessionManager() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    const response = await fetch('/api/auth/sessions');
    setSessions(await response.json());
  };

  const revokeSession = async (sessionId: string) => {
    await fetch(`/api/auth/sessions/${sessionId}`, { method: 'DELETE' });
    fetchSessions();
  };

  return (
    <div>
      <h2>Active Sessions</h2>
      {sessions.map(session => (
        <SessionRow
          key={session.id}
          session={session}
          onRevoke={revokeSession}
        />
      ))}
    </div>
  );
}
```

---

## Advanced Scenario 6: Multi-Provider Support (Future)

### Supporting Multiple OIDC Providers

**Architecture**:

```python
# Multiple providers configuration
OIDC_PROVIDERS = {
    'authelia': {
        'issuer': 'https://auth.engen.tech',
        'client_id': 'parchmark-web',
        'name': 'Company SSO',
    },
    'okta': {
        'issuer': 'https://company.okta.com',
        'client_id': 'parchmark-okta',
        'name': 'Okta',
    },
    'google': {
        'issuer': 'https://accounts.google.com',
        'client_id': 'parchmark-google',
        'name': 'Google',
    },
}

class MultiProviderOIDCValidator:
    def __init__(self):
        self.validators = {
            provider: OIDCValidator(config)
            for provider, config in OIDC_PROVIDERS.items()
        }

    async def validate_from_any_provider(
        self, token: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Validate token from any provider."""

        for provider, validator in self.validators.items():
            try:
                claims = await validator.validate_oidc_token(token)
                return provider, claims
            except OIDCValidationError:
                continue

        raise OIDCValidationError("Token not valid from any provider")
```

---

## Advanced Scenario 7: Adaptive Authentication

### Risk-Based Authentication

**Use Case**: Require additional verification for suspicious logins

**Implementation**:

```python
class RiskAssessment:
    @staticmethod
    def assess_login_risk(
        user: User,
        ip_address: str,
        device_fingerprint: str,
        location: Optional[str] = None
    ) -> Tuple[int, List[str]]:
        """Assess risk of login (0-100 score)."""

        risk_score = 0
        risk_factors = []

        # Check IP reputation
        if ip_address not in user.trusted_ips:
            risk_score += 10
            risk_factors.append("New IP address")

        # Check device
        if device_fingerprint not in user.trusted_devices:
            risk_score += 15
            risk_factors.append("New device")

        # Check location (if available)
        if location and location != user.last_known_location:
            risk_score += 20
            risk_factors.append("New location")

        # Check time of day
        if not RiskAssessment.is_usual_login_time(user):
            risk_score += 5
            risk_factors.append("Unusual login time")

        # Check failed attempts
        recent_failures = get_recent_failed_logins(user.id, hours=1)
        if recent_failures > 3:
            risk_score += 25
            risk_factors.append("Multiple failed attempts")

        return risk_score, risk_factors

    @staticmethod
    def requires_mfa(risk_score: int) -> bool:
        """Determine if MFA is required."""
        return risk_score > 50
```

---

## See Also

- **AUTHELIA_OIDC_IMPLEMENTATION.md** - Core implementation
- **AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md** - Backend architecture
- **AUTHELIA_OIDC_SECURITY_HARDENING.md** - Security considerations
