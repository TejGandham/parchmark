# OIDC Frontend Developer Guide

Deep dive into the ParchMark frontend OIDC implementation for developers maintaining and extending the authentication system.

---

## Overview

This guide explains:
- How the OIDC flow works in the frontend
- Architecture of the auth store and components
- How to extend or modify OIDC functionality
- Key design decisions and trade-offs
- Performance considerations
- Security implications

---

## Architecture

### Authentication Flow

```
User clicks "Sign In with SSO"
    ↓
OIDCCallback redirects to Authelia authorization endpoint
    ↓
User authenticates at Authelia
    ↓
Authelia redirects back with authorization code
    ↓
OIDCCallback component exchanges code for tokens
    ↓
Frontend stores tokens in localStorage
    ↓
Auth store updated with token source and tokens
    ↓
Navigate to /notes (or saved route)
    ↓
API requests include token in Authorization header
    ↓
Backend validates token (local or OIDC)
    ↓
Response returned
```

### Code Structure

```
ui/src/
├── config/
│   └── oidc.ts                          # OIDC configuration

├── features/auth/
│   ├── components/
│   │   ├── LoginForm.tsx               # Local login + SSO button
│   │   ├── OIDCCallback.tsx            # Callback handler
│   │   └── ProtectedRoute.tsx          # Route protection
│   │
│   ├── store/
│   │   └── auth.ts                     # Auth state management
│   │
│   ├── utils/
│   │   ├── oidcUtils.ts                # OIDC client utilities
│   │   └── tokenUtils.ts               # Token management
│   │
│   ├── hooks/
│   │   ├── useStoreRouterSync.ts       # URL/state sync
│   │   └── useTokenExpirationMonitor.ts # Token expiration tracking
│   │
│   └── __tests__/
│       ├── OIDCCallback.test.tsx
│       ├── oidcUtils.test.ts
│       └── auth.oidc.test.ts

└── App.tsx                              # Routes including /oidc/callback
```

---

## Core Components

### 1. OIDC Configuration

**Location**: `ui/src/config/oidc.ts`

**Purpose**: Centralized OIDC configuration

```typescript
// Environment variables
const OIDC_CONFIG = {
  authority: process.env.VITE_OIDC_ISSUER_URL,
  client_id: process.env.VITE_OIDC_CLIENT_ID,
  redirect_uri: process.env.VITE_OIDC_REDIRECT_URI,
  post_logout_redirect_uri: process.env.VITE_OIDC_LOGOUT_REDIRECT_URI,
  response_type: 'code',
  scope: 'openid profile email',
  code_challenge_method: 'S256',  // PKCE
  // ... other settings
};
```

**Key Settings**:

| Setting | Example | Purpose |
|---------|---------|---------|
| `authority` | http://localhost:9091 | OIDC provider URL |
| `client_id` | parchmark-web | Client registered in Authelia |
| `redirect_uri` | http://localhost:5173/oidc/callback | Where to redirect after login |
| `response_type` | code | OAuth2 authorization code flow |
| `scope` | openid profile email | What user data to request |
| `code_challenge_method` | S256 | PKCE SHA256 |

**Design Decisions**:

1. **Configuration via Environment Variables**
   - Allows different configs per environment
   - Development, staging, production configs
   - No hardcoding

2. **PKCE S256 Enabled**
   - Protection against authorization code interception
   - Required for public clients (SPAs)
   - Security best practice

3. **Standard OIDC Scopes**
   - `openid`: Core OpenID Connect
   - `profile`: Username and name
   - `email`: Email address

### 2. OIDC User Manager

**Location**: `ui/src/features/auth/utils/oidcUtils.ts`

**Purpose**: Manage OIDC flow using oidc-client-ts library

**Key Functions**:

#### `initOIDCManager()` - Initialize UserManager

```typescript
export async function initOIDCManager() {
  const manager = new UserManager(OIDC_CONFIG);

  // Handle redirect after login
  manager.events.addUserLoaded((user) => {
    console.log('User loaded from OIDC');
  });

  // Handle logout
  manager.events.addUserSignedOut(() => {
    console.log('User signed out from OIDC');
  });

  return manager;
}
```

