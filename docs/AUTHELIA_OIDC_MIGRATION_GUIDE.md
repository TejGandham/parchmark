# OIDC Migration Guide

Guide for migrating existing ParchMark users from local-only authentication to hybrid (local + OIDC) authentication.

---

## Overview

This guide helps:
- Transition existing local users to hybrid authentication
- Maintain backward compatibility
- Minimize user disruption
- Handle edge cases
- Validate migration success

---

## Pre-Migration Checklist

### Planning Phase

- [ ] **Backup Database**
  ```bash
  # Create backup before any changes
  pg_dump -U parchmark_user parchmark_db > backup_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Notify Users**
  - Email notification about new SSO option
  - Documentation links
  - FAQ for common questions
  - Support contact information

- [ ] **Staging Environment Testing**
  ```bash
  # Test migration on staging first
  1. Deploy hybrid auth code
  2. Run migration scripts
  3. Test with sample users
  4. Validate data integrity
  5. Test OIDC and local login both work
  ```

- [ ] **Communication Plan**
  - Timeline for rollout
  - Any expected downtime
  - Support escalation process
  - Rollback plan if issues

### Technical Requirements

- [ ] All services running and healthy
- [ ] Database backups created
- [ ] OIDC provider (Authelia) accessible
- [ ] Network connectivity verified
- [ ] Rollback procedure documented

---

## Migration Scenarios

### Scenario 1: Hybrid Mode (Local + OIDC Together)

**Best For**: Organizations wanting both auth methods permanently

**Steps**:

1. **Deploy hybrid auth code**
   ```bash
   git checkout authelia_support
   git merge main
   ```

2. **Update environment**
   ```bash
   AUTH_MODE=hybrid          # Enable both methods
   OIDC_ISSUER_URL=...      # Set OIDC provider
   OIDC_AUDIENCE=...        # Set client ID
   ```

3. **No database migration needed**
   - Existing local users keep working
   - New OIDC users auto-created on first login
   - Both coexist in same database

4. **Testing**
   ```bash
   # Test local user login
   - Username: existing_user
   - Password: (unchanged)

   # Test OIDC user login
   - Click "Sign In with SSO"
   - Use Authelia credentials

   # Verify both work
   make test-backend-oidc
   make test-ui-oidc
   ```

5. **Gradual User Migration**
   - Users can continue with local login
   - SSO available as alternative
   - No forced migration
   - Users migrate at their own pace

---

### Scenario 2: Full OIDC Migration (Local → OIDC Only)

**Best For**: Organizations moving fully to centralized auth

**Steps**:

1. **Phase 1: Deploy in Hybrid Mode (Week 1)**
   ```bash
   # Users can use either method
   AUTH_MODE=hybrid
   # Let users get familiar with SSO
   ```

2. **Phase 2: Announce Transition (Week 2)**
   - Email users about transition
   - Provide migration instructions
   - Set transition date (e.g., Week 4)
   - Offer support sessions

3. **Phase 3: Data Preparation (Week 3)**
   ```bash
   # Link local users to OIDC accounts

   # Option A: Email-based matching
   # If user email matches OIDC email, link account
   UPDATE users
   SET oidc_sub = (
      SELECT preferred_username FROM oidc_users
      WHERE email = users.email
   ),
   auth_provider = 'oidc'
   WHERE email IS NOT NULL;

   # Option B: Manual linking
   # Admin provides mapping file
   # Users manually link accounts

   # Option C: Username-based
   # Use existing username as OIDC username
   # Verify with users beforehand
   ```

4. **Phase 4: Cutover (Week 4)**
   ```bash
   # Switch to OIDC-only
   AUTH_MODE=oidc

   # Local login endpoint still works (for backwards compatibility)
   # but /api/auth/login returns 403 Forbidden
   ```

5. **Phase 5: Cleanup (Week 5)**
   ```bash
   # After successful transition
   # Keep backups for 30+ days
   # Monitor for any issues

   # Optional: Remove password_hash values
   UPDATE users SET password_hash = NULL WHERE auth_provider = 'oidc';
   ```

---

### Scenario 3: User Account Linking

**Best For**: Users who want to keep both local and OIDC access

**Implementation**:

```sql
-- Add linking support to users table
ALTER TABLE users ADD COLUMN linked_to_user_id INTEGER;
ALTER TABLE users ADD CONSTRAINT fk_linked_user
  FOREIGN KEY (linked_to_user_id) REFERENCES users(id);

