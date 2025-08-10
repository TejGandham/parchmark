
## Core JWT Authentication Implementation

  

### Guardian Configuration

  

```elixir

# Dependencies in mix.exs

{:guardian, "~> 2.3"},

{:bcrypt_elixir, "~> 3.0"}

```

  

**Guardian Module Structure:**

- Create `Api.Auth.Guardian` module

- Implement required callback functions

- Configure JWT signing algorithm (RS256 recommended)

- Store keys securely in environment variables

- Define token types (access, refresh) with different TTLs

  

**JWT Claims Configuration:**

- Standard claims: `sub`, `iat`, `exp`, `iss`

- Custom claims: `type` (access/refresh), `permissions`

- Ensure proper audience and issuer validation

  

### Database Schema Enhancements

  

**User Schema Additions:**

- `password_hash`: Securely stored using Bcrypt

- `last_login`: Timestamp tracking for security auditing

- `login_count`: Counter for security monitoring

- `active`: Boolean flag for account status control

  

**Refresh Token Storage:**

- Create dedicated `tokens` table

- Fields:

- `jti`: Token identifier

- `user_id`: Associated user

- `token_hash`: Hashed token value

- `context`: Purpose of token (refresh/reset)

- `inserted_at`, `expires_at`: Timestamp tracking

- Add composite index on `user_id` and `context`

- Implement automatic token pruning

  

### Authentication Pipeline Implementation

  

**Pipeline Components:**

- Pipeline module with plugs sequence

- Token extraction from multiple sources (header, cookies, params)

- Access control based on token verification

- Error handling with proper status codes

- Rate limiting implementation with sliding window

  

**Request Processing Flow:**

1. Extract token from request

2. Verify token signature and claims

3. Load user resource from token subject

4. Attach user to connection assigns

5. Check permissions and continue or halt

  

### Token Management Implementation

  

**Token Generation:**

- Create access token with short TTL (15 min)

- Create refresh token with longer TTL (14 days)

- Sign tokens with proper key (RSA private key)

- Include essential claims for security

  

**Token Delivery:**

- Store access token in HttpOnly, Secure cookie

- Set appropriate cookie options (SameSite=Lax)

- Consider double-submit pattern for CSRF protection

- Implement cookie rotation on authentication state change

  

**Token Refresh Implementation:**

- Verify refresh token authenticity

- Check token against stored hash

- Implement single-use refresh tokens

- Create new token pair on successful refresh

- Update stored token hash for rotation

  

### Security Implementation Details

  

**Password Handling:**

- Implement Bcrypt with proper cost factor

- Create password validation rules

- Store only password hash, never plaintext

- Implement secure password reset flow

  

**CSRF Protection:**

- Generate CSRF token on session creation

- Require token for state-changing operations

- Validate token on all authenticated requests

- Rotate CSRF token on authentication state change

  

**API Security Headers:**

- Implement Content-Security-Policy

- Add X-Content-Type-Options: nosniff

- Configure Strict-Transport-Security

- Add X-XSS-Protection header

- Implement proper CORS configuration

  

## Federated Authentication Implementation

  

### OAuth/OIDC Implementation

  

**Provider Integration:**

```elixir

# Dependencies

{:ueberauth, "~> 0.10"},

{:ueberauth_google, "~> 0.10"},

{:ueberauth_microsoft, "~> 0.10"}

```

  

**Provider Configuration:**

- Configure client IDs and secrets in environment

- Define callback URLs with CSRF protection

- Specify required scopes (email, profile)

- Implement proper state parameter handling

  

**Identity Storage Schema:**

- Create `user_identities` table with:

- `provider`: Identity provider name

- `provider_user_id`: External user identifier

- `user_id`: Reference to internal user

- `token_data`: Encrypted provider tokens

- `profile_data`: JSON profile information

- `created_at`, `updated_at`: Timestamps

  

### OAuth Flow Implementation

  

**Authentication Request Flow:**

1. Generate secure state parameter

2. Store state in session or server-side

3. Redirect to provider's authorization endpoint

4. Include proper scopes and response_type

5. Add PKCE for additional security

  

**Callback Processing:**

1. Validate state parameter

2. Exchange authorization code for tokens

3. Fetch user profile information

4. Create or retrieve local user account

5. Associate external identity with user

6. Issue Guardian tokens for API access

  

**Account Linking Implementation:**

- Detect existing accounts with same email

- Implement secure linking confirmation

- Allow unlinking with account continuity

- Handle conflict resolution for duplicate accounts

- Store multiple identities per user

  

### Session Management with Federation

  

**Cross-Provider Session Handling:**

- Create unified session representation

- Store authentication source in tokens

- Implement provider-specific token refresh

- Create consistent logout across providers

- Handle provider-initiated logout (back-channel)

  

**Token Claims Extension:**

- Add `provider` claim for authentication source

- Include `identity_id` for provider tracking

- Add provider-specific permissions mapping

- Create adaptive token TTL based on provider policies

  

