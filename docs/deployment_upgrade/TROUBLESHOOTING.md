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
  uses: tailscale/github-action@v4
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

**Create Tailscale OAuth Client:**

1. Go to https://login.tailscale.com/admin/settings/oauth
2. Click "Generate OAuth client"
3. Add a description (e.g., "GitHub Actions CI/CD")
4. **Configure permissions** - You only need ONE scope:
   - Under "**Devices**" section, check "**Write**"
   - Leave all other scopes (DNS, Policy File, Users, etc.) unchecked
5. **Add tags**: Enter `tag:ci` (or your preferred tag for CI nodes)
6. Click "Generate client"
7. Copy the **Client ID** and **Client secret** immediately (secret only shown once)

**Add GitHub Secrets:**
1. Go to: GitHub Repository → Settings → Secrets and variables → Actions
2. Add new repository secrets:
   - `TS_OAUTH_CLIENT_ID` = Your OAuth client ID
   - `TS_OAUTH_SECRET` = Your OAuth client secret
   - `PROD_HOST` = Your server's Tailscale IP (e.g., `100.120.107.12`)

**Important Notes:**
- Only **Devices: Write** permission is needed (creates ephemeral nodes)
- Don't select "OAuth Keys" - use "Auth keys" with Write permission
- The `tag:ci` allows you to control access via Tailscale ACLs
- GitHub Actions runners will appear as ephemeral devices and auto-cleanup after jobs

---

### Tailscale ACL Configuration for tag:ci

After creating the OAuth client with `tag:ci`, you must configure your Tailscale Access Control Lists (ACLs) to allow the CI runners to access your production server.

⚠️ **CRITICAL**: Tailscale SSH ACL rules do NOT accept IP addresses in the `dst` field. They only accept tags, groups, or autogroups!

#### Step 1: Tag Your Production Server

Before configuring ACLs, tag your production server.

**Option A: Via Tailscale Admin Console (Recommended)**

1. Go to https://login.tailscale.com/admin/machines
2. Find your production server (look for IP 100.120.107.12 or hostname)
3. Click the three dots `...` → "Edit machine..."
4. In the "Tags" field, type: `tag:prod-server`
5. Click "Save"
6. Verify from your server:
   ```bash
   ssh deploy@notes.engen.tech "tailscale status"
   # Should show "tag:prod-server" in the output
   ```

**Option B: Via CLI Re-authentication**

```bash
# SSH into production server
ssh deploy@notes.engen.tech

# Re-authenticate with tags (generates new node key, keeps same IP)
sudo tailscale login --advertise-tags=tag:prod-server --force-reauth

# Follow the authentication link, then verify:
tailscale status
```

**Note**: `tailscale set --advertise-tags` does NOT exist. Use admin console (easiest, no re-auth) or `tailscale login --advertise-tags` (requires re-auth).

#### Step 2: Access Tailscale ACL Editor

1. Go to https://login.tailscale.com/admin/acls
2. Click "Edit" to open the ACL editor

#### Step 3: Define Tag Owners

Add both `tag:ci` and `tag:prod-server` to the `tagOwners` section:

```json
{
  "tagOwners": {
    "tag:ci": ["autogroup:admin"],          // GitHub Actions ephemeral nodes
    "tag:prod-server": ["autogroup:admin"]  // Production server
  },
```

**Options for tag owners:**
- `"autogroup:admin"` - All tailnet admins (recommended for OAuth clients)
- `"group:ci-admins"` - Custom group (must create group first)
- `"user@example.com"` - Specific user email

#### Step 4: Configure Network ACLs

Add rules to allow `tag:ci` nodes to access your production server:

```json
  "acls": [
    {
      "action": "accept",
      "src": ["tag:ci"],
      "dst": ["tag:prod-server:22"]  // Use tag, can also use IP here
    }
  ],
```

**Note**: Network ACLs CAN use IP addresses (`"100.120.107.12:22"`), but using tags is more maintainable.

#### Step 5: Configure SSH Rules (Recommended)

For fine-grained SSH access control, add SSH-specific rules:

```json
  "ssh": [
    {
      "action": "accept",
      "src": ["tag:ci"],
      "dst": ["tag:prod-server"],  // MUST use tag, NOT IP!
      "users": ["deploy"]           // SSH username on target server
    }
  ]
}
```

**CRITICAL**: SSH ACL `dst` field MUST use tags/groups/autogroups. IP addresses like `"100.120.107.12"` will cause an error!

**Important**: The `"users"` field specifies which OS user accounts on the target server the CI can SSH into. Use `"deploy"` to match your deployment user.

#### Complete ACL Example

Here's a complete minimal ACL configuration:

```json
{
  "tagOwners": {
    "tag:ci": ["autogroup:admin"],
    "tag:prod-server": ["autogroup:admin"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["tag:ci"],
      "dst": ["tag:prod-server:22"]
    }
  ],
  "ssh": [
    {
      "action": "accept",
      "src": ["tag:ci"],
      "dst": ["tag:prod-server"],  // Tag required!
      "users": ["deploy"]
    }
  ]
}
```