-- Link accounts
UPDATE users u1
SET linked_to_user_id = u2.id
WHERE u1.auth_provider = 'local'
  AND u2.auth_provider = 'oidc'
  AND u1.email = u2.email;

-- Query linked accounts
SELECT u1.username as local_user, u2.username as oidc_user
FROM users u1
JOIN users u2 ON u1.id = u2.linked_to_user_id;
```

---

## Data Migration Strategies

### Strategy 1: Email-Based Matching (Recommended)

**Assumptions**:
- Email addresses in local accounts are accurate
- OIDC provider has same email addresses
- Email is unique identifier

**Process**:
```sql
-- Check for matches
SELECT COUNT(*) FROM users u1
WHERE u1.auth_provider = 'local'
  AND EXISTS (
    SELECT 1 FROM oidc_provider
    WHERE email = u1.email
  );

-- Link matching users
UPDATE users u1
SET oidc_sub = (
  SELECT oidc_id FROM oidc_provider WHERE email = u1.email
),
auth_provider = 'hybrid'  -- Both methods
WHERE u1.auth_provider = 'local'
  AND u1.email IN (SELECT email FROM oidc_provider);

-- Check for unmatched users
SELECT username, email FROM users u1
WHERE u1.auth_provider = 'local'
  AND NOT EXISTS (
    SELECT 1 FROM oidc_provider WHERE email = u1.email
  );
```

**Advantages**:
- Automated
- No manual intervention
- Preserves existing logins

**Disadvantages**:
- Requires accurate emails
- May not match if email changed
- No consent from users

---

### Strategy 2: Username-Based Matching

**Assumptions**:
- OIDC usernames match local usernames
- Or can be mapped programmatically

**Process**:
```sql
-- Create mapping if needed
CREATE TEMP TABLE username_mapping (
  local_username VARCHAR,
  oidc_username VARCHAR
);

-- Insert mappings (from CSV or admin input)
COPY username_mapping FROM STDIN;

-- Apply mappings
UPDATE users u
SET oidc_sub = um.oidc_username,
    auth_provider = 'hybrid'
FROM username_mapping um
WHERE u.username = um.local_username;
```

---

### Strategy 3: Manual User-Initiated Linking

**Process**:
```typescript
// Frontend: Account linking UI
<AccountLinking>
  <p>Link your account to SSO</p>
  <Button onClick={handleLinkAccount}>
    Link to OIDC Account
  </Button>

  // Verification flow:
  // 1. User clicks "Link Account"
  // 2. System sends verification email
  // 3. User confirms email
  // 4. Account linked to OIDC identity
</AccountLinking>
```

**Advantages**:
- User consent obtained
- Transparent process
- No data assumptions

**Disadvantages**:
- Slow (users must take action)
- Some users may not complete
- Requires additional UI

---

## Gradual Rollout Strategy

### Phase-Based Rollout

**Week 1: Small Group Testing**
```bash
# Deploy to 5-10 power users
# Get feedback
# Fix issues
# Document learnings
```

**Week 2: Department Testing**
```bash
# Deploy to one department
# Monitor for issues
# Provide training
# Gather feedback
```

**Week 3: Company-Wide**
```bash
# Deploy to all users
# Support team ready
# Monitor closely
# Be prepared to rollback
```

**Monitoring During Rollout**:
```bash
# Check error rates
docker logs parchmark-backend | grep -i "oidc\|error" | tail -100

