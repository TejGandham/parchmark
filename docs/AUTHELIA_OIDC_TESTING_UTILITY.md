# OIDC Integration Testing Utility

Comprehensive testing utility for validating Authelia OIDC integration with ParchMark.

---

## Overview

The `test_oidc_integration.py` script provides automated testing of all OIDC components:

- ✅ OIDC discovery endpoint
- ✅ JWKS endpoint and caching
- ✅ Token validation
- ✅ Backend API health
- ✅ Hybrid authentication configuration
- ✅ Performance metrics (JWKS caching latency)

---

## Quick Start

### Run All Tests

```bash
# Using Makefile (recommended)
make test-oidc-integration

# Or directly
cd backend && uv run python scripts/test_oidc_integration.py --test-all
```

### Run Specific Tests

```bash
# Test OIDC discovery endpoint
make test-oidc-discovery

# Test JWKS endpoint
make test-oidc-jwks

# Test token validation
make test-oidc-tokens

# Test backend health
make test-oidc-health

# Test hybrid auth configuration
make test-oidc-hybrid

# Test OIDC performance
make test-oidc-perf
```

---

## Available Commands

### Makefile Targets

```bash
# Complete OIDC integration testing
make test-oidc-integration      # Run all tests

# Individual component tests
make test-oidc-discovery        # OIDC discovery endpoint
make test-oidc-jwks             # JWKS endpoint and caching
make test-oidc-tokens           # Token validation
make test-oidc-health           # Backend API health
make test-oidc-hybrid           # Hybrid auth configuration
make test-oidc-perf             # Performance (JWKS caching)
```

### Direct Script Usage

```bash
# Run all tests
cd backend
uv run python scripts/test_oidc_integration.py --test-all

# Run specific tests
uv run python scripts/test_oidc_integration.py --test-discovery
uv run python scripts/test_oidc_integration.py --test-jwks
uv run python scripts/test_oidc_integration.py --test-validation
uv run python scripts/test_oidc_integration.py --test-health
uv run python scripts/test_oidc_integration.py --test-hybrid
uv run python scripts/test_oidc_integration.py --test-performance

# Custom configuration
uv run python scripts/test_oidc_integration.py \
  --issuer http://authelia:9091 \
  --client-id parchmark-web \
  --api http://backend:8000 \
  --test-all
```

---

## Test Scenarios

### Test 1: OIDC Discovery

**What it tests**: Verifies Authelia OIDC provider is discoverable

**Steps**:
1. Fetches `/.well-known/openid-configuration`
2. Validates required fields present:
   - `issuer`
   - `authorization_endpoint`
   - `token_endpoint`
   - `jwks_uri`
   - `userinfo_endpoint`

**Success criteria**:
- HTTP 200 response
- All required fields present
- URLs are valid

**Example output**:
```
ℹ Testing OIDC discovery at http://localhost:9091
ℹ Fetching discovery document: http://localhost:9091/.well-known/openid-configuration
✓ OIDC discovery document retrieved
ℹ Issuer: http://localhost:9091
ℹ JWKS URI: http://localhost:9091/.well-known/openid-configuration/jwks
ℹ Scopes: ['openid', 'profile', 'email']
```

**Troubleshooting**:
- If fails with "connection refused": Authelia not running
- If fails with "HTTP 404": Authelia not configured for OIDC
- If fails with "timeout": Network connectivity issue

---

### Test 2: JWKS Endpoint

**What it tests**: Verifies JWKS (JSON Web Key Set) is available and valid

**Steps**:
1. Fetches JWKS from discovery endpoint
2. Validates signing keys present
3. Displays key information

**Success criteria**:
- HTTP 200 response
- At least one signing key present
- Keys have proper structure

**Example output**:
```
ℹ Testing JWKS endpoint
ℹ Fetching JWKS: http://localhost:9091/.well-known/openid-configuration/jwks
✓ JWKS retrieved with 1 key(s)
ℹ   Key 1: key-1
```

**Troubleshooting**:
- If no keys found: Authelia key generation failed
- If fails with timeout: OIDC provider overloaded
- If fails with 404: Invalid JWKS URI in discovery

---

### Test 3: Token Validation

**What it tests**: Verifies backend can accept and validate tokens

**Steps**:
1. Creates test token with proper structure
2. Sends token to backend `/api/auth/me` endpoint
3. Validates response

**Success criteria**:
- Backend responds with 200 or 401
- 200 = test token accepted (very unlikely)
- 401 = test token rejected as expected

**Example output**:
```
ℹ Testing token validation
✓ Test token created
ℹ Token (first 50 chars): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ℹ Testing token against backend API
⚠ Token rejected by backend (expected for test token)
```

