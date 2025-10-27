# Tailscale Setup Guide for GitHub Actions Deployment

This guide walks you through configuring Tailscale for secure GitHub Actions deployments to your production server.

## Overview

Tailscale enables GitHub Actions runners to securely SSH into your production server through a private mesh network, without exposing SSH to the public internet.

**Architecture:**
```
GitHub Actions Runner → Tailscale Network → Production Server
                       (ephemeral node)      (tag:prod-server)
                       tag:ci                deploy user
```

## Prerequisites

- Tailscale installed and running on your production server
- Tailscale account with admin access
- GitHub repository with secrets configured

## Complete Setup Process

### Part 1: Create Tailscale Ephemeral Auth Key

**Time required**: ~3 minutes

1. **Navigate to Auth Keys settings**
   - URL: https://login.tailscale.com/admin/settings/keys
   - Click "Generate auth key"

2. **Configure the auth key**
   - **Description**: `GitHub Actions CI/CD - ParchMark`
   - **Ephemeral**: ✅ **Check this box** (key expires after node disconnects)
   - **Reusable**: ✅ **Check this box** (can be used multiple times)
   - **Tags**: Select or enter `tag:ci`
   - **Pre-approved**: ✅ Check this (optional, bypasses ACL checks during auth)
   - Leave expiry at default (90 days) or set longer if needed

3. **Generate and save the key**
   - Click "Generate key"
   - **IMMEDIATELY COPY** the auth key (shown only once):
     - Format: `tskey-auth-xxxxxxxxxxxxx-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy`
   - Store securely - this will be your `TS_AUTHKEY` secret

### Part 2: Tag Your Production Server

**Time required**: ~3 minutes

⚠️ **CRITICAL**: Tailscale SSH ACL rules require tags, NOT IP addresses in the `dst` field!

**Option A: Via Tailscale Admin Console (Recommended)**

1. Go to https://login.tailscale.com/admin/machines
2. Find your production server (look for IP 100.120.107.12 or hostname)
3. Click the three dots `...` menu on the far right
4. Select **"Edit tags"** (or **"Edit ACL Tags"**)
5. In the tags field, add: `tag:prod-server`
6. Click **"Save"**
7. Verify the tag was applied:
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

### Part 3: Configure Tailscale ACLs

**Time required**: ~10 minutes

1. **Open ACL editor**
   - URL: https://login.tailscale.com/admin/acls
   - Click "Edit"

2. **Add tag configuration**

   Add/modify the following sections in your ACL JSON:

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
         "dst": ["tag:prod-server"],  // Must use tag, NOT IP!
         "users": ["deploy"]
       }
     ]
   }
   ```

   **Important**:
   - SSH ACL `dst` field MUST use tags (like `tag:prod-server`)
   - SSH ACL `dst` field CANNOT use IP addresses (will cause error!)
   - Network ACL `dst` field CAN use either tags OR IPs
   - Replace `deploy` with your actual SSH username

3. **Save and validate**
   - Click "Save"
   - Tailscale will validate JSON syntax
   - Fix any errors before saving

### Part 4: Configure GitHub Secrets

**Time required**: ~3 minutes

1. **Navigate to repository secrets**
   - URL: `https://github.com/YOUR_USERNAME/parchmark/settings/secrets/actions`
   - Click "New repository secret"

2. **Add Tailscale auth key**

   Create this secret (case-sensitive):

   | Secret Name | Value | Example |
   |-------------|-------|---------|
   | `TS_AUTHKEY` | Auth key from Part 1 | `tskey-auth-xxxxx-yyyyyy...` |

   **Important**: This is the ephemeral, reusable auth key you generated in Part 1.

3. **Update PROD_HOST secret**

   Update the existing `PROD_HOST` secret:

   | Secret Name | Value | Notes |
   |-------------|-------|-------|
   | `PROD_HOST` | `100.120.107.12` | Your server's Tailscale IP |

### Part 5: Verify Workflow Configuration

**Time required**: ~2 minutes