# Check login attempts
SELECT auth_provider, COUNT(*) FROM login_events
GROUP BY auth_provider;

# Check success rates
SELECT auth_provider, success_count, fail_count,
  (success_count::float / (success_count + fail_count)) * 100 as success_rate
FROM login_stats;
```

---

## Validation Steps

### Pre-Migration Validation

```bash
# 1. Database integrity
psql -U parchmark_user -d parchmark_db -c "
  SELECT COUNT(*) as total_users FROM users;
  SELECT auth_provider, COUNT(*) FROM users GROUP BY auth_provider;
"

# 2. Test both auth methods
make test-backend-oidc
make test-ui-oidc

# 3. Verify API health
curl -s http://localhost:8000/api/health | jq .

# 4. Check OIDC provider
curl -s http://localhost:9091/.well-known/openid-configuration | jq '.issuer'

# 5. Load test
ab -n 100 -c 10 http://localhost:8000/api/health
```

### Post-Migration Validation

```bash
# 1. Verify data integrity
SELECT COUNT(*) FROM users WHERE auth_provider NOT IN ('local', 'oidc');

# 2. Check for orphaned records
SELECT u.id FROM users u
WHERE u.auth_provider = 'oidc'
  AND u.oidc_sub IS NULL;

# 3. Test user access
# For each user:
# - Local user: Can still login with password
# - OIDC user: Can login via SSO
# - Linked user: Can login with both methods

# 4. Verify note access
SELECT u.id, u.username, COUNT(n.id) as note_count
FROM users u
LEFT JOIN notes n ON u.id = n.user_id
GROUP BY u.id;

# 5. Test token refresh
# Login and verify token can be refreshed

# 6. Performance check
# Measure login time
# Measure API response time
# Compare before/after
```

---

## Rollback Procedure

### If Issues Occur During Migration

**Immediate Actions** (< 1 minute):

```bash
# 1. Set AUTH_MODE back to local
# In docker-compose.yml or env
AUTH_MODE=local

# 2. Restart backend
docker restart parchmark-backend

# 3. Verify local login works
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

**Restore from Backup** (if data corruption):

```bash
# 1. Stop all services
docker-compose down

# 2. Drop current database
psql -U parchmark_user -c "DROP DATABASE parchmark_db;"

# 3. Restore from backup
psql -U parchmark_user < backup_20250108_120000.sql

# 4. Restart services
docker-compose up -d

# 5. Verify
curl http://localhost:8000/api/health
```

**Document Findings**:
- What went wrong
- When it was detected
- How it was resolved
- Prevention for future

---

## Communication Templates

### Pre-Migration Email

```
Subject: New Single Sign-On (SSO) Now Available

Hi [User],

We're excited to announce that ParchMark now supports Single Sign-On (SSO)
via Authelia! You can now login with your SSO credentials in addition to
your existing username and password.

What's changing:
- New "Sign In with SSO" button on the login page
- Your existing login still works
- No action required - both methods work together

How to try SSO:
1. Go to https://notes.engen.tech/login
2. Click "Sign In with SSO"
3. Login with your SSO credentials
4. All your existing notes and data are available

FAQ:
Q: Do I have to use SSO?
A: No, your existing login still works.

Q: Will I have to change my password?
A: No, nothing changes unless you want it to.

Q: What if something breaks?
A: Contact support@example.com

Learn more: [link to AUTHELIA_OIDC_QUICKSTART.md]

Best regards,
The ParchMark Team
```

### Migration Announcement Email

```
Subject: Important: SSO Login Migration on [Date]

Hi [User],

On [Date], we're migrating to Single Sign-On (SSO) as our primary
authentication method. Here's what you need to know:

Timeline:
- [Date 1]: SSO available alongside traditional login
- [Date 2]: SSO becomes primary method
- [Date 3]: Traditional login disabled (keep password for recovery)

What to do:
1. Login with SSO at least once before [Date 2]
2. Verify you can access all your notes
3. Save your password somewhere safe

Your login options:
- SSO login: Recommended
- Local login: Still available until [Date 3]
- Password recovery: Available anytime

Questions?
- FAQ: [link]
- Support: support@example.com
- Training: [Zoom link]

Thank you,
The ParchMark Team
```

