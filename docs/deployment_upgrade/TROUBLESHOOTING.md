# Deployment Troubleshooting Guide

This document provides solutions for common deployment issues encountered with the ParchMark automated deployment system.

---

## SSH Connection Timeout

### Symptom
```
dial tcp ***:22: i/o timeout
Error: Process completed with exit code 1
```

### Cause
GitHub Actions runner cannot establish SSH connection to the production server. This can happen for several reasons:

1. **Firewall blocking GitHub Actions IPs**
2. **Incorrect PROD_HOST secret**
3. **Server SSH daemon not running**
4. **Network routing issues**

### Solutions

#### Solution 1: Allow GitHub Actions IP Ranges (Recommended)

GitHub Actions uses dynamic IP addresses from specific ranges. You need to allow these in your server firewall.

**Get GitHub's IP ranges:**
```bash
# Fetch GitHub's meta information
curl https://api.github.com/meta | jq -r '.actions[]'
```

**Configure firewall (example with ufw):**
```bash
# SSH into your server manually
ssh deploy@notes.engen.tech

# For each IP range from GitHub's meta API:
sudo ufw allow from 20.0.0.0/8 to any port 22 comment "GitHub Actions"
sudo ufw allow from 143.0.0.0/8 to any port 22 comment "GitHub Actions"
# ... add all ranges

# Or allow all GitHub Actions ranges at once (less secure but simpler):
# Download and apply GitHub's IP ranges
curl https://api.github.com/meta | jq -r '.actions[]' | while read range; do
  sudo ufw allow from "$range" to any port 22 comment "GitHub Actions"
done

# Reload firewall
sudo ufw reload

# Verify rules
sudo ufw status numbered
```

**Important Notes:**
- GitHub's IP ranges change periodically - check them monthly
- This approach works for cloud-hosted servers (DigitalOcean, AWS, etc.)
- If using Tailscale or other VPN, see Solution 3

#### Solution 2: Use Self-Hosted Runner

If you cannot modify firewall rules, use a GitHub Actions self-hosted runner on your network.

**Benefits:**
- No firewall changes needed
- Faster builds (no image pull delays)
- Direct access to your infrastructure

**Setup:**
1. Go to GitHub Repository → Settings → Actions → Runners
2. Click "New self-hosted runner"
3. Follow installation instructions for Linux
4. Place runner on same network as production server
5. Update workflow to use: `runs-on: self-hosted`

#### Solution 3: Use Tailscale for Secure Access

If your server uses Tailscale, configure GitHub Actions to connect via Tailscale.

**Setup:**
```yaml
# Add to deploy-to-production job, before SSH step
- name: Connect to Tailscale
  uses: tailscale/github-action@v2
  with:
    oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
    oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
    tags: tag:ci

- name: Deploy via SSH
  uses: appleboy/ssh-action@v1.2.2
  with:
    host: 100.x.y.z  # Tailscale IP from your tailnet
    # ... rest of config
```

**Required Secrets:**
- `TS_OAUTH_CLIENT_ID` - Tailscale OAuth client ID
- `TS_OAUTH_SECRET` - Tailscale OAuth secret

Generate these at: https://login.tailscale.com/admin/settings/oauth

#### Solution 4: Verify PROD_HOST Secret

Ensure the `PROD_HOST` secret contains the correct value.

**Check secret:**
1. Go to GitHub Repository → Settings → Secrets and variables → Actions
2. Find `PROD_HOST` in Repository secrets
3. Verify it matches your server's hostname or IP
   - Hostname: `notes.engen.tech`
   - OR Tailscale IP: `100.120.107.12`
   - OR Public IP if different

**Test from your machine:**
```bash
# Test connection using the same credentials
ssh -i ~/.ssh/parchmark_deploy deploy@notes.engen.tech

# If this works but GitHub Actions fails, it's a firewall issue
```

#### Solution 5: Temporary Workaround - Open SSH to All

**⚠️ ONLY USE FOR TESTING - NOT RECOMMENDED FOR PRODUCTION**

```bash
ssh deploy@notes.engen.tech
sudo ufw allow 22/tcp
sudo ufw reload
```

This allows SSH from anywhere. **REMOVE THIS RULE** after testing:
```bash
sudo ufw delete allow 22/tcp
sudo ufw allow from <your-ip> to any port 22  # Re-add your IP
```

### Verification

After applying a solution, trigger a manual deployment:

```bash
# From your local machine
make deploy-trigger

# Or via gh CLI directly
gh workflow run deploy.yml
```

Monitor the deployment:
```bash
make deploy-watch
```

If successful, you should see:
```
✅ Deployment to production completed successfully!
```

---

## Invalid Workflow Parameter: script_stop

### Symptom
```
Warning: Unexpected input(s) 'script_stop', valid inputs are [...]
```