**Note**: Real OIDC token validation happens with actual Authelia-issued tokens. This test validates the API endpoint structure.

---

### Test 4: API Health

**What it tests**: Verifies backend API is healthy and responsive

**Steps**:
1. Fetches `/api/health` endpoint
2. Validates response structure
3. Displays database status

**Success criteria**:
- HTTP 200 response
- `database: "connected"`
- Service information present

**Example output**:
```
ℹ Testing backend API health
ℹ Fetching health check: http://localhost:8000/api/health
✓ Backend API healthy
ℹ Database: connected
ℹ Service: ParchMark API
ℹ Version: 1.0.0
```

**Troubleshooting**:
- If fails with "connection refused": Backend not running
- If database is "disconnected": Database connection issue
- If fails with timeout: Backend overloaded

---

### Test 5: Hybrid Auth Configuration

**What it tests**: Verifies hybrid authentication (local + OIDC) is enabled

**Steps**:
1. Attempts local login endpoint
2. Validates response (expects 200 or 401)
3. Confirms both auth methods available

**Success criteria**:
- `/api/auth/login` endpoint responds
- Returns 200 (local user exists) or 401 (auth failed)
- Not 404 or 500

**Example output**:
```
ℹ Testing hybrid authentication configuration
✓ Local auth endpoint available (hybrid mode)
```

**Troubleshooting**:
- If fails with 404: Auth routes not configured
- If fails with 500: Auth dependency error
- If backend down: Connection refused

---

### Test 6: Performance

**What it tests**: Measures OIDC performance (JWKS caching effectiveness)

**Steps**:
1. Fetches JWKS 5 times sequentially
2. Measures response time each time
3. Calculates average
4. Validates caching is working

**Success criteria**:
- All requests succeed
- Average time < 100ms (with caching)
- First request may be slower (cache miss)

**Example output**:
```
ℹ Testing OIDC performance (JWKS caching)
ℹ JWKS fetch 1: 45.23ms
ℹ JWKS fetch 2: 12.45ms
ℹ JWKS fetch 3: 11.89ms
ℹ JWKS fetch 4: 13.12ms
ℹ JWKS fetch 5: 12.34ms
✓ Average JWKS fetch time: 19.01ms
✓ JWKS caching performing well
```

**Performance expectations**:
- First fetch: 50-200ms (network latency + processing)
- Subsequent fetches: <20ms (cached)
- Average should be heavily influenced by cache hits

---

## Custom Configuration

### Override Defaults

```bash
# Test custom Authelia instance
make test-oidc-integration \
  OIDC_ISSUER=http://auth.example.com \
  OIDC_CLIENT=myapp \
  API_URL=http://api.example.com

# Direct script usage
cd backend && uv run python scripts/test_oidc_integration.py \
  --issuer http://auth.example.com \
  --client-id myapp \
  --api http://api.example.com \
  --test-all
```

### Environment Variables

Set in shell before running:

```bash
export OIDC_ISSUER=http://localhost:9091
export OIDC_CLIENT_ID=parchmark-web
export PARCHMARK_API=http://localhost:8000

make test-oidc-integration
```

---

## Test Results Interpretation

### All Tests Passed ✓

```
=== Test Summary ===

✓ OIDC Discovery
✓ JWKS
✓ Token Validation
✓ API Health
✓ Hybrid Auth
✓ Performance

ℹ Passed: 6/6
✓ All tests passed!
```

**Meaning**: OIDC integration is working correctly. Safe to proceed with OIDC usage.

---

### Some Tests Failed ✗

```
=== Test Summary ===

✓ OIDC Discovery
✓ JWKS
✗ Token Validation
✓ API Health
✓ Hybrid Auth
⚠ Performance

ℹ Passed: 5/6
✗ 1 test(s) failed
```

**Meaning**: Issue detected. See the failed test output for diagnosis.

---

### Troubleshooting Failed Tests

#### Discovery Test Fails

**Symptoms**:
```
✗ Failed to connect to http://localhost:9091
```

**Causes**:
- Authelia not running
- Wrong URL
- Port not accessible
- Firewall blocking

**Solutions**:
1. Verify Authelia running: `docker ps | grep authelia`
2. Verify port: `curl -I http://localhost:9091`
3. Check firewall: `sudo iptables -L | grep 9091`
4. Restart: `docker restart authelia`

---

#### JWKS Test Fails

**Symptoms**:
```
✗ No signing keys found in JWKS
```

**Causes**:
- Authelia keys not generated
- OIDC not fully configured
- JWKS endpoint broken

**Solutions**:
1. Check Authelia logs: `docker logs authelia | grep -i "oidc\|key"`
2. Manually test JWKS: `curl http://localhost:9091/.well-known/openid-configuration/jwks`
3. Restart Authelia: `docker restart authelia`