---

## Common Issues & Solutions

### Issue 1: Email Mismatch

**Problem**: Local user email doesn't match OIDC email

**Solution**:
```sql
-- Find mismatches
SELECT u.username, u.email as local_email
FROM users u
WHERE u.auth_provider = 'local'
  AND u.email NOT IN (SELECT email FROM oidc_provider)
  AND u.email IS NOT NULL;

-- Options:
-- A) Update local user email to match OIDC
UPDATE users SET email = 'new@example.com' WHERE username = 'john';

-- B) Update OIDC email to match local (if possible in Authelia)
-- C) Create new OIDC account with local email
-- D) Manual linking by admin
```

### Issue 2: Duplicate Users

**Problem**: Same person has both local and OIDC account

**Solution**:
```sql
-- Find duplicates
SELECT COUNT(*), email FROM users
GROUP BY email HAVING COUNT(*) > 1;

-- Verify it's the same person (manual step)
-- Then merge:

-- Option 1: Keep local, remove OIDC
DELETE FROM users WHERE id = [oidc_user_id];

-- Option 2: Keep OIDC, remove local
DELETE FROM users WHERE id = [local_user_id];
REATTACH notes to remaining user:
UPDATE notes SET user_id = [kept_user_id]
WHERE user_id = [deleted_user_id];
```

### Issue 3: User Can't Login via OIDC

**Problem**: User exists in Authelia but ParchMark doesn't recognize

**Solution**:
```bash
# Check if user exists in Authelia
curl http://localhost:9091/userinfo -H "Authorization: Bearer [token]"

# Check if user was auto-created
psql -U parchmark_user -d parchmark_db -c \
  "SELECT * FROM users WHERE auth_provider='oidc' AND email='user@example.com';"

# If not created, manually create
docker exec parchmark-backend python -c "
from app.models import User
from app.database import SessionLocal

db = SessionLocal()
user = User(
    username='user@example.com',
    email='user@example.com',
    auth_provider='oidc',
    oidc_sub='user',
    password_hash=None
)
db.add(user)
db.commit()
"
```

---

## Post-Migration Optimization

### Cleanup Operations

```bash
# 1. Analyze query performance
ANALYZE;

# 2. Reindex tables
REINDEX TABLE users;

# 3. Vacuum to reclaim space
VACUUM ANALYZE;

# 4. Check for unused indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0;  # Unused indexes
```

### Decommission Old Resources

```bash
# After successful migration:

# 1. Archive backups
# Keep for 30+ days, then archive

# 2. Remove temporary tables/migrations
DROP TABLE IF EXISTS user_migration_log;

# 3. Update documentation
# Remove migration steps
# Update troubleshooting

# 4. Monitor long-term
# Continue checking for issues
# Weekly health check for 1 month
```

---

## Success Criteria

### Operational Success

- ✓ Zero authentication failures during migration
- ✓ All users can login (local or OIDC)
- ✓ No data loss or corruption
- ✓ Performance maintained (response time < 100ms)
- ✓ Support team has zero escalations

### User Success

- ✓ 80%+ of users have tried SSO
- ✓ User satisfaction score > 4/5
- ✓ No complaints about authentication
- ✓ Support tickets < 5

### Technical Success

- ✓ All tests passing
- ✓ Monitoring alerts at baseline
- ✓ No performance degradation
- ✓ Database integrity verified
- ✓ Rollback plan not needed

---

## See Also

- **AUTHELIA_OIDC_QUICKSTART.md** - New user getting started
- **AUTHELIA_OIDC_TROUBLESHOOTING.md** - Problem diagnosis
- **AUTHELIA_OIDC_DEPLOYMENT.md** - Deployment procedures
