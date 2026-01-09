# Authelia OIDC Deployment Checklist

This checklist ensures a safe, secure deployment of the Authelia OIDC integration to production.

## Pre-Deployment Phase

### 1. Code Review
- [ ] All OIDC-related code has been reviewed
- [ ] Security vulnerabilities have been addressed
- [ ] Error handling is comprehensive
- [ ] No hardcoded secrets in code
- [ ] No debugging code left in production paths

### 2. Testing
- [ ] `make test-all` passes locally
- [ ] `make test-backend-oidc` passes with 90%+ coverage
- [ ] `make test-ui-oidc` passes with 90%+ coverage
- [ ] All OIDC smoke tests pass
- [ ] No flaky tests identified
- [ ] Error scenarios tested

### 3. Documentation Review
- [ ] Environment variable documentation is up-to-date
- [ ] Smoke test guide is accurate
- [ ] Deployment instructions are clear
- [ ] Troubleshooting guide addresses known issues
- [ ] Team is trained on OIDC flow

### 4. Dependencies
- [ ] `httpx` is pinned in production
- [ ] `oidc-client-ts` version is stable (not alpha/beta)
- [ ] All transitive dependencies are reviewed
- [ ] No deprecated packages used

## Authelia Configuration Phase

### 1. OIDC Client Registration
- [ ] "parchmark-web" OIDC client created in Authelia
- [ ] Client set as "public": true (no client secret)
- [ ] PKCE enabled with S256 challenge method
- [ ] Grant types include "authorization_code" and "refresh_token"
- [ ] Scopes: openid, profile, email
- [ ] Redirect URIs configured:
  - [ ] Production: `https://notes.engen.tech/oidc/callback`
  - [ ] Development: `http://localhost:5173/oidc/callback` (if needed)

### 2. OIDC Endpoints Verification
- [ ] Discovery endpoint returns valid configuration:
  - [ ] issuer
  - [ ] authorization_endpoint
  - [ ] token_endpoint
  - [ ] jwks_uri
  - [ ] end_session_endpoint
- [ ] JWKS endpoint returns valid keys
- [ ] All endpoints are HTTPS in production

### 3. Authelia Security
- [ ] TLS/SSL certificate is valid and not expiring soon
- [ ] CORS headers permit frontend domain
- [ ] OIDC session timeout is reasonable (15-60 minutes)
- [ ] Token expiration is set (15-60 minutes for access, 7 days for refresh)
- [ ] Authelia is reachable from backend service

## Backend Deployment Phase

### 1. Environment Variables
- [ ] `AUTH_MODE=hybrid` set (or appropriate mode)
- [ ] `OIDC_ISSUER_URL=https://auth.engen.tech` (correct URL)
- [ ] `OIDC_AUDIENCE=parchmark-web` (matches Authelia config)
- [ ] `OIDC_USERNAME_CLAIM=preferred_username` set
- [ ] `ALLOWED_ORIGINS` includes frontend domain
- [ ] All other required vars set and validated

### 2. Database Preparation
- [ ] Database migrations applied successfully
- [ ] User table has new columns: oidc_sub, email, auth_provider
- [ ] Existing users have auth_provider='local' and password_hash set
- [ ] oidc_sub column is unique (nullable for local users)
- [ ] Database backups taken before deployment

### 3. Backend Testing
- [ ] Backend starts without errors
- [ ] `GET /api/health` returns with database: connected
- [ ] OIDC configuration loaded correctly
  - Check: `docker logs parchmark-backend | grep -i "oidc"`
- [ ] No errors in startup logs
- [ ] Database connections working

### 4. JWKS Verification
- [ ] Backend can reach Authelia discovery endpoint
- [ ] Backend can fetch and cache JWKS
- [ ] JWKS is cached (verify via logs or metrics)

Test:
```bash
curl -X GET https://assets-api.engen.tech/api/health
# Should return with "database": "connected"
```

## Frontend Deployment Phase

### 1. Environment Variables
- [ ] `VITE_OIDC_ISSUER_URL=https://auth.engen.tech` set
- [ ] `VITE_OIDC_CLIENT_ID=parchmark-web` set
- [ ] `VITE_OIDC_REDIRECT_URI=https://notes.engen.tech/oidc/callback` set
- [ ] `VITE_OIDC_LOGOUT_REDIRECT_URI=https://notes.engen.tech/login` set
- [ ] `VITE_API_URL` points to backend
- [ ] All required vars set and validated