1. **Check workflow file**

   Ensure `.github/workflows/deploy.yml` contains:

   ```yaml
   deploy-to-production:
     steps:
       - name: Connect to Tailscale
         uses: tailscale/github-action@v2
         with:
           authkey: ${{ secrets.TS_AUTHKEY }}

       - name: Deploy via SSH
         uses: appleboy/ssh-action@v1.2.2
         with:
           host: ${{ secrets.PROD_HOST }}
           username: ${{ secrets.PROD_USER }}
           key: ${{ secrets.PROD_SSH_KEY }}
           # ...
   ```

2. **Verify all required secrets exist**

   Required GitHub secrets:
   - ✅ `TS_AUTHKEY` (Ephemeral auth key)
   - ✅ `PROD_HOST` (Tailscale IP)
   - ✅ `PROD_USER` (e.g., `deploy`)
   - ✅ `PROD_SSH_KEY` (SSH private key)
   - ✅ `GHCR_PULL_TOKEN` (GitHub Container Registry token)

### Part 6: Test Deployment

**Time required**: ~5 minutes

1. **Trigger manual deployment**
   ```bash
   make deploy-trigger
   ```

2. **Watch deployment progress**
   ```bash
   make deploy-watch
   ```

3. **Check for success indicators**

   In the GitHub Actions logs, look for:
   ```
   ✅ Tailscale started successfully
   ✅ Connected to Tailscale network
   ✅ SSH connection successful
   ✅ Deployment completed successfully
   ```

4. **Verify production health**
   ```bash
   make deploy-verify
   ```

## Troubleshooting

### Issue: "tag collision" or "tag ownership" error

**Cause**: Tag not defined in ACL or auth key tag doesn't match

**Solution**:
- Verify `tag:ci` exists in `tagOwners` section of ACLs
- Ensure auth key was created with tag `tag:ci` selected

### Issue: Connection timeout after Tailscale connects

**Cause**: ACL doesn't allow access to server

**Solution**:
- Verify server's Tailscale IP is correct in ACL
- Ensure port 22 is specified: `"100.120.107.12:22"`
- Check SSH service is running: `systemctl status sshd`

### Issue: "Permission denied" during SSH

**Cause**: SSH rules don't match deployment user

**Solution**:
- Verify `"users": ["deploy"]` in SSH rules matches actual username
- Check SSH key in `PROD_SSH_KEY` is authorized on server
- Test SSH manually: `ssh -i key.pem deploy@100.120.107.12`

### Issue: Auth key not working

**Cause**: Key copied incorrectly, expired, or revoked

**Solution**:
- Generate a new auth key at https://login.tailscale.com/admin/settings/keys
- Ensure "Ephemeral" and "Reusable" are both checked
- Select `tag:ci` in the tags field
- Copy the full key (starts with `tskey-auth-`)
- Update `TS_AUTHKEY` secret in GitHub with new value

## Security Best Practices

### ✅ What We Implemented

1. **Ephemeral Auth Keys**: Nodes auto-cleanup after GitHub Actions job completes
2. **Reusable Keys**: Same key works for multiple deployments
3. **Tag-based Access**: `tag:ci` isolates CI/CD access
4. **SSH User Restriction**: Only `deploy` user accessible
5. **Private Network**: No public SSH exposure
6. **Specific Destination**: ACL limits access to single server

### ✅ Additional Recommendations

1. **Rotate auth keys** every 90 days (or set expiry when creating)
2. **Monitor ephemeral nodes** in Tailscale admin console
3. **Audit ACL changes** regularly
4. **Use separate tags** for different environments (prod/staging)
5. **Enable MFA** on Tailscale account
6. **Review tagOwners** permissions periodically
7. **Revoke old auth keys** when no longer needed

## Quick Reference

### Commands

```bash
# Deployment
make deploy-trigger          # Trigger GitHub Actions deployment
make deploy-watch           # Watch deployment progress
make deploy-verify          # Verify production health

# Tailscale on server
tailscale status            # Check Tailscale connection
tailscale ip               # Show Tailscale IPs
tailscale ping <node>      # Test connectivity
```