#### Network ACLs vs SSH ACLs

**Key Difference:**

| ACL Section | Can use IPs? | Can use Tags? | Example |
|-------------|--------------|---------------|---------|
| **Network ACLs** (`acls`) | ✅ Yes | ✅ Yes | `"dst": ["100.120.107.12:22"]` or `"dst": ["tag:prod-server:22"]` |
| **SSH ACLs** (`ssh`) | ❌ No | ✅ Yes (required!) | `"dst": ["tag:prod-server"]` |

#### Step 6: Test ACL Configuration

After saving your ACLs:

1. Click "Save" in the ACL editor
2. The editor will validate your JSON syntax
3. Fix any errors before saving

**Test connectivity:**
```bash
# Trigger a deployment to test
make deploy-trigger

# Watch the workflow logs
make deploy-watch

# Look for Tailscale connection success:
# "Tailscale started successfully"
# "Connected to Tailscale network"
```

#### Troubleshooting ACL Issues

**Error: "invalid dst \"100.120.107.12\""**
- **Cause**: SSH ACL rules cannot use IP addresses in `dst` field
- **Fix**: Use a tag instead:
  ```json
  // ❌ WRONG - IP in SSH rule
  "ssh": [{"dst": ["100.120.107.12"]}]

  // ✅ CORRECT - Tag in SSH rule
  "ssh": [{"dst": ["tag:prod-server"]}]
  ```
- **Action**: Tag your production server first, then use the tag in SSH ACLs

**Error: "tag collision" or "tag ownership"**
- Ensure both `tag:ci` and `tag:prod-server` are defined in `tagOwners`
- Verify your OAuth client's tag matches exactly (`tag:ci`, not `ci`)
- Check that production server has been tagged: `tailscale status | grep tag:prod-server`

**Error: "connection refused" or "timeout" after Tailscale connects**
- Check ACL rules use `tag:prod-server` instead of IP
- Verify port 22 is included in the network ACL destination: `"tag:prod-server:22"`
- Ensure SSH service is running on target server: `systemctl status sshd`
- Verify production server tag is active: `tailscale status`

**Error: "permission denied" during SSH**
- Check the `users` field in SSH rules matches your deployment user (`deploy`)
- Verify the SSH key in GitHub secrets is authorized on the server
- Ensure the tag:prod-server is correctly applied to the target server

#### Advanced ACL Options

**Multiple servers (using tags - recommended):**
```json
"tagOwners": {
  "tag:ci": ["autogroup:admin"],
  "tag:prod-server": ["autogroup:admin"],
  "tag:staging-server": ["autogroup:admin"]
},
"acls": [
  {
    "action": "accept",
    "src": ["tag:ci"],
    "dst": ["tag:prod-server:22", "tag:staging-server:22"]
  }
],
"ssh": [
  {
    "action": "accept",
    "src": ["tag:ci"],
    "dst": ["tag:prod-server", "tag:staging-server"],  // Tags required!
    "users": ["deploy"]
  }
]
```

**Multiple tags for different pipelines:**
```json
"tagOwners": {
  "tag:ci-prod": ["autogroup:admin"],
  "tag:ci-staging": ["autogroup:admin"],
  "tag:prod-server": ["autogroup:admin"],
  "tag:staging-server": ["autogroup:admin"]
},
"acls": [
  {
    "action": "accept",
    "src": ["tag:ci-prod"],
    "dst": ["tag:prod-server:22"]
  },
  {
    "action": "accept",
    "src": ["tag:ci-staging"],
    "dst": ["tag:staging-server:22"]
  }
],
"ssh": [
  {
    "action": "accept",
    "src": ["tag:ci-prod"],
    "dst": ["tag:prod-server"],
    "users": ["deploy"]
  },
  {
    "action": "accept",
    "src": ["tag:ci-staging"],
    "dst": ["tag:staging-server"],
    "users": ["deploy"]
  }
]
```

**Restrict by GitHub repository (using separate OAuth clients):**
- Create different OAuth clients for different repos
- Use different tags for each repo: `tag:ci-repo1`, `tag:ci-repo2`
- Grant different permissions per tag

#### ACL Best Practices

1. **Principle of Least Privilege**: Only grant access to specific servers and ports needed
2. **Use SSH rules**: More secure than broad network ACLs
3. **Document tags**: Add comments in ACL JSON (not standard JSON but Tailscale supports it)
4. **Test changes**: Use the ACL editor's test feature before saving
5. **Version control**: Keep a backup of your ACL configuration
6. **Audit regularly**: Review who has tagOwner permissions

#### References

- [Tailscale ACL Documentation](https://tailscale.com/kb/1198/access-controls)
- [Tailscale GitHub Action Guide](https://tailscale.com/kb/1276/tailscale-github-action)
- [SSH Access Controls](https://tailscale.com/kb/1193/tailscale-ssh)

---

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