**Purpose**: Set up the OIDC client with configuration

**Storage**: Uses browser's session storage by default

#### `startOIDCLogin()` - Initiate Login

```typescript
export async function startOIDCLogin() {
  const manager = await initOIDCManager();
  await manager.signinRedirect();
}
```

**Flow**:
1. Generate PKCE code challenge
2. Generate random state parameter
3. Redirect to Authelia authorization endpoint
4. URL: `https://auth.engen.tech/authorization?client_id=parchmark-web&...`

#### `handleOIDCCallback()` - Handle Callback

```typescript
export async function handleOIDCCallback() {
  const manager = await initOIDCManager();
  const user = await manager.signinCallback();
  return user;
}
```

**Steps**:
1. Extract authorization code from URL
2. Verify state parameter matches
3. Exchange code for tokens (backend communication)
4. Store tokens in session storage
5. Return user object

**Token Exchange**:
```
Frontend → Authelia: code + state + verifier
           ↓
Authelia verifies code (not expired, matches client)
         verifies PKCE verifier
         ↓
Authelia → Frontend: access_token + refresh_token + id_token
```

#### `renewOIDCToken()` - Silent Token Renewal

```typescript
export async function renewOIDCToken() {
  const manager = await initOIDCManager();
  const user = await manager.signinSilent();
  return user;
}
```

**Purpose**: Refresh tokens without user interaction

**When Used**:
- Token expiration detected
- Proactive renewal (60 seconds before expiry)
- User activity detected

**Backend Request**:
```
GET /authorization/refresh?refresh_token=TOKEN
```

#### `logoutOIDC()` - OIDC Logout

```typescript
export async function logoutOIDC() {
  const manager = await initOIDCManager();
  await manager.signoutRedirect();
}
```

**Flow**:
1. Redirect to `end_session_endpoint`
2. Authelia clears session
3. Redirect to configured logout URI
4. Frontend clears auth store

### 3. Auth Store (Zustand)

**Location**: `ui/src/features/auth/store/auth.ts`

**Purpose**: Centralized auth state management

**Key State**:

```typescript
interface AuthState {
  // Token management
  token: string | null;           // Access token
  refreshToken: string | null;    // Refresh token
  tokenSource: 'local' | 'oidc';  // Which auth method
  isLoading: boolean;
  error: string | null;

  // User info
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  loginLocal(username: string, password: string): Promise<void>;
  loginWithOIDC(): Promise<void>;
  handleOIDCCallbackFlow(): Promise<void>;
  refreshTokens(): Promise<void>;
  logout(): Promise<void>;
  clearError(): void;
}
```

**Key Differences by Auth Method**:

| Aspect | Local | OIDC |
|--------|-------|------|
| Login endpoint | POST /api/auth/login | Authelia /authorization |
| Token stored in | Auth store + localStorage | Auth store + localStorage |
| Token type | HS256 JWT | RS256 JWT |
| Refresh method | POST /api/auth/refresh | OIDC silent renewal |
| Logout redirect | Just clear store | Authelia end_session |

**Token Refresh Logic**:

```typescript
async refreshTokens() {
  if (this.tokenSource === 'local') {
    // Use backend refresh endpoint
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });
    const data = await response.json();
    set({ token: data.access_token });
  } else if (this.tokenSource === 'oidc') {
    // Use OIDC client renewal
    const user = await renewOIDCToken();
    set({ token: user.access_token });
  }
}
```

**Logout Logic**:

```typescript
async logout() {
  if (this.tokenSource === 'oidc') {
    // Clear OIDC session on Authelia
    await logoutOIDC();  // Redirects to end_session endpoint
  }
  // Clear local auth state
  set({ token: null, user: null, tokenSource: null });
}
```

### 4. OIDCCallback Component

**Location**: `ui/src/features/auth/components/OIDCCallback.tsx`

**Purpose**: Handle Authelia redirect after authentication

