# Authelia OIDC Disaster Recovery & Business Continuity Guide

Comprehensive disaster recovery and business continuity procedures for ParchMark with Authelia OIDC.

---

## Table of Contents

1. [Overview](#overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Failure Scenarios](#failure-scenarios)
4. [Data Backup Strategy](#data-backup-strategy)
5. [Recovery Procedures](#recovery-procedures)
6. [Failover & High Availability](#failover--high-availability)
7. [Business Continuity Plan](#business-continuity-plan)
8. [Testing & Validation](#testing--validation)

---

## Overview

### Recovery Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ ParchMark Architecture with DR Components                   │
└─────────────────────────────────────────────────────────────┘

Primary Region:
├─ Frontend (2 instances)
├─ Backend (2 instances)
├─ PostgreSQL (Master + Replica)
├─ Authelia (2 instances)
└─ Redis Cache

DR Region (Standby):
├─ PostgreSQL Read Replica (cross-region)
├─ Secrets backup (encrypted)
└─ Application images (pre-built)

Backups:
├─ Database backups (daily + hourly)
├─ Configuration backups
├─ Secrets backup
└─ Application state snapshots
```

---

## Recovery Objectives

### Target Recovery Time (RTO) and Recovery Point Objective (RPO)

| Scenario | RTO | RPO | Priority |
|----------|-----|-----|----------|
| Database corruption | 1 hour | 1 hour | P1 |
| Data loss | 2 hours | 4 hours | P1 |
| Authelia provider down | 30 minutes | N/A | P2 |
| Single backend failure | 5 minutes | N/A | P2 |
| Regional outage | 4 hours | 1 hour | P3 |
| Complete data loss | 24 hours | 24 hours | P3 |

### Availability Targets

- **Uptime SLA**: 99.5% (max 3.6 hours downtime/month)
- **Planned maintenance**: 1 hour/month (scheduled 2 AM Sunday)
- **Unplanned outage**: < 1 hour/month average
- **Auth system availability**: 99.9% (max 43 minutes/month)

---

## Failure Scenarios

### Scenario 1: Database Corruption

**Detection**:
```bash
# Check database integrity
docker exec parchmark-db psql -U parchmark_user -d parchmark_db -c "
  SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';
"

# Verify no errors
docker logs parchmark-backend | grep -i "database error"
```

**Recovery Steps**:

1. **Immediate (< 5 min)**:
   ```bash
   # Stop application
   docker compose -f docker-compose.prod.yml down

   # Create copy of corrupted database for forensics
   docker exec parchmark-db pg_dump -U parchmark_user -d parchmark_db \
     -f /backups/corrupted-$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Identify Latest Good Backup (< 10 min)**:
   ```bash
   # List available backups
   ls -lh /backups/parchmark-db-*.sql.gz | tail -10

   # Verify backup integrity
   gunzip -t /backups/parchmark-db-20250108_020000.sql.gz
   ```

3. **Restore Database (10-30 min)**:
   ```bash
   # 1. Start fresh PostgreSQL
   docker compose -f docker-compose.prod.yml up -d parchmark-db
   sleep 30

   # 2. Drop corrupted database
   docker exec parchmark-db psql -U parchmark_user -c "
     DROP DATABASE parchmark_db;
   "

   # 3. Create new database
   docker exec parchmark-db psql -U parchmark_user -c "
     CREATE DATABASE parchmark_db OWNER parchmark_user;
   "

   # 4. Restore from backup
   zcat /backups/parchmark-db-20250108_020000.sql.gz | \
     docker exec -i parchmark-db psql -U parchmark_user -d parchmark_db

   # 5. Verify restore
   docker exec parchmark-db psql -U parchmark_user -d parchmark_db -c "
     SELECT COUNT(*) as user_count FROM users;
   "
   ```

4. **Restart Application (5 min)**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d

   # Verify health
   sleep 30
   curl https://assets-api.engen.tech/api/health
   ```

5. **Communication & Investigation**:
   - Post incident report
   - Investigate root cause (disk failure? corruption? bug?)
   - Implement fix if needed

**Total Recovery Time**: 15-45 minutes

---

### Scenario 2: Authelia Provider Down

**Detection**:
```bash
# OIDC logins start failing
docker logs parchmark-backend --since 10m | grep -i "provider.*error"

# No response from provider
curl -v https://auth.engen.tech/.well-known/openid-configuration
```

**Recovery Steps**:

1. **Immediate (< 2 min)**:
   ```bash
   # Check Authelia status
   docker ps | grep authelia
   docker logs authelia | tail -50
   ```

2. **Restart Authelia (< 5 min)**:
   ```bash
   # If container is running but unresponsive
   docker restart authelia

   # Wait for healthy
   sleep 20

   # Verify
   curl -s https://auth.engen.tech/.well-known/openid-configuration | jq '.issuer'
   ```

3. **If Database Issue**:
   ```bash
   # Check Authelia database connectivity
   docker logs authelia | grep -i "database"

   # Restart Authelia database if separate
   docker restart authelia-db

   # Wait and restart Authelia
   sleep 10
   docker restart authelia
   ```

4. **User Communication**:
   - Post: "SSO temporarily unavailable, use local login"
   - Estimated recovery: 10 minutes
   - No action needed from users

5. **Investigation**:
   ```bash
   # Check resource usage (if slow)
   docker stats authelia

   # Check recent errors
   docker logs authelia --since 1h | grep -i error
   ```

**During Outage**:
- ✓ Local login still works
- ✓ Users can access existing notes
- ✗ New OIDC logins blocked
- ✓ Existing OIDC sessions continue (tokens still valid)

**Total Recovery Time**: 5-10 minutes

---

### Scenario 3: Secrets Compromised

**Detection**:
- Accidental commit to GitHub
- Container image leaked with embedded secret
- Unauthorized access detected

**Immediate Actions (< 5 min)**:

```bash
# 1. Rotate all secrets immediately
# Update these in Secrets Manager/Vault:
- SECRET_KEY (application)
- OIDC_CLIENT_SECRET (Authelia)
- DB_PASSWORD (PostgreSQL)
- AUTHELIA_JWT_SECRET
- JWT_REFRESH_SECRET

# 2. Revoke old secrets (if applicable)
# For Authelia: Update client secret in configuration
# For DB: Update password and restart

# 3. Audit access logs
docker logs parchmark-backend | grep -i "unauthorized\|invalid" | head -50
```

**Recovery Procedure (30 min)**:

```bash
# 1. Create new secrets
export NEW_SECRET_KEY=$(openssl rand -base64 32)
export NEW_DB_PASSWORD=$(openssl rand -base64 32)
export NEW_OIDC_SECRET=$(openssl rand -base64 32)

# 2. Update .env files and secrets manager
# (Don't commit to Git!)

# 3. Update database password
docker exec parchmark-db psql -U parchmark_user -c \
  "ALTER ROLE parchmark_user PASSWORD '$NEW_DB_PASSWORD';"

# 4. Update Authelia configuration
# Edit authelia/configuration.yml with new OIDC_CLIENT_SECRET
# Restart Authelia
docker restart authelia

# 5. Update backend
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# 6. Verify everything works
sleep 30
curl https://assets-api.engen.tech/api/health
```

**Post-Incident**:
- [ ] Revoke old secrets from Secrets Manager
- [ ] Update API keys in all external integrations
- [ ] Rotate SSH keys for server access
- [ ] Check git history for accidental commits
- [ ] Update disaster recovery secrets with new values
- [ ] Brief security team on incident
- [ ] Document findings and improvements

**Total Recovery Time**: 30-60 minutes

---

## Data Backup Strategy

### Backup Types & Frequency

| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| Database full | Daily | 30 days | /backups, AWS S3 |
| Database incremental | Hourly | 7 days | /backups |
| Configuration | Daily | 90 days | AWS S3 encrypted |
| Secrets | Before changes | 90 days | AWS Secrets Manager |
| Application state | Weekly | 12 weeks | AWS S3 |
| OIDC config | Before changes | 1 year | GitHub (encrypted) |

### Database Backup Script

**File: `/scripts/backup-database.sh`**:

```bash
#!/bin/bash
set -Eeuo pipefail

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/parchmark-db-$TIMESTAMP.sql.gz"
S3_BUCKET="s3://parchmark-backups"
LOG_FILE="/var/log/parchmark-backup.log"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup
log "Starting database backup..."
docker exec parchmark-db pg_dump \
  -U parchmark_user \
  -d parchmark_db \
  --verbose \
  | gzip > "$BACKUP_FILE"

if [ $? -ne 0 ]; then
  log "ERROR: Backup failed"
  exit 1
fi

log "Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Verify backup integrity
log "Verifying backup..."
gunzip -t "$BACKUP_FILE" || {
  log "ERROR: Backup corrupted"
  exit 1
}

# Upload to S3
log "Uploading to S3..."
aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/$(basename "$BACKUP_FILE")" \
  --sse AES256 \
  --storage-class GLACIER || {
  log "ERROR: S3 upload failed"
  exit 1
}

# Cleanup old backups (keep 30 days)
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "parchmark-db-*.sql.gz" -mtime +30 -delete

log "Backup completed successfully"
```

**Cron Job**:
```bash
# Daily backup at 2 AM
0 2 * * * /scripts/backup-database.sh >> /var/log/backup-cron.log 2>&1

# Hourly incremental (optional, for highly critical data)
0 * * * * /scripts/backup-database-incremental.sh >> /var/log/backup-cron.log 2>&1
```

### Backup Verification

```bash
# Weekly backup test restore (every Monday 3 AM)
0 3 * * 1 /scripts/test-backup-restore.sh

# Script: test-backup-restore.sh
#!/bin/bash
# 1. Create temporary database
# 2. Restore latest backup
# 3. Run sanity checks
# 4. Report results
# 5. Cleanup
```

---

## Recovery Procedures

### Step-by-Step Recovery Runbook

#### Level 1: Service Restart (5 min)

**For**:
- Unresponsive service
- Memory leak
- Hung connections

**Procedure**:
```bash
# Restart single service
docker restart parchmark-backend

# Or full stack restart
docker compose -f docker-compose.prod.yml restart

# Verify
curl https://assets-api.engen.tech/api/health
```

#### Level 2: Configuration Recovery (15 min)

**For**:
- Wrong environment variables
- Configuration corruption
- Secrets out of sync

**Procedure**:
```bash
# 1. Check current config
docker exec parchmark-backend printenv | grep -i oidc

# 2. Restore from backup
git show HEAD~1:docker-compose.prod.yml > docker-compose.backup.yml

# 3. Compare and update
diff docker-compose.prod.yml docker-compose.backup.yml

# 4. Restart with corrected config
docker compose -f docker-compose.prod.yml restart
```

#### Level 3: Data Recovery (1-2 hours)

**For**:
- Database corruption
- Data loss
- Accidental deletion

**Procedure**:
(See Scenario 1 above)

#### Level 4: Infrastructure Rebuild (4-8 hours)

**For**:
- Hardware failure
- Complete data loss
- Regional disaster

**Procedure**:
1. Provision new infrastructure
2. Deploy application images
3. Restore database from backup
4. Restore configuration
5. Restore secrets
6. Run smoke tests

---

## Failover & High Availability

### Active-Active Database Replication

**PostgreSQL Streaming Replication**:

```bash
# Primary configuration (postgresql.conf)
wal_level = replica
max_wal_senders = 10
wal_keep_size = '1GB'

# Standby configuration
standby_mode = 'on'
primary_conninfo = 'host=primary-db port=5432 user=replicator password=repl_password'
```

### Automatic Failover with Patroni

**Patroni Configuration**:

```yaml
scope: parchmark-db
namespace: /parchmark

postgresql:
  data_dir: /var/lib/postgresql/data
  bin_dir: /usr/lib/postgresql/15/bin
  parameters:
    wal_level: replica
    max_wal_senders: 10

etcd:
  hosts: ['etcd-1:2379', 'etcd-2:2379', 'etcd-3:2379']

restapi:
  listen: '0.0.0.0:8008'
```

**Automatic Failover Workflow**:
```
1. Primary DB fails → Heartbeat missed
2. Etcd detects failure → Leader election
3. Standby promoted → Becomes new primary
4. DNS updated → Via Route53 health check
5. Backend connections → Auto-reconnect to new primary
```

### Application-Level Failover

```python
# Multiple connection strings
DATABASE_URLS = [
    "postgresql://user:pass@primary-db:5432/parchmark_db",
    "postgresql://user:pass@standby-db:5432/parchmark_db",
]

# Connection pool with failover
engine = create_engine(
    f"postgresql+psycopg2://{DATABASE_URLS[0]}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle stale connections
    echo_pool=False
)
```

---

## Business Continuity Plan

### Runbook for Common Scenarios

#### Scenario A: We Lost the Primary Database

1. **Immediate**: Promote read replica
2. **Verify**: Run data integrity checks
3. **Notify**: Send incident notice
4. **Monitor**: Watch for replication lag
5. **Fix**: Rebuild failed primary
6. **Restore**: Rebuild replication

**Expected Downtime**: < 5 minutes

#### Scenario B: Entire Datacenter Lost

1. **Activate DR**: Start services in standby region
2. **DNS Failover**: Update Route53 records
3. **Restore Data**: From cross-region backup
4. **Verify**: Run smoke tests
5. **Notify**: Update status page

**Expected Downtime**: 1-2 hours

#### Scenario C: Secrets Compromised

1. **Rotate**: Update all secrets
2. **Redeploy**: Rebuild containers with new secrets
3. **Audit**: Check for unauthorized access
4. **Communicate**: Notify users if needed

**Expected Downtime**: 30-60 minutes

### Critical Contacts

```yaml
on_call:
  primary: +1-555-0100
  backup: +1-555-0101

escalation:
  level1: team-oncall@company.com
  level2: team-lead@company.com
  level3: cto@company.com

external:
  aws_support: support@aws.amazon.com
  authelia_support: support@authelia.com
  database_vendor: support@postgresql.org
```

### Communication Template

**Incident Started**:
```
Subject: [INCIDENT] ParchMark Service Degradation

An incident affecting ParchMark has been detected.
Status: Investigating
Estimated Impact: OIDC login temporarily unavailable
ETA for Resolution: 30 minutes

Users CAN: Use local login to access existing notes
Users CANNOT: Create new OIDC accounts

We will update this every 15 minutes.
```

**Resolution**:
```
Subject: [RESOLVED] ParchMark Service Restored

The incident has been resolved.
Duration: 45 minutes
Root Cause: Authelia database connection pool exhausted
Resolution: Restarted Authelia services
Preventive Action: Increasing connection pool limits

Thank you for your patience.
```

---

## Testing & Validation

### Disaster Recovery Drill Schedule

| Drill | Frequency | Participants | Duration |
|-------|-----------|--------------|----------|
| Backup restore | Monthly | Ops team | 30 min |
| Failover | Quarterly | Ops + Dev | 1 hour |
| Full DR | Semi-annually | All teams | 2-4 hours |
| Incident simulation | Quarterly | Full team | 1-2 hours |

### Backup Restore Test Checklist

```bash
# Monthly test (1st Monday 10 AM)
- [ ] Restore latest daily backup to test database
- [ ] Verify user count matches production
- [ ] Verify note count matches production
- [ ] Test local login works
- [ ] Test backend health check
- [ ] Verify OIDC configuration
- [ ] Generate test report
- [ ] Document any issues
- [ ] Share results with team
```

### Failover Drill Checklist

```bash
# Quarterly test (every 3 months)
- [ ] Stop primary database
- [ ] Verify automatic promotion
- [ ] Update DNS records
- [ ] Test backend connectivity
- [ ] Verify no data loss
- [ ] Check application logs for errors
- [ ] Document recovery time
- [ ] Share lessons learned
```

---

## See Also

- **AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md** - Daily operations
- **AUTHELIA_OIDC_MONITORING_OBSERVABILITY.md** - Monitoring setup
- **AUTHELIA_OIDC_BACKUP_RETENTION_POLICY.md** - Detailed backup policy (future)