### URLs

- **Auth Keys**: https://login.tailscale.com/admin/settings/keys
- **ACL Editor**: https://login.tailscale.com/admin/acls
- **GitHub Secrets**: https://github.com/YOUR_USERNAME/parchmark/settings/secrets/actions
- **Tailscale Machines**: https://login.tailscale.com/admin/machines

### Key Concepts

| Term | Definition |
|------|------------|
| **Auth Key** | Ephemeral, reusable key for GitHub Actions to join Tailscale network |
| **tag:ci** | Tag identifying ephemeral CI/CD nodes |
| **tagOwners** | ACL section defining who can create tagged nodes |
| **Ephemeral Node** | Temporary Tailscale device (auto-cleanup after job) |
| **Reusable Key** | Auth key that can be used for multiple connections |
| **ACL** | Access Control List (firewall rules) |
| **SSH Rules** | Fine-grained SSH access control |

## Complete Configuration Checklist

Use this checklist to verify your setup:

### Auth Key
- [ ] Auth key created with description
- [ ] "Ephemeral" checkbox enabled
- [ ] "Reusable" checkbox enabled
- [ ] Tag `tag:ci` selected
- [ ] Auth key copied immediately (shown only once)
- [ ] Key starts with `tskey-auth-`

### Tailscale ACLs
- [ ] ACL editor opened at https://login.tailscale.com/admin/acls
- [ ] `tag:ci` added to `tagOwners` section
- [ ] `tagOwners` specifies `autogroup:admin` or appropriate group
- [ ] Network ACL added for `tag:ci` → server IP:22
- [ ] SSH rule added for `tag:ci` → server IP with `deploy` user
- [ ] Server's Tailscale IP verified (e.g., `100.120.107.12`)
- [ ] ACL JSON saved and validated successfully

### GitHub Secrets
- [ ] `TS_AUTHKEY` added to repository secrets
- [ ] `PROD_HOST` updated to server's Tailscale IP
- [ ] `PROD_USER` set to `deploy` (or correct username)
- [ ] `PROD_SSH_KEY` contains valid SSH private key
- [ ] `GHCR_PULL_TOKEN` configured for image pulling

### Workflow Configuration
- [ ] `.github/workflows/deploy.yml` has Tailscale step
- [ ] Tailscale action uses version @v2
- [ ] `authkey` parameter uses `${{ secrets.TS_AUTHKEY }}`
- [ ] SSH step uses `${{ secrets.PROD_HOST }}`
- [ ] Workflow committed and pushed to repository

### Testing
- [ ] Test deployment triggered (`make deploy-trigger`)
- [ ] Deployment logs show Tailscale connection success
- [ ] SSH connection successful to production server
- [ ] Deployment completes without errors
- [ ] Production health check passes (`make deploy-verify`)
- [ ] Ephemeral node appears in Tailscale admin console
- [ ] Ephemeral node disappears after job completion

## Next Steps

After completing this setup:

1. **Merge deployment branch to main**
   ```bash
   git checkout main
   git merge automatic-deployment
   git push origin main
   ```

2. **Enable automatic deployments**
   - Workflow already configured to run on push to `main`
   - Every push to main will trigger automated deployment

3. **Set up branch protection** (recommended)
   - Require PR reviews before merging to main
   - Require status checks to pass
   - Prevents broken code from auto-deploying

4. **Monitor deployments**
   - Check GitHub Actions tab after each push
   - Use `make deploy-status` to see recent deployments
   - Set up notifications for failed deployments

## Getting Help

- **Troubleshooting Guide**: `docs/deployment_upgrade/TROUBLESHOOTING.md`
- **Deployment Commands**: `make deploy-help`
- **Tailscale Docs**: https://tailscale.com/kb/1276/tailscale-github-action
- **GitHub Issues**: Report issues at repository

---

**Last Updated**: 2025-10-26
**Tested With**: Tailscale v1.78+, GitHub Actions, Ubuntu 24.04