```typescript
export function OIDCCallback() {
  const navigate = useNavigate();
  const { handleOIDCCallbackFlow } = useAuthStore();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // 1. Exchange code for tokens
        await handleOIDCCallbackFlow();

        // 2. Redirect to notes or saved location
        const from = sessionStorage.getItem('auth-redirect-from') || '/notes';
        navigate(from);
      } catch (err) {
        setError(`Authentication failed: ${err.message}`);
      } finally {
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [handleOIDCCallbackFlow, navigate]);

  if (isProcessing) {
    return <Spinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return null;
}
```

**Flow**:

```
Component mounts (user redirected from Authelia)
    ↓
handleOIDCCallbackFlow():
  1. Extract authorization code from URL
  2. Exchange code for tokens with Authelia
  3. Parse tokens (no server-side validation needed)
  4. Store tokens in localStorage
  5. Update auth store
    ↓
Navigate to saved route or /notes
    ↓
Component unmounts
```

**Handling**:
1. **Loading State**: Shows spinner during token exchange
2. **Error Handling**: Shows error message if auth fails
3. **Redirect**: Navigates to protected route or /notes

### 5. LoginForm Component

**Location**: `ui/src/features/auth/components/LoginForm.tsx`

**Updates**:

```typescript
export function LoginForm() {
  const { loginLocal, loginWithOIDC, isLoading, error } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isOIDCLoading, setIsOIDCLoading] = useState(false);

  const handleLocalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await loginLocal(username, password);
  };

  const handleOIDCLogin = async () => {
    setIsOIDCLoading(true);
    try {
      // Save current location for redirect after auth
      sessionStorage.setItem('auth-redirect-from', window.location.pathname);
      await loginWithOIDC();
      // Will redirect to Authelia
    } finally {
      setIsOIDCLoading(false);
    }
  };

  return (
    <Box>
      {/* Local login form */}
      <form onSubmit={handleLocalLogin}>
        <Input
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Username"
        />
        <Input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Password"
        />
        <Button type="submit" isLoading={isLoading}>
          Sign In
        </Button>
      </form>

      {/* Divider */}
      <HStack>
        <Divider />
        <Text>OR</Text>
        <Divider />
      </HStack>

      {/* OIDC button */}
      <Button
        onClick={handleOIDCLogin}
        isLoading={isOIDCLoading}
        colorScheme="blue"
        width="100%"
      >
        Sign In with SSO
      </Button>

      {error && <Alert status="error">{error}</Alert>}
    </Box>
  );
}
```

**Features**:
- Local login form
- "OR" divider
- SSO button below
- Loading states for both methods
- Error display

---

## Key Design Decisions

### 1. Token Storage in localStorage

**Decision**: Store tokens in localStorage

**Alternative Considered**: Secure HttpOnly cookies

**Why localStorage**:
- SPA must access tokens for Authorization header
- HttpOnly cookies can't be read by JavaScript
- Would require server-side proxy for API requests
- Simpler implementation

**Security Notes**:
- XSS vulnerability could steal tokens
- Mitigated by sanitizing user input
- React auto-escapes by default
- Consider moving to secure cookies in future

### 2. Token Source Tracking

**Decision**: Track whether token is "local" or "oidc"

**Benefits**:
- Different refresh logic per method
- Proper logout behavior
- User type detection
- Debugging aid

**Implementation**:
```typescript
set({ tokenSource: 'oidc' });  // Set during OIDC auth
set({ tokenSource: 'local' });  // Set during local auth
```

### 3. PKCE for Public Client

**Decision**: Use PKCE S256

**Why**:
- Protection against authorization code interception
- Recommended for SPAs and native apps
- Industry standard
- No additional complexity

**Flow**:
```
1. Generate code_verifier (random string)
2. Create code_challenge = SHA256(code_verifier)
3. Send code_challenge in authorization request
4. Authelia includes code_challenge in returned code
5. Exchange code with code_verifier
6. Authelia verifies SHA256(verifier) == challenge
```

### 4. Session Storage for Temp Data

**Decision**: Use sessionStorage for redirect URLs

**Rationale**:
- Survives page navigation
- Cleared when tab closes
- Isolated per tab
- Don't need persistent storage

**Usage**:
```typescript
sessionStorage.setItem('auth-redirect-from', '/notes/123');
const from = sessionStorage.getItem('auth-redirect-from');
sessionStorage.removeItem('auth-redirect-from');
```

