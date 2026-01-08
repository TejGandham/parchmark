# Authelia OIDC Monitoring & Metrics Guide

Monitor OIDC authentication in production using logs, metrics, and health checks.

## Overview

Production OIDC implementation requires monitoring of:
- Authentication success/failure rates
- Token validation performance
- JWKS fetch latency
- OIDC provider availability
- User auto-creation activity
- Token refresh patterns

---

## Log Monitoring

### Backend OIDC Logs

**Enable debug logging** in backend:

```bash
# In backend main.py or logging config
import logging
logging.getLogger('app.auth').setLevel(logging.DEBUG)
```

**Key log messages to monitor**:

```python
# OIDC token validation
"Validating OIDC token for user..."
"OIDC token validation success"
"OIDC token validation failed: <reason>"

# User creation
"Creating new OIDC user: <username>"
"OIDC user created successfully"
"Failed to create OIDC user: <reason>"

# JWKS caching
"Fetching JWKS from discovery endpoint"
"JWKS cached successfully"
"JWKS cache expired, refreshing"
```

**Grep for OIDC events**:

```bash
# All OIDC-related logs
docker logs parchmark-backend | grep -i oidc

# Validation failures
docker logs parchmark-backend | grep "validation failed"

# User creation
docker logs parchmark-backend | grep "user created"

# Errors
docker logs parchmark-backend | grep -i "error.*oidc\|oidc.*error"
```

### Frontend OIDC Logs

**Enable console logging**:

```javascript
// In browser console
localStorage.debug = 'app:*,oidc:*';
window.location.reload();

// Or set in app:
console.debug = true;
```

**Key events to monitor**:

```javascript
// OIDC flow
"Starting OIDC login..."
"OIDC callback received, exchanging code for tokens"
"OIDC tokens stored successfully"
"OIDC token refresh initiated"
"Token refresh successful"

// Errors
"OIDC login failed: <reason>"
"OIDC callback error: <reason>"
"Token refresh failed: <reason>"
```

### Authelia Logs

**Monitor Authelia for client issues**:

```bash
docker logs authelia | grep -i parchmark

# Client registration issues
docker logs authelia | grep "client.*not found"

# Token issues
docker logs authelia | grep -i "invalid.*token\|token.*invalid"

# OIDC flow issues
docker logs authelia | grep -i "redirect.*mismatch\|pkce.*failed"
```

---

## Health Checks

### Backend Health Endpoint

**Endpoint**: `GET /api/health`

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "ParchMark API",
  "version": "1.0.0"
}
```

**Monitor**:
- Response status: `200 OK`
- `database`: `"connected"`
- Response time: `<100ms`

```bash
# Test health
curl -I http://localhost:8000/api/health

# Monitor with uptime check
*/5 * * * * curl -f http://localhost:8000/api/health || alert "API unhealthy"
```

### OIDC Provider Availability

**Monitor discovery endpoint**:

```bash
# Test OIDC provider
curl -I https://auth.engen.tech/.well-known/openid-configuration

# Monitor with cron
*/5 * * * * curl -f https://auth.engen.tech/.well-known/openid-configuration || alert "OIDC provider unreachable"
```

### JWKS Endpoint

**Monitor JWKS accessibility**:

```bash
# Test JWKS
curl -I https://auth.engen.tech/.well-known/openid-configuration/jwks

# Count keys
curl https://auth.engen.tech/.well-known/openid-configuration/jwks | jq '.keys | length'
# Should be >= 1
```

---

## Metrics Collection

### Login Metrics

Track authentication attempts and success rates:

```python
# Backend - Add to auth endpoints
import logging
logger = logging.getLogger('metrics')

@app.post("/api/auth/login")
def login(credentials: LoginRequest):
    logger.info(f"auth.attempt|method:local|user:{credentials.username}")
    try:
        # ... login logic ...
        logger.info(f"auth.success|method:local|user:{user.username}")
    except Exception as e:
        logger.warning(f"auth.failure|method:local|reason:{e}")
```

**Metrics to collect**:
- `auth.attempt.local` - Local login attempts
- `auth.attempt.oidc` - OIDC login attempts
- `auth.success.local` - Local login successes
- `auth.success.oidc` - OIDC login successes
- `auth.failure.local` - Local login failures
- `auth.failure.oidc` - OIDC login failures
- `auth.user.created.local` - Local users created
- `auth.user.created.oidc` - OIDC users created

### Performance Metrics

Track OIDC operation latency:

```python
import time
from functools import wraps