### 2. Frontend Build
- [ ] Build succeeds without errors: `npm run build`
- [ ] No TypeScript errors
- [ ] No ESLint warnings in auth module
- [ ] Bundle size is acceptable
- [ ] Source maps are excluded from production build

### 3. Frontend Testing
- [ ] Login page loads
- [ ] "Sign In with SSO" button visible and styled correctly
- [ ] Local login still works
- [ ] SSO redirect works (check console for any errors)

Test:
```javascript
// In browser console
console.log(import.meta.env.VITE_OIDC_ISSUER_URL);
console.log(import.meta.env.VITE_OIDC_CLIENT_ID);
console.log(import.meta.env.VITE_OIDC_REDIRECT_URI);
```

### 4. Nginx Configuration
- [ ] CORS headers allow Authelia domain (if cross-origin)
- [ ] HTTPS is enforced
- [ ] Security headers are set
- [ ] Proxy headers are correct (X-Forwarded-Proto, etc.)

## DNS and Network Phase

### 1. DNS Resolution
- [ ] `auth.engen.tech` resolves correctly
- [ ] `notes.engen.tech` resolves correctly
- [ ] `assets-api.engen.tech` resolves correctly
- [ ] All DNS A records point to correct IPs

### 2. Network Connectivity
- [ ] Backend can reach Authelia (port 9091 or 443)
- [ ] Frontend can reach Authelia (port 443)
- [ ] Frontend can reach Backend API
- [ ] Firewall rules allow necessary traffic
- [ ] No rate limiting blocking OIDC endpoints

Test from production:
```bash
# From backend
curl -I https://auth.engen.tech/.well-known/openid-configuration

# From frontend (browser console)
fetch('https://auth.engen.tech/.well-known/openid-configuration')
  .then(r => r.json())
  .then(console.log)
```

## Production Verification Phase

### 1. Health Checks
- [ ] Backend health endpoint works: `GET /api/health`
- [ ] Response includes: `"database": "connected"`
- [ ] Frontend health check (can reach it in browser)

### 2. Smoke Tests
- [ ] Local login works
- [ ] SSO login works
- [ ] New OIDC user auto-created
- [ ] Existing OIDC user can login
- [ ] User isolation (notes not visible to other users)
- [ ] Token refresh works
- [ ] Logout works
- [ ] 401 error handling works

### 3. Database Verification
- [ ] OIDC users are created with correct fields
- [ ] oidc_sub is populated and unique
- [ ] email is populated
- [ ] auth_provider is set to 'oidc'
- [ ] password_hash is NULL for OIDC users

### 4. Logs Inspection
- [ ] No error logs in backend
- [ ] No error logs in frontend (console)
- [ ] OIDC token validation succeeding
- [ ] No spurious 401 errors
- [ ] Database operations succeeding

### 5. Monitoring Setup
- [ ] Application metrics being collected
- [ ] Error rate baseline established
- [ ] Token refresh rate baseline established
- [ ] OIDC provider latency being monitored
- [ ] Alerts configured for high error rates

## Security Phase

### 1. Secrets Management
- [ ] No secrets in Git
- [ ] All secrets in secure vault
- [ ] Environment variables use secure source
- [ ] No SSH keys or tokens in logs
- [ ] Rotation schedule established

### 2. HTTPS/TLS
- [ ] All traffic is HTTPS
- [ ] Certificate is valid and trusted
- [ ] Certificate expiration is monitored (alert 30 days before)
- [ ] TLS version is 1.2+
- [ ] Cipher suites are strong

### 3. CORS
- [ ] CORS allows only necessary origins
- [ ] CORS credentials properly configured
- [ ] No wildcard CORS origins
- [ ] Preflight requests working correctly

### 4. Token Security
- [ ] Token storage is secure (localStorage OK for tokens, not secrets)
- [ ] Token expiration is appropriate (15-60 minutes for access)
- [ ] Refresh token storage is secure
- [ ] Token validation is strict
- [ ] No token logging in production