---

## Implementation Patterns

### Pattern 1: Protecting Routes

```typescript
// ✓ CORRECT - Check auth before rendering
<ProtectedRoute>
  <NotesPage />
</ProtectedRoute>

// In ProtectedRoute:
if (!isAuthenticated) {
  return <Navigate to="/login" />;
}
return children;
```

### Pattern 2: Token Expiration Handling

```typescript
// ✓ CORRECT - Proactive refresh before expiration
const tokenExpiry = decodeToken(token).exp * 1000;  // Convert to ms
const now = Date.now();
const timeUntilExpiry = tokenExpiry - now;

if (timeUntilExpiry < 60000) {  // 60 seconds
  await refreshTokens();
}

// ✗ WRONG - Wait until 401 error
// Results in failed requests before refresh
```

### Pattern 3: Error Handling

```typescript
// ✓ CORRECT - Distinguish between auth and other errors
try {
  const response = await fetch('/api/notes', {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (response.status === 401) {
    // Unauthorized - token invalid or expired
    await logout();
    navigate('/login');
  } else if (!response.ok) {
    // Other error (500, 404, etc.)
    throw new Error(`API error: ${response.status}`);
  }
} catch (error) {
  // Network or other error
  setError(error.message);
}
```

---

## Performance Optimization

### 1. Token Caching

**Current**: Tokens cached in store and localStorage

**Benefits**:
- No network call on page load
- Instant app startup
- Offline capability (tokens still valid)

**Timing**:
- Store read: <1ms
- localStorage read: ~5ms
- Total startup: <10ms

### 2. OIDC Manager Reuse

**Current**: Create UserManager once, reuse instance

**Alternative**: Create new instance per call (slower)

```typescript
// ✓ CORRECT - Singleton instance
let manager: UserManager | null = null;

async function getOIDCManager() {
  if (!manager) {
    manager = new UserManager(OIDC_CONFIG);
  }
  return manager;
}

// ✗ WRONG - New instance every time
async function getOIDCManager() {
  return new UserManager(OIDC_CONFIG);  // Slow
}
```

### 3. Lazy Token Validation

**Current**: Validate token on route change

**Alternative**: Validate every request (more network calls)

```typescript
// In useTokenExpirationMonitor hook
setInterval(() => {
  const token = useAuthStore.getState().token;
  if (isTokenExpiringSoon(token, 60)) {
    useAuthStore.getState().refreshTokens();
  }
}, 3 * 60 * 1000);  // Check every 3 minutes
```

---

## Security Considerations

### 1. PKCE Implementation

**What it does**:
- Prevents authorization code interception
- Even if code is stolen, can't exchange without verifier

**How it works**:
```
1. code_verifier = random_string()
2. code_challenge = base64url(sha256(code_verifier))
3. Include code_challenge in authorization request
4. Include code_verifier in token request
5. Server validates: sha256(verifier) == challenge
```

### 2. Token Expiration

**Access Token**:
- Expires after 30 minutes
- Used for API requests
- Short TTL limits exposure if stolen

**Refresh Token**:
- Expires after 7 days
- Used to get new access token
- Longer TTL for convenience

**Proactive Logout**:
- Logout 60 seconds before expiration
- Prevents "session expired" mid-action
- User re-authenticates on next login

### 3. State Parameter

**What it does**:
- Prevents Cross-Site Request Forgery (CSRF)
- oidc-client-ts manages automatically

**Flow**:
```
1. Generate random state: state = random_string()
2. Store state in session: sessionStorage.state = state
3. Send state in authorization request
4. Authelia returns same state in callback
5. Verify: sessionStorage.state == returned_state
```

### 4. Same-Origin Policy

**SPA Protection**:
- Can only call APIs on same origin
- localStorage accessible only from same origin
- Cookies sent only to same origin

**Cross-Origin**:
- API on different domain uses CORS
- Authorization header requires CORS header
- Breaks CSRF attacks automatically

---

## Testing Strategy

### Unit Tests

**OIDC Utils Tests** (`oidcUtils.test.ts`):
- Token renewal flow
- Login initiation
- Callback handling
- Mock OIDC client responses