### Cause
The `script_stop` parameter was removed from newer versions of `appleboy/ssh-action`.

### Solution
**Fixed in latest workflow** - The parameter has been removed and replaced with:
- `command_timeout: 30m` - Prevents hanging on long operations
- `set -Eeuo pipefail` - Built into script for fail-fast behavior

If you see this warning, ensure you're using the latest workflow:
```bash
git pull origin main
```

---

## Test Job Failing: eslint: not found

### Symptom
```
sh: 1: eslint: not found
make: *** [makefiles/ui.mk:12: test-ui-lint] Error 127
```

### Cause
Dependencies not installed before running tests in the test job.

### Solution
**Fixed in latest workflow** - Added `make install-all` step before running tests.

Ensure your workflow includes:
```yaml
- name: Install dependencies
  run: make install-all

- name: Run all tests
  run: make test-all
```

---

## Migration Failures

### Symptom
```
❌ Deployment failed at line XXX
Migration script exited with error
```

### Cause
Database migration script failed. Possible reasons:
- Invalid SQL syntax
- Schema conflicts
- Permission issues
- Database connection problems

### Solution

**1. Test migrations locally first:**
```bash
# Start local PostgreSQL
make docker-dev

# Run backend with migrations
cd backend
uv run alembic upgrade head  # Or your migration command
```

**2. Check migration script:**
```bash
# Review the migration file
cat backend/scripts/migrate.sh

# Ensure it's executable
chmod +x backend/scripts/migrate.sh
```

**3. Test migration on production (manual):**
```bash
# SSH into production
make deploy-ssh

# Navigate to app directory
cd /home/deploy/parchmark

# Run migration manually
docker compose -f docker-compose.prod.yml exec -T backend bash /app/scripts/migrate.sh

# Check for errors in output
```

**4. Common fixes:**
- Add `IF NOT EXISTS` clauses to CREATE statements
- Add `IF EXISTS` clauses to DROP statements
- Check for typos in column/table names
- Verify database user has CREATE/ALTER permissions

**5. Rollback if needed:**
If migration applied partially and deployment failed:
```bash
# Find the last good SHA
make deploy-list-images

# Rollback
make deploy-rollback SHA=abc123
```

---

## Health Check Failures

### Symptom
```
❌ Backend health check failed after retries!
```

### Cause
Service failed to start properly or health endpoint not responding.

### Solutions

**1. Check container logs:**
```bash
make deploy-logs-backend
# or
make deploy-logs-frontend
```

**2. Verify health endpoint manually:**
```bash
# Backend
curl https://assets-api.engen.tech/api/health

# Frontend
curl https://notes.engen.tech/
```

**3. Check container status:**
```bash
make deploy-ps
```

**4. Increase start_period if services need more time:**
Edit `docker-compose.prod.yml`:
```yaml
healthcheck:
  start_period: 60s  # Increase from 30s if needed
```

**5. Check database connection:**
```bash
make deploy-ssh

# Test database connectivity
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.database.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK')
"
```

---

## Image Pull Failures

### Symptom
```
Error response from daemon: pull access denied for ghcr.io/tejgandham/parchmark-backend
```

### Cause
GHCR authentication failed or token expired.

### Solutions

**1. Verify GHCR_PULL_TOKEN:**
- Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Check token hasn't expired (90-day limit)
- Verify token has `read:packages` scope

**2. Regenerate token if expired:**
- Create new classic PAT with `read:packages` scope
- Update GitHub Secret `GHCR_PULL_TOKEN` with new value
- Retry deployment

**3. Test token manually:**
```bash
# On production server
echo "YOUR_TOKEN" | docker login ghcr.io -u tejgandham --password-stdin
docker pull ghcr.io/tejgandham/parchmark-backend:latest
```

---

## Disk Space Issues

### Symptom
```
no space left on device
```

### Solution

**Check disk usage:**
```bash
make deploy-disk-usage
```

**Clean up old images:**
```bash
make deploy-ssh

# Remove old images (older than 7 days)
docker image prune -a --filter "until=168h"

# Remove unused volumes
docker volume prune

# Remove build cache
docker builder prune -a
```

---

## Additional Resources

- **Deployment Guide**: `docs/deployment_upgrade/DEPLOYMENT_VALIDATED.md`
- **Progress Tracker**: `docs/deployment_upgrade/DEPLOYMENT_PROGRESS.md`
- **GitHub Secrets Setup**: `docs/deployment_upgrade/PHASE4_GITHUB_SECRETS.md`
- **Server Setup**: `docs/deployment_upgrade/PHASE3_SERVER_SETUP.md`
- **Makefile Commands**: Run `make deploy-help` for complete guide

---

**Last Updated**: 2025-10-26