### 5. Authentication Flow
- [ ] Authorization code flow is used (not implicit)
- [ ] PKCE is enforced
- [ ] State parameter validation working
- [ ] Nonce validation working (if available)
- [ ] No cross-site request forgery (CSRF) vulnerability

## Performance Phase

### 1. Response Times
- [ ] Login page loads in < 2 seconds
- [ ] SSO redirect happens in < 1 second
- [ ] Token validation happens in < 50ms (with JWKS cache)
- [ ] API requests with OIDC token in < 100ms

### 2. Resource Usage
- [ ] Backend memory usage is stable
- [ ] Frontend bundle size acceptable (< 500KB gzip)
- [ ] JWKS cache reduces requests by 99%
- [ ] Database queries are efficient

### 3. Concurrency
- [ ] System handles 100+ concurrent users
- [ ] Token refresh doesn't cause bottlenecks
- [ ] JWKS cache is thread-safe
- [ ] No race conditions in user creation

## Rollback Phase

### 1. Rollback Plan
- [ ] Previous version is still deployable
- [ ] Database migrations are reversible (if needed)
- [ ] Fallback auth method available (local login)
- [ ] Rollback procedure is documented

### 2. Rollback Testing
- [ ] Rollback to previous version successful
- [ ] All functionality restored after rollback
- [ ] No data corruption during rollback

## Post-Deployment Phase

### 1. Monitoring
- [ ] Alerts are configured for:
  - [ ] High error rates
  - [ ] OIDC provider unreachable
  - [ ] Token validation failures
  - [ ] Database errors
- [ ] Dashboards show OIDC metrics
- [ ] User authentication patterns are normal

### 2. Support
- [ ] Support team trained on OIDC troubleshooting
- [ ] Escalation procedures documented
- [ ] Known issues documented
- [ ] Contact information for Authelia support available

### 3. Documentation Updates
- [ ] Runbook updated with OIDC steps
- [ ] Incident response guide includes OIDC scenarios
- [ ] Team wiki/documentation current
- [ ] Password reset procedures updated (consider OIDC users)

### 4. Feedback Collection
- [ ] Collect user feedback on SSO experience
- [ ] Track OIDC-related support tickets
- [ ] Monitor for any issues
- [ ] Plan follow-up improvements

## Sign-Off

| Role | Name | Date | Sign |
|------|------|------|------|
| Developer | | | |
| QA | | | |
| DevOps/Ops | | | |
| Security | | | |
| Product Owner | | | |

## Deployment Timeline

- **T-1 hour**: Final verification and smoke tests
- **T-0**: Deploy to production
- **T+5 min**: Health checks and basic smoke tests
- **T+15 min**: Full smoke test suite
- **T+30 min**: Monitoring review and alert configuration
- **T+1 hour**: Team debrief and documentation updates
- **T+24 hours**: Monitor for any issues
- **T+7 days**: Post-deployment review

## Emergency Contacts

- **Authelia Support**: [Contact information]
- **Backend Team**: [Contact information]
- **Frontend Team**: [Contact information]
- **Security Team**: [Contact information]
- **On-Call**: [Phone/Slack]

## Appendix: Troubleshooting Reference

### OIDC Provider Unreachable
- Check network connectivity
- Check DNS resolution
- Check firewall rules
- Check TLS certificate validity
- Refer to: AUTHELIA_OIDC_SMOKE_TEST.md

### User Auto-Creation Failing
- Verify database schema migration applied
- Check backend logs
- Verify OIDC_USERNAME_CLAIM is correct
- Refer to: AUTHELIA_OIDC_ENV.md

### Token Validation Failing
- Verify OIDC_ISSUER_URL matches Authelia
- Verify OIDC_AUDIENCE matches Authelia config
- Check JWKS endpoint accessibility
- Check token expiration
- Refer to: AUTHELIA_OIDC_SMOKE_TEST.md

For additional help, refer to:
- `docs/AUTHELIA_OIDC_PLAN.md` - Implementation plan
- `docs/AUTHELIA_OIDC_ENV.md` - Environment variables
- `docs/AUTHELIA_OIDC_IMPLEMENTATION.md` - Technical details
- `docs/AUTHELIA_OIDC_SMOKE_TEST.md` - Test procedures
