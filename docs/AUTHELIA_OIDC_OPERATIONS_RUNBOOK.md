# Authelia OIDC Operations Runbook

Comprehensive operational procedures for running ParchMark with Authelia OIDC authentication in production.

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring](#monitoring)
3. [Common Issues & Resolution](#common-issues--resolution)
4. [Incident Response](#incident-response)
5. [Capacity Planning](#capacity-planning)
6. [Backup & Recovery](#backup--recovery)
7. [Maintenance Windows](#maintenance-windows)
8. [Escalation Procedures](#escalation-procedures)

---

## Daily Operations

### Morning Health Check (5 minutes)

**Frequency**: Every morning before users arrive

**Procedure**:
```bash
# 1. Check ParchMark API health
curl -s https://assets-api.engen.tech/api/health | jq .

# 2. Check Authelia health
curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'

# 3. Check frontend availability
curl -s -o /dev/null -w "%{http_code}" https://notes.engen.tech

# 4. Check recent error logs
docker logs parchmark-backend --since 10m 2>&1 | grep -i "error\|warning" | head -20

# 5. Check database connectivity
docker exec parchmark-backend python -c "from app.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```

**Expected Output**:
- API health: `{"status": "ok", "database": "connected"}`
- Authelia: issuer URL (e.g., `"https://auth.engen.tech"`)
- Frontend: HTTP 200
- Logs: No OIDC validation errors
- Database: "DB OK"

**If any check fails**: See [Common Issues](#common-issues--resolution) section

### User Activity Monitoring (Daily)

**Frequency**: Check at end of business day

**Procedure**:
```bash
# 1. Count authentication attempts by method
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  SELECT
    auth_provider,
    COUNT(*) as total_logins,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h
  FROM users
  GROUP BY auth_provider;
"

# 2. Check for failed login patterns
docker logs parchmark-backend --since 24h 2>&1 | grep -i "invalid\|unauthorized" | wc -l

# 3. Monitor active sessions
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  SELECT
    COUNT(DISTINCT user_id) as active_users,
    MIN(created_at) as oldest_session
  FROM active_sessions
  WHERE expires_at > NOW();
"
```

**Expected Patterns**:
- Gradual increase in OIDC logins as users adopt
- <5% authentication failures (normal rate)
- Active sessions match concurrent user base

### Credential Rotation Check (Weekly)

**Frequency**: Every Monday morning

**Procedure**:
```bash
# 1. Verify Authelia secrets haven't been exposed
cd /path/to/parchmark
grep -r "OIDC_CLIENT_SECRET" . --exclude-dir=.git || echo "No secrets in repo (good)"

# 2. Check JWT secret age
docker exec parchmark-backend python -c "
import os
from datetime import datetime
secret = os.getenv('SECRET_KEY')
if len(secret) < 32:
    print('WARNING: SECRET_KEY too short')
else:
    print(f'SECRET_KEY length: {len(secret)} (OK)')
"

# 3. Review GitHub Secrets last update
# (Manual: Check GitHub repo settings > Secrets > Updated dates)
# Secrets should be rotated every 90 days
```

---

## Monitoring

### Key Metrics to Track

**Backend Metrics** (via logs and database):
- Authentication success rate (target: >99%)
- Token validation latency (target: <10ms)
- OIDC provider response time (target: <200ms)
- Database connection pool utilization
- Error rate by type (target: <0.1%)

**Frontend Metrics**:
- Page load time (target: <3s)
- OIDC callback completion rate (target: >98%)
- Token expiration proactive logout (should be 0 unexpected logouts)

**Authelia Integration Metrics**:
- Authorization endpoint response time
- Token endpoint response time
- JWKS endpoint cache hit rate
- Session timeout incidents

### Monitoring Setup (Prometheus)

**Create `/path/to/prometheus/authelia-oidc-rules.yml`**:

```yaml
groups:
  - name: authelia_oidc
    interval: 30s
    rules:
      # Alert when auth fails >1%
      - alert: HighAuthenticationFailureRate
        expr: |
          (
            rate(parchmark_auth_failures_total[5m]) /
            (rate(parchmark_auth_attempts_total[5m]) + 0.0001)
          ) > 0.01
        for: 5m
        annotations:
          summary: "High authentication failure rate"
          description: "Auth failure rate > 1% for 5 minutes"

      # Alert when token validation slow
      - alert: SlowOIDCTokenValidation
        expr: |
          histogram_quantile(0.95, rate(parchmark_token_validation_duration_seconds_bucket[5m])) > 0.05
        for: 5m
        annotations:
          summary: "OIDC token validation slow"
          description: "95th percentile token validation > 50ms"

      # Alert when OIDC provider down
      - alert: OIDCProviderUnreachable
        expr: |
          rate(parchmark_oidc_provider_errors_total[5m]) > 0.1
        for: 2m
        annotations:
          summary: "OIDC provider unreachable"
          description: "Authelia provider errors detected"

      # Alert on database migration issues
      - alert: DatabaseMigrationFailure
        expr: |
          parchmark_db_migration_success == 0
        for: 1m
        annotations:
          summary: "Database migration failed"
          description: "Latest migration attempt failed"
```

### Log Aggregation (ELK Stack)

**Logstash Configuration for OIDC events**:

```ruby
filter {
  if [docker][container_name] =~ /parchmark-backend/ {
    # Parse OIDC validation logs
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} .*OIDC.*%{GREEDYDATA:oidc_event}"
      }
    }

    # Extract relevant fields
    if [message] =~ /OIDC/ {
      mutate {
        add_field => { "event_type" => "oidc" }
      }

      if [message] =~ /validation failed/ {
        mutate { add_field => { "severity" => "warning" } }
      }
      if [message] =~ /provider error/ {
        mutate { add_field => { "severity" => "critical" } }
      }
    }
  }
}

output {
  if [event_type] == "oidc" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "parchmark-oidc-%{+YYYY.MM.dd}"
    }
  }
}
```

### Grafana Dashboard Setup

**Dashboard Title**: "Authelia OIDC - ParchMark Monitoring"

**Key Panels**:
1. **Authentication Rate** (Graph)
   - Query: `rate(parchmark_auth_attempts_total[5m])` by source (local vs OIDC)
   - Target: Smooth trending, gradual OIDC growth

2. **Auth Success Rate** (Gauge)
   - Query: `parchmark_auth_success_rate`
   - Target: >99%

3. **Token Validation Latency** (Heatmap)
   - Query: `parchmark_token_validation_duration_seconds_bucket`
   - Target: P95 < 10ms

4. **OIDC Provider Status** (Status Panel)
   - Query: `parchmark_oidc_provider_up`
   - Shows: UP/DOWN with last error timestamp

5. **User Growth by Auth Method** (Graph)
   - Query: `count(users) by auth_provider`
   - Shows: Adoption trend

6. **Database Connection Pool** (Gauge)
   - Query: `parchmark_db_connections_active / parchmark_db_connections_max`
   - Target: <80%

---

## Common Issues & Resolution

### Issue 1: Users Getting "Invalid Client ID" Errors

**Symptoms**:
- Users see "Invalid client_id" error when clicking SSO button
- This started after recent deployment

**Diagnosis**:
```bash
# Check OIDC client is registered in Authelia
docker logs authelia | grep -i "parchmark-web"

# Verify Authelia configuration
docker exec authelia cat /etc/authelia/configuration.yml | grep -A 10 "parchmark-web"

# Check frontend has correct client ID
grep VITE_OIDC_CLIENT_ID .env.production
```

**Resolution**:
1. **If client not registered**: Add to Authelia config and restart
   ```yaml
   identity_providers:
     oidc:
       clients:
         - id: parchmark-web
           public: true
           redirect_uris:
             - "https://notes.engen.tech/oidc/callback"
   ```

2. **If client ID mismatch**: Update frontend .env to match
   ```bash
   VITE_OIDC_CLIENT_ID=parchmark-web
   ```

3. **Restart services**:
   ```bash
   docker compose -f docker-compose.prod.yml restart authelia parchmark-backend parchmark-frontend
   ```

4. **Verify**: Try SSO login again

---

### Issue 2: "Authorization Code Already Used" Errors

**Symptoms**:
- Users see "Authorization code already used" error during callback
- Usually happens on page refresh during callback handling

**Diagnosis**:
```bash
# Check backend logs for code reuse attempts
docker logs parchmark-backend --since 1h | grep -i "authorization.*code.*used"

# This is logged when handleOIDCCallback attempts to exchange the same code twice
```

**Root Cause**:
- User refreshes browser during callback page load (code exchange in progress)
- Race condition where code is exchanged twice

**Resolution**:
1. **Frontend**: Ensure callback page shows loading indicator with text
   ```typescript
   return (
     <Center h="100vh">
       <Spinner />
       <Text>Completing login...</Text>
     </Center>
   );
   ```

2. **User guidance**: Tell users not to refresh during callback (usually <2 seconds)

3. **Monitoring**: Track rate of this error
   ```bash
   docker logs parchmark-backend --since 24h | grep -c "code already used"
   ```

---

### Issue 3: Token Expiration Causing Automatic Logouts

**Symptoms**:
- Users report being logged out unexpectedly
- No user interaction, just happens after 30+ minutes of inactivity
- More common with OIDC than local auth

**Diagnosis**:
```bash
# Check token expiration settings
docker exec parchmark-backend python -c "
import os
print(f'ACCESS_TOKEN_EXPIRE_MINUTES: {os.getenv(\"ACCESS_TOKEN_EXPIRE_MINUTES\", 30)}')
"

# Check frontend token monitoring
curl https://notes.engen.tech -H "Authorization: Bearer [token]" -I

# Monitor logout events by source
docker logs parchmark-backend --since 24h | grep -i "logout\|token.*expired"
```

**Root Causes**:
1. **Token legitimately expired** (30 minute lifetime)
   - Expected behavior for security

2. **Token refresh failed**
   - OIDC provider down or unreachable
   - Network connectivity issue

3. **Clock skew** between client and server
   - Device time is significantly off

**Resolution**:

**For Case 1 (Legitimate Expiration)**: Document this is expected behavior for security
- Inform users: "Tokens automatically refresh every 30 minutes"
- If refresh fails, users see logout prompt

**For Case 2 (Refresh Failure)**:
```bash
# Check OIDC provider status
curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'

# If provider is slow, check its health
docker logs authelia | tail -50 | grep -i "error"

# Restart Authelia if needed
docker restart authelia
```

**For Case 3 (Clock Skew)**:
```bash
# Check server time
date

# Check client time matches server
# (Difficult to do at scale - send alert to users to sync their device time)

# Adjust clock skew buffer in token validation (if needed)
# Backend already has 10-second buffer built in
```

---

### Issue 4: "User Not Found" or "No OIDC User Created"

**Symptoms**:
- OIDC login succeeds (redirects back to app)
- Then shows "User not found" error
- Usually happens on first OIDC login

**Diagnosis**:
```bash
# Check if user was created in database
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  SELECT * FROM users WHERE oidc_sub = 'authelia-user-id';
"

# Check backend logs for auto-create errors
docker logs parchmark-backend --since 10m | grep -i "create\|oidc" | tail -20

# Check OIDC token contents
# (Manually decode JWT from browser console:
#  atob(token.split('.')[1]) to see claims)
```

**Root Causes**:
1. **Database migration not applied**
   - User model missing oidc_sub column

2. **OIDC token missing required claims**
   - Missing "sub", "preferred_username", or "email"

3. **Database unique constraint violation**
   - OIDC user with same oidc_sub already exists (shouldn't happen)

**Resolution**:

**For Case 1 (Migration)**:
```bash
# Apply migrations
docker exec parchmark-backend python -m alembic upgrade head

# Or restart with auto-migration
docker restart parchmark-backend

# Verify columns exist
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  \d users
" | grep "oidc_sub\|auth_provider"
```

**For Case 2 (Missing Claims)**:
```bash
# Check OIDC token claims in backend logs
docker logs parchmark-backend | grep "extract_username\|extract_user_info"

# If claims missing, check Authelia configuration for correct scopes
docker exec authelia cat /etc/authelia/configuration.yml | grep -A 5 "scopes"

# Scopes should include: "openid profile email"
```

**For Case 3 (Constraint Violation)**:
```bash
# Check for duplicate oidc_sub values
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  SELECT oidc_sub, COUNT(*) FROM users
  WHERE oidc_sub IS NOT NULL
  GROUP BY oidc_sub HAVING COUNT(*) > 1;
"

# If duplicates found, manually fix by reviewing which to keep
# (Unlikely - unique constraint should prevent this)
```

---

### Issue 5: OIDC Provider (Authelia) Downtime

**Symptoms**:
- Users can't login with SSO
- "Connection refused" or timeout errors
- Error mentions "auth.engen.tech" or provider URL

**Diagnosis**:
```bash
# Check Authelia container status
docker ps | grep authelia

# Check if container is running
docker exec authelia echo "Authelia is running"

# Check Authelia logs for errors
docker logs authelia | tail -50

# Check if port 9091 is accessible
curl -v https://auth.engen.tech:9091 2>&1 | head -20

# Check network connectivity from backend
docker exec parchmark-backend curl -v https://auth.engen.tech/.well-known/openid-configuration
```

**Resolution**:

**If Authelia not running**:
```bash
# Start Authelia
docker compose -f docker-compose.prod.yml up -d authelia

# Wait for health check
sleep 10

# Verify it's healthy
curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'
```

**If Authelia running but responding slowly**:
```bash
# Check database connectivity (Authelia stores users in DB)
docker logs authelia | grep -i "database\|connection"

# Restart Authelia
docker restart authelia

# Monitor recovery
docker logs authelia -f
```

**If port unreachable**:
```bash
# Check Docker network
docker network ls
docker network inspect parchmark_default

# Check Nginx routing (if using proxy)
curl -v https://auth.engen.tech/

# Verify DNS resolution
nslookup auth.engen.tech
```

**For users during outage**:
- Local login still works
- Users can temporarily use local auth
- Create incident notification

---

## Incident Response

### P1: Authentication System Down (All Users Affected)

**Definition**: Users can't login via either local or OIDC methods

**Detection**:
- Alert: "High authentication failure rate > 10%"
- Users report "can't login"

**Response Steps**:

1. **Immediate (0-5 min)**:
   ```bash
   # Check backend health
   curl -s https://assets-api.engen.tech/api/health

   # Check all services running
   docker ps | grep parchmark

   # Restart backend if needed
   docker restart parchmark-backend
   ```

2. **If Backend Down (5-10 min)**:
   ```bash
   # Check logs for startup errors
   docker logs parchmark-backend --tail 100

   # Check database connectivity
   docker exec parchmark-backend python -c "from app.database import SessionLocal; SessionLocal()"

   # Restart Docker stack
   docker compose -f docker-compose.prod.yml restart
   ```

3. **If Database Down (10-15 min)**:
   ```bash
   # Check PostgreSQL
   docker ps | grep postgres

   # Restart database
   docker restart parchmark-db

   # Wait for recovery
   sleep 30
   docker logs parchmark-db | tail -20

   # Restart backend after DB is healthy
   docker restart parchmark-backend
   ```

4. **Communication**:
   - Post status update to team Slack
   - Update status page (if exists)
   - Estimate time to resolution

5. **Recovery Verification**:
   ```bash
   # Test local login works
   curl -X POST https://assets-api.engen.tech/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}'

   # Test OIDC flow
   curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'
   ```

**Resolution Time Target**: < 15 minutes

---

### P2: OIDC Only Down (Users Can Use Local Auth)

**Definition**: SSO login broken, but local login works

**Detection**:
- OIDC callback errors in logs
- Users report "SSO button doesn't work"

**Response Steps**:

1. **Immediate (0-5 min)**:
   ```bash
   # Check Authelia status
   docker ps | grep authelia
   docker logs authelia | tail -30

   # Check connectivity to Authelia
   curl -s https://auth.engen.tech/.well-known/openid-configuration
   ```

2. **If Authelia Down**:
   ```bash
   # Restart Authelia
   docker restart authelia

   # Wait for it to be ready
   sleep 20

   # Verify it's responding
   curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'
   ```

3. **If Authelia Slow**:
   ```bash
   # Check resource usage
   docker stats authelia

   # If high memory/CPU, restart it
   docker restart authelia

   # Monitor performance
   docker logs authelia -f
   ```

4. **User Communication**:
   - Post in Slack: "SSO temporarily unavailable, please use local login"
   - Estimated recovery time

5. **Root Cause Investigation** (After recovery):
   - Check logs for what caused outage
   - Was it a crash? Hang? Memory leak?
   - Implement fix if needed

**Resolution Time Target**: < 10 minutes

---

### P3: Database Migration Failed

**Definition**: New deployment includes schema changes, migration failed

**Detection**:
- Backend fails to start
- Log shows "migration failed" or "column not found"
- Error on `/api/health` endpoint

**Response Steps**:

1. **Immediate**:
   ```bash
   # Check migration status
   docker logs parchmark-backend | grep -i "migration\|alembic"

   # See the specific error
   docker logs parchmark-backend | tail -100
   ```

2. **Determine if Rollback Needed**:
   - If partial migration: Can't proceed forward safely
   - Must rollback to previous version

3. **Rollback Procedure**:
   ```bash
   # Get list of available image versions
   docker images | grep parchmark-backend

   # Stop current deployment
   docker compose -f docker-compose.prod.yml down

   # Rollback to previous version
   export PARCHMARK_VERSION=sha-abc123  # Previous working version
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d

   # Verify health
   sleep 30
   curl https://assets-api.engen.tech/api/health
   ```

4. **Fix Migration** (Parallel work):
   - Debug why migration failed
   - Usually data incompatibility issue
   - Fix code or data
   - Test migration on staging first

5. **Re-deploy After Fix**:
   ```bash
   # Test new code/migration on staging
   make test-all

   # Build new image
   docker build -f backend/Dockerfile -t parchmark-backend:sha-def456 .

   # Deploy again
   git push origin main  # Triggers CI/CD
   ```

**Resolution Time Target**: < 30 minutes

---

## Capacity Planning

### Metrics to Track for Growth

**Monthly Review**:
```bash
# Total users
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "SELECT COUNT(*) FROM users;"

# OIDC adoption rate
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "
  SELECT
    auth_provider,
    COUNT(*) as user_count,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as percentage
  FROM users
  GROUP BY auth_provider;
"

# Total notes
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "SELECT COUNT(*) FROM notes;"

# Database size
docker exec parchmark-backend psql -U parchmark_user -d parchmark_db -c "SELECT pg_size_pretty(pg_database_size('parchmark_db'));"
```

### Scaling Triggers

**When to Increase Resources**:

1. **Database**: If size > 50GB or queries > 100ms
   - Action: Add read replicas, optimize queries, or upgrade disk

2. **Backend**: If CPU > 70% or memory > 80% consistently
   - Action: Increase instance size or add replicas

3. **OIDC Provider**: If auth latency > 100ms
   - Action: Check Authelia health, add caching layer

4. **Connections**: If DB connections > 80% of pool
   - Action: Increase connection pool size or add application instances

---

## Backup & Recovery

### Daily Backup Procedure

**Frequency**: Every day at 2 AM

**Script** (`/path/to/scripts/backup-oidc-db.sh`):
```bash
#!/bin/bash
set -Eeuo pipefail

BACKUP_DIR="/backups/parchmark"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
docker exec parchmark-db pg_dump -U parchmark_user -d parchmark_db | \
  gzip > "$BACKUP_DIR/parchmark-db-$TIMESTAMP.sql.gz"

# Keep last 30 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/parchmark-db-$TIMESTAMP.sql.gz"
```

**Cron Entry**:
```
0 2 * * * /path/to/scripts/backup-oidc-db.sh >> /var/log/parchmark-backup.log 2>&1
```

### Restore from Backup

**If database corruption detected**:

```bash
# 1. Find backup to restore from
ls -la /backups/parchmark/*.sql.gz

# 2. Stop application
docker compose -f docker-compose.prod.yml down

# 3. Restore database
docker compose -f docker-compose.prod.yml up -d parchmark-db
sleep 10

# 4. Drop current database
docker exec parchmark-db psql -U parchmark_user -c "DROP DATABASE parchmark_db;"

# 5. Create new database
docker exec parchmark-db psql -U parchmark_user -c "CREATE DATABASE parchmark_db OWNER parchmark_user;"

# 6. Restore from backup
zcat /backups/parchmark/parchmark-db-20250108_020000.sql.gz | \
  docker exec -i parchmark-db psql -U parchmark_user -d parchmark_db

# 7. Start application
docker compose -f docker-compose.prod.yml up -d

# 8. Verify
sleep 30
curl https://assets-api.engen.tech/api/health
```

### OIDC Configuration Backup

**Backup Authelia configuration** (before any changes):

```bash
# Backup Authelia config
cp /etc/authelia/configuration.yml /backups/authelia-config-$(date +%Y%m%d_%H%M%S).yml

# Backup secrets (encrypted)
# Note: Store secrets in GitHub Secrets or Vault, not in files
```

---

## Maintenance Windows

### Routine Maintenance

**Monthly**: 1 hour, low-traffic window (suggested: 2 AM Sunday)

**Tasks**:
1. Update Docker images
2. Run security scans
3. Analyze database and reindex if needed
4. Review and clean up logs

**Procedure**:
```bash
# 1. Announce maintenance
# Post: "Scheduled maintenance: 2-3 AM Sunday, 30 min expected downtime"

# 2. Pull latest images
docker compose -f docker-compose.prod.yml pull

# 3. Stop services
docker compose -f docker-compose.prod.yml down

# 4. Database maintenance
docker exec parchmark-db psql -U parchmark_user -d parchmark_db -c "
  ANALYZE;
  REINDEX DATABASE parchmark_db;
  VACUUM ANALYZE;
"

# 5. Start services
docker compose -f docker-compose.prod.yml up -d

# 6. Wait and verify
sleep 30
curl https://assets-api.engen.tech/api/health

# 7. Post update: "Maintenance complete"
```

### OIDC Provider Updates

**When Authelia has updates** (check monthly):

```bash
# 1. Check for new version
docker pull authelia/authelia:latest

# 2. Read changelog
docker run --rm authelia/authelia:latest cat /CHANGELOG.md | head -50

# 3. Test in staging
docker compose -f docker-compose.dev.yml pull authelia
docker compose -f docker-compose.dev.yml up -d authelia

# 4. Run test suite
make test-oidc-integration

# 5. If all passes, update production
docker compose -f docker-compose.prod.yml up -d authelia
```

---

## Escalation Procedures

### Level 1: Local Team

**Handles**:
- Common issues (login loops, token refresh)
- Minor bugs (button not showing)
- User password resets

**Contact**: Slack #parchmark-support

**Response Time**: < 30 minutes

**Tools Available**:
- SSH access to production server
- Docker commands
- Database queries

---

### Level 2: OIDC Specialist

**Handles**:
- OIDC protocol issues
- Authelia integration problems
- Token validation errors

**Contact**: Slack @oidc-oncall or escalate Level 1

**Response Time**: < 1 hour

**Tools Available**:
- Full repository access
- Authelia configuration files
- OIDC client configuration

**Requires**:
- Understanding of OAuth 2.0 / OIDC
- Authelia administration experience
- JWT token debugging

---

### Level 3: Infrastructure Team

**Handles**:
- Database corruption
- Service failures
- Deployment issues
- Network problems

**Contact**: Escalate from Level 2

**Response Time**: < 2 hours

**Tools Available**:
- Full system access
- Ability to modify infrastructure
- Backup and recovery procedures

**Requires**:
- Kubernetes/Docker expertise
- PostgreSQL administration
- Infrastructure troubleshooting

---

### Escalation Path Decision Tree

```
Problem: User can't login

├─ Can local login? (test with testuser/testpass)
│  ├─ NO → Auth system down (P1 incident, call L3)
│  └─ YES → SSO-specific issue
│     ├─ Check: Is Authelia accessible?
│     │  ├─ NO → L2 escalation (provider down)
│     │  └─ YES → Check: Valid OIDC client?
│     │     ├─ NO → L2 escalation (config issue)
│     │     └─ YES → L1 can debug (token claims, user creation)

Problem: High error rates

├─ Check: Database healthy?
│  ├─ NO → L3 escalation (infrastructure)
│  └─ YES → Check: Application logs
│     ├─ Auth errors → L1
│     ├─ OIDC errors → L2
│     └─ Connection errors → L3

Problem: Performance degradation

├─ Check: CPU/Memory usage
│  ├─ > 80% → L3 escalation (scaling)
│  └─ Normal → Check: Response times
│     ├─ OIDC slow → L2 escalation
│     ├─ Database slow → L3 escalation
│     └─ Network slow → L3 escalation
```

---

## See Also

- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Detailed troubleshooting guide
- **AUTHELIA_OIDC_MONITORING.md** - Monitoring setup details
- **AUTHELIA_OIDC_SECURITY_HARDENING.md** - Security procedures
- **AUTHELIA_OIDC_DEPLOYMENT.md** - Deployment procedures