---

#### Token Validation Fails

**Symptoms**:
```
✗ Unexpected status 500
```

**Causes**:
- Backend error in token validation
- Missing OIDC configuration
- JWKS fetch error

**Solutions**:
1. Check backend logs: `docker logs parchmark-backend | grep -i "error\|oidc"`
2. Verify env vars: `docker exec parchmark-backend env | grep OIDC`
3. Check backend health: `curl http://localhost:8000/api/health`

---

#### Health Test Fails

**Symptoms**:
```
✗ Backend unhealthy: database disconnected
```

**Causes**:
- Database not running
- Connection string wrong
- Database credentials wrong

**Solutions**:
1. Check database: `docker ps | grep postgres`
2. Check connection: `docker logs parchmark-backend | grep DATABASE`
3. Restart database: `docker restart postgres`

---

## Usage in CI/CD

### GitHub Actions Integration

```yaml
# .github/workflows/oidc-testing.yml
- name: Test OIDC Integration
  run: |
    make test-oidc-integration

- name: Test OIDC Performance
  run: |
    make test-oidc-perf
```

### Pre-Deployment Validation

```bash
#!/bin/bash
# scripts/validate-oidc.sh

echo "Validating OIDC configuration..."

# Test discovery
make test-oidc-discovery || exit 1

# Test JWKS
make test-oidc-jwks || exit 1

# Test tokens
make test-oidc-tokens || exit 1

# Test health
make test-oidc-health || exit 1

echo "✓ All OIDC validations passed!"
```

---

## Output Colors

The utility uses colored output for clarity:

| Color  | Meaning | Examples |
|--------|---------|----------|
| Green  | Success | ✓ Test passed |
| Red    | Error   | ✗ Test failed |
| Yellow | Warning | ⚠ Performance could improve |
| Cyan   | Info    | ℹ Additional information |

---

## Performance Benchmarking

### Expected Performance

**Normal operation**:
- OIDC discovery: 50-150ms
- JWKS fetch (first): 50-200ms
- JWKS fetch (cached): <20ms
- Token validation: <10ms (in-memory)
- Average JWKS: <50ms

**Performance issues if**:
- Discovery > 200ms: Network latency
- JWKS first > 500ms: Authelia slow
- JWKS cached > 100ms: Cache not working
- Token validation > 100ms: JWKS fetch slow

### Performance Optimization

If performance is poor:

1. **Check network**: `ping -c 10 localhost:9091`
2. **Check Authelia**: `docker stats authelia`
3. **Check backend**: `docker stats parchmark-backend`
4. **Increase cache TTL**: Edit `backend/app/auth/oidc_validator.py`

---

## Advanced Usage

### Testing Remote OIDC Provider

```bash
# Test production Authelia instance
make test-oidc-integration \
  --issuer https://auth.engen.tech \
  --api https://assets-api.engen.tech

# Or directly
cd backend && uv run python scripts/test_oidc_integration.py \
  --issuer https://auth.engen.tech \
  --api https://assets-api.engen.tech \
  --test-all
```

### Testing Multiple Configurations

```bash
#!/bin/bash
# Test multiple environments

for env in dev staging prod; do
  echo "Testing $env..."
  make test-oidc-integration \
    --issuer https://auth-$env.engen.tech \
    --api https://api-$env.engen.tech
done
```

### Continuous Monitoring

```bash
#!/bin/bash
# Monitor OIDC health continuously

while true; do
  echo "$(date): Testing OIDC..."
  make test-oidc-integration > /tmp/oidc-test.log

  if [ $? -eq 0 ]; then
    echo "✓ OIDC healthy"
  else
    echo "✗ OIDC failed - $(tail -5 /tmp/oidc-test.log)"
  fi

  sleep 300  # Test every 5 minutes
done
```

---

## Exit Codes

```
0 = All tests passed
1 = One or more tests failed
```

Use in scripts to detect failures:

```bash
make test-oidc-integration
if [ $? -eq 0 ]; then
  echo "OIDC is ready for deployment"
else
  echo "OIDC issues detected - do not deploy"
  exit 1
fi
```

---

## See Also

- **AUTHELIA_OIDC_LOCAL_TESTING.md** - Local testing with Docker Compose
- **AUTHELIA_OIDC_SMOKE_TEST.md** - Manual smoke test procedures
- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Comprehensive troubleshooting
- **AUTHELIA_OIDC_MONITORING.md** - Production monitoring

---

## Support

For issues with the testing utility:

1. Check the utility can connect: `curl http://localhost:9091`
2. Review test output for specific error
3. Check service logs: `docker logs <service>`
4. Refer to troubleshooting guide