def track_latency(operation_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                logger.info(f"oidc.{operation_name}.latency_ms|{duration_ms}")
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.warning(f"oidc.{operation_name}.error_latency_ms|{duration_ms}|{e}")
                raise
        return wrapper
    return decorator

@track_latency("token_validation")
def validate_oidc_token(token):
    # ... validation logic ...
    pass

@track_latency("jwks_fetch")
def get_jwks():
    # ... JWKS fetch ...
    pass
```

**Metrics to track**:
- `oidc.token_validation.latency_ms` - Token validation time
- `oidc.jwks_fetch.latency_ms` - JWKS fetch time
- `oidc.user_lookup.latency_ms` - Database user lookup
- `oidc.user_creation.latency_ms` - User creation time

### Cache Metrics

Track JWKS caching effectiveness:

```python
# In oidc_validator.py
class OIDCValidator:
    def __init__(self):
        self.jwks_cache_hits = 0
        self.jwks_cache_misses = 0

    async def get_jwks(self):
        # Check cache
        if self.jwks_cache and not self._cache_expired():
            self.jwks_cache_hits += 1
            logger.info(f"oidc.jwks.cache|hit|total_hits:{self.jwks_cache_hits}")
            return self.jwks_cache

        # Cache miss
        self.jwks_cache_misses += 1
        logger.info(f"oidc.jwks.cache|miss|total_misses:{self.jwks_cache_misses}")
        # ... fetch and cache ...
```

**Metrics**:
- `oidc.jwks.cache.hit` - Cache hit count
- `oidc.jwks.cache.miss` - Cache miss count
- `oidc.jwks.cache.hit_rate` - Hit rate percentage

---

## Alerts & Thresholds

### Critical Alerts

Set alerts for these conditions:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| OIDC provider unreachable | 1 failure | Page on-call |
| OIDC token validation failing | >5% of requests | Investigate Authelia |
| User auto-creation failing | >1% of OIDC logins | Check database |
| Token validation latency | >500ms | Check JWKS fetch |
| API health check failing | 3 consecutive checks | Page on-call |

### Warning Alerts

| Condition | Threshold | Action |
|-----------|-----------|--------|
| High OIDC login failure rate | >10% | Monitor and investigate |
| JWKS cache miss rate increasing | >50% hit rate drop | Check OIDC provider |
| Token validation latency increasing | >200ms avg | Check backend performance |
| DB query latency increasing | >100ms | Monitor database |

### Alert Configuration Examples

**Prometheus-style alerts**:

```yaml
groups:
  - name: oidc
    rules:
      # OIDC provider down
      - alert: OIDCProviderDown
        expr: up{job="authelia"} == 0
        for: 2m
        annotations:
          summary: "OIDC provider (Authelia) is down"

      # High token validation failure rate
      - alert: HighOIDCValidationFailureRate
        expr: rate(oidc_validation_failures[5m]) / rate(oidc_validation_attempts[5m]) > 0.05
        for: 5m
        annotations:
          summary: "OIDC validation failure rate >5%"

      # JWKS cache missing
      - alert: JWKSCacheMissing
        expr: up{job="jwks"} == 0
        for: 1m
        annotations:
          summary: "JWKS caching is failing"
```

**Log-based alerts**:

```bash
# Alert on OIDC validation failures
ERROR "Validation failed" \
  && ACTION "Page on-call" \
  && COOLDOWN 15m

# Alert on user creation failures
ERROR "Failed to create.*OIDC user" \
  && ACTION "Create incident" \
  && COOLDOWN 30m
```

---

## Dashboard Metrics

### Key Dashboard Panels

**Authentication Overview**:
- Local logins (24h, 7d, 30d trends)
- OIDC logins (24h, 7d, 30d trends)
- Total authentication attempts
- Success rate % (local, OIDC, combined)

**OIDC Performance**:
- Token validation latency (p50, p95, p99)
- JWKS fetch latency
- JWKS cache hit rate
- Token refresh latency

**User Activity**:
- New OIDC users created (24h, 7d, 30d)
- Active OIDC users
- Active local users
- User retention

**Errors**:
- OIDC validation errors (rate/count)
- OIDC provider errors
- User creation errors
- Database errors

### Sample Queries

**Grafana/Prometheus**:

```promql
# OIDC login rate
rate(oidc_logins_total[5m])

# Local login rate
rate(local_logins_total[5m])

# Combined success rate
rate(auth_success_total[5m]) / rate(auth_attempt_total[5m])

# Token validation latency p95
histogram_quantile(0.95, oidc_validation_duration_seconds_bucket)

# JWKS cache hit rate
increase(jwks_cache_hits_total[5m]) / (increase(jwks_cache_hits_total[5m]) + increase(jwks_cache_misses_total[5m]))

# User creation rate
rate(oidc_users_created_total[5m])
```

---

## Log Aggregation

### Centralized Logging Setup

**ELK Stack Example**:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/parchmark/backend.log
    fields:
      service: parchmark-backend
    processors:
      - add_kubernetes_metadata:
      - add_docker_metadata:

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "parchmark-%{+yyyy.MM.dd}"
```

**Log parsing**:

```json
{
  "timestamp": "2025-01-08T12:34:56Z",
  "service": "parchmark-backend",
  "level": "INFO",
  "message": "auth.success|method:oidc|user:john@example.com",
  "metrics": {
    "auth_method": "oidc",
    "auth_result": "success",
    "username": "john@example.com"
  }
}
```

---

## Best Practices

### 1. Structured Logging

Use JSON format for easy parsing:

```python
import json

# Instead of: logger.info(f"User {user} logged in")
# Use:
logger.info(json.dumps({
    "event": "auth.success",
    "method": "oidc",
    "username": username,
    "duration_ms": duration,
    "timestamp": datetime.now().isoformat()
}))
```

### 2. Correlation IDs

Track requests end-to-end:

```python
import uuid

def middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log with correlation ID
    logger.info(f"correlation_id: {request_id}, event: auth_attempt")

    response = await call_next(request)
    return response
```

### 3. Sampling for High-Volume Events

Don't log every request, sample:

```python
import random

if random.random() < 0.1:  # Log 10% of requests
    logger.info(f"auth_attempt|sampled|rate:10%")
```

### 4. Privacy in Logs

Never log sensitive data:

```python
# BAD:
logger.info(f"Password: {password}")

# GOOD:
logger.info(f"Auth attempt for user: {username}")
```

---

## Runbooks

### OIDC Provider Down

**Symptoms**:
- OIDC logins failing
- Error: "Cannot reach OIDC provider"
- Alerts: OIDCProviderDown

**Investigation**:
```bash
# 1. Check OIDC provider
curl -I https://auth.engen.tech/.well-known/openid-configuration

# 2. Check connectivity
docker exec parchmark-backend ping auth.engen.tech

# 3. Check Authelia service
docker ps | grep authelia
docker logs authelia | tail -50

# 4. Check firewall
iptables -L | grep 9091 # if applicable
```

**Resolution**:
1. Restart Authelia: `docker restart authelia`
2. Check Authelia logs for errors
3. Contact Authelia team if still down
4. Enable local login fallback

### High Token Validation Failure Rate

**Symptoms**:
- >5% OIDC logins failing
- Error: "Token validation failed"
- Metrics: oidc_validation_failures increasing

**Investigation**:
```bash
# 1. Check JWKS
curl https://auth.engen.tech/.well-known/openid-configuration/jwks | jq '.keys | length'

# 2. Check backend logs
docker logs parchmark-backend | grep "validation failed"

# 3. Check token claims
# Decode token in browser console
function decodeJWT(token) {
  const parts = token.split('.');
  return JSON.parse(atob(parts[1]));
}

# 4. Check configuration
docker exec parchmark-backend env | grep OIDC
```

**Resolution**:
1. Verify OIDC_ISSUER_URL matches Authelia issuer
2. Verify OIDC_AUDIENCE matches Authelia client ID
3. Check system clock sync (clock skew issues)
4. Restart backend with correct config

### User Auto-Creation Failing

**Symptoms**:
- OIDC login succeeds but no user created
- Error: "Failed to create user"
- No new records in database

**Investigation**:
```bash
# 1. Check database schema
docker exec postgres psql -U parchmark_user -d parchmark_db -c "\d users"

# 2. Check for constraint violations
docker logs parchmark-backend | grep -i "constraint\|duplicate"

# 3. Check user lookup
docker exec postgres psql -U parchmark_user -d parchmark_db -c \
  "SELECT * FROM users WHERE auth_provider='oidc' LIMIT 5;"

# 4. Check error details
docker logs parchmark-backend | grep -i "create.*user\|user.*create" | tail -20
```

**Resolution**:
1. Apply database migrations if not done
2. Check for duplicate oidc_sub values
3. Verify OIDC_USERNAME_CLAIM is set correctly
4. Check database permissions
5. Restart backend to clear any connection issues

---

## Summary

**Monitoring Checklist**:
- [ ] Health check endpoint monitoring (5-min interval)
- [ ] OIDC provider availability check (5-min interval)
- [ ] Backend logs aggregated and searchable
- [ ] Critical alerts configured
- [ ] Metrics dashboard created
- [ ] Runbooks documented
- [ ] On-call rotation aware of OIDC
- [ ] Weekly log review for anomalies

**Key Metrics to Track**:
- Authentication success rate
- Token validation latency
- JWKS cache hit rate
- User auto-creation rate
- OIDC provider availability
- Error rates by type

**Regular Reviews**:
- Daily: Error rate trends
- Weekly: Performance metrics
- Monthly: Capacity planning
- Quarterly: Security audit