**Example**:
```typescript
it('should handle OIDC callback and store token', async () => {
  const mockUser = {
    access_token: 'token123',
    id_token: 'id123',
    refresh_token: 'refresh123'
  };

  // Mock OIDC manager
  vi.mock('oidc-client-ts', () => ({
    UserManager: vi.fn(() => ({
      signinCallback: vi.fn(() => mockUser)
    }))
  }));

  const result = await handleOIDCCallback();
  expect(result).toEqual(mockUser);
});
```

### Component Tests

**OIDCCallback Tests** (`OIDCCallback.test.tsx`):
- Component renders
- Token exchange happens
- Navigation occurs
- Error handling

**Example**:
```typescript
it('should show spinner while processing', () => {
  const { getByTestId } = render(<OIDCCallback />);
  expect(getByTestId('spinner')).toBeInTheDocument();
});

it('should navigate to /notes on success', async () => {
  const navigate = vi.fn();
  vi.mock('react-router', () => ({ useNavigate: () => navigate }));

  render(<OIDCCallback />);
  await waitFor(() => {
    expect(navigate).toHaveBeenCalledWith('/notes');
  });
});
```

### Integration Tests

**Auth Store Tests** (`auth.oidc.test.ts`):
- Login flow
- Token refresh
- Logout flow
- State consistency

---

## Debugging

### Enable Debug Logging

```typescript
// In App.tsx
if (process.env.NODE_ENV === 'development') {
  localStorage.debug = 'app:*,oidc:*';
}
```

### Check Token

```javascript
// In browser console
const auth = JSON.parse(localStorage.getItem('auth-store'));
console.log('Token:', auth.state.token);
console.log('Token source:', auth.state.tokenSource);

// Decode token
function decodeToken(token) {
  const parts = token.split('.');
  return JSON.parse(atob(parts[1]));
}
console.log('Claims:', decodeToken(auth.state.token));
```

### Monitor OIDC Flow

```javascript
// In browser console
// Enable detailed logging
const manager = new UserManager(OIDC_CONFIG);
manager.events.addUserLoaded(user => console.log('User loaded:', user));
manager.events.addUserUnloaded(() => console.log('User unloaded'));
manager.events.addAccessTokenExpiring(() => console.log('Token expiring'));
manager.events.addAccessTokenExpired(() => console.log('Token expired'));
manager.events.addUserSignedOut(() => console.log('User signed out'));
```

### Common Issues

**Issue**: "Authorization code is invalid"
```
Solution: Check if callback URL matches registered redirect_uri
         Check state parameter (should be automatic)
         Check PKCE verifier (should be automatic)
```

**Issue**: "Token not storing in localStorage"
```
Solution: Check browser allows localStorage
         Check privacy/incognito mode isn't enabled
         Check localStorage quota not exceeded
         Verify auth store is persisting correctly
```

**Issue**: "Silent renewal not working"
```
Solution: Check refresh_token is present
         Check OIDC provider supports refresh token grant
         Check token not expired
         Check iframe for silent renewal is working
```

---

## Best Practices

1. **Always use tokenSource to differentiate auth methods**
   - Different refresh/logout logic
   - Clear understanding of user type
   - Debugging aid

2. **Validate tokens before using**
   - Check expiration before API call
   - Proactive refresh before expiration
   - Handle 401 responses gracefully

3. **Store sensitive data securely**
   - Don't store in window or global variables
   - Use Zustand store with persist
   - Clear on logout

4. **Handle OIDC provider errors gracefully**
   - Network timeout: Show retry option
   - Invalid state: Restart login
   - Server error: Show error message

5. **Test both auth methods**
   - Local login tests
   - OIDC login tests
   - Mixed user scenarios
   - Token expiration scenarios

---

## See Also

- **AUTHELIA_OIDC_IMPLEMENTATION.md** - Overall architecture
- **AUTHELIA_OIDC_API_REFERENCE.md** - API endpoints
- **AUTHELIA_OIDC_LOCAL_TESTING.md** - Local testing guide
- Frontend code: `ui/src/features/auth/`