## WebAuthn/Passkey Implementation

  

### WebAuthn Foundation

  

```elixir

# Dependencies

{:wax, "~> 0.5"}, # Elixir WebAuthn library

```

  

**Credential Storage Schema:**

- Create `credentials` table with:

- `id`: Primary key

- `user_id`: Associated user

- `credential_id`: Base64URL encoded ID

- `public_key`: Encoded credential public key

- `sign_count`: Counter for replay protection

- `attestation_type`: Type of attestation used

- `created_at`, `last_used_at`: Timestamps

- `friendly_name`: User-assigned device name

  

### Registration Implementation

  

**Challenge Generation:**

- Create cryptographically random challenge

- Store challenge with session or server-side

- Define acceptable authenticator criteria

- Specify resident key preference

- Set user verification requirement

  

**Attestation Verification:**

- Verify client data hash matches challenge

- Validate attestation statement format

- Extract and store credential public key

- Verify attestation certificate chain

- Record initial signature counter

  

### Authentication Implementation

  

**Assertion Challenge:**

- Generate random challenge for authentication

- Specify allowed credential IDs

- Set user verification requirement

- Store challenge server-side with timeout

  

**Assertion Verification:**

- Validate client data against challenge

- Verify signature using stored public key

- Check and update signature counter

- Detect and prevent replay attacks

- Issue Guardian tokens on successful verification

  

### Multi-Factor Authentication

  

**MFA Policy Implementation:**

- Define rules for when MFA is required

- Create step-up authentication flow

- Implement risk-based authentication triggers

- Allow user preference for MFA enforcement

- Create recovery options (backup codes)

  

**Cross-Method Authentication:**

- Support fallback between authentication methods

- Create unified authentication flow UI

- Implement credential suggestion based on device

- Allow user to select authentication method

- Handle method-specific error states

  

## Integration with Frontend

  

### Authentication State Management

  

**Zustand Auth Store Extension:**

```typescript

// Extended Auth store interface

interface AuthState {

isAuthenticated: boolean;

user: User | null;

authMethod: 'password' | 'google' | 'microsoft' | 'passkey';

tokens: {

accessToken: string | null;

accessExpiry: number | null;

refreshToken: string | null;

};

actions: {

login: (username: string, password: string) => Promise<boolean>;

loginWithProvider: (provider: string) => Promise<boolean>;

loginWithPasskey: () => Promise<boolean>;

refreshTokens: () => Promise<boolean>;

logout: () => Promise<void>;

};

}

```

  

**Token Management:**

- Store tokens in HttpOnly cookies

- Implement automatic token refresh

- Handle token expiration gracefully

- Provide login status reactivity

  

### API Integration

  

**Axios Interceptor Implementation:**

```typescript

// Request interceptor for authentication

api.interceptors.request.use(config => {

// Token is in cookie, so no need to attach manually

return config;

});

  

// Response interceptor for token refresh

api.interceptors.response.use(

response => response,

async error => {

if (error.response?.status === 401) {

try {

// Try to refresh the token

const refreshed = await authStore.actions.refreshTokens();

if (refreshed) {

// Retry the original request

return api(error.config);

}

} catch (refreshError) {

// Handle refresh failure

}

// Force logout on authentication failure

await authStore.actions.logout();

window.location.href = '/login';

}

return Promise.reject(error);

}

);

```

  

**Authentication Components:**

- Create unified login interface

- Implement provider selection buttons

- Add passkey authentication button

- Create registration form with validation

- Implement proper error handling

- Show appropriate authentication methods based on device capabilities

  

## Security Hardening

  

### Token Security

  

**Token Storage Recommendations:**

- Use HttpOnly cookies for tokens

- Implement proper cookie security flags

- Consider token binding for additional security

- Implement proper CORS to prevent token theft

- Use short-lived access tokens (15 minutes max)

  

**Revocation Strategy:**

- Implement token blacklisting for critical scenarios

- Create user session management interface

- Allow users to terminate sessions remotely

- Implement forced logout for security issues

- Add audit logging for authentication events

  

### Input Validation

  

**Authentication Request Validation:**

- Validate all inputs with proper schemas

- Implement rate limiting with increasing backoff

- Create IP-based request throttling

- Add anomaly detection for authentication attempts

- Implement proper error messages (informative but not revealing)

  

### Monitoring and Alerting

  

**Security Monitoring Implementation:**

- Log all authentication events

- Track failed login attempts

- Monitor geographic access patterns

- Create alerts for suspicious activity

- Implement regular security audit processes

  

## Deployment Considerations

  

**Environment Configuration:**

- Store all secrets in environment variables

- Use proper key rotation procedures

- Configure different settings per environment

- Implement proper SSL/TLS configuration

- Create backup and recovery procedures

  

**Scaling Considerations:**

- Design token validation for horizontal scaling

- Consider database sharding for large user bases

- Implement proper caching strategies

- Plan for high availability of authentication services

- Ensure proper database indexing for auth queries