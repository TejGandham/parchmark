# Tailscale ACL Changes for GitHub Actions CI/CD

## ⚠️ CRITICAL: SSH ACL Syntax Requirements

**Important**: Tailscale SSH ACL rules do NOT accept IP addresses in the `dst` field. They only accept:
- Tags (e.g., `tag:prod-server`)
- Groups (e.g., `group:admins`)
- Autogroups (e.g., `autogroup:self`)

**This means**: Your production server must be tagged before configuring SSH ACLs.

---

## Current ACL Analysis

Your current configuration:
- ✅ Wide-open network access (`"*"` to `"*:*"`) - No restrictions
- ✅ SSH check mode for all members to their own devices
- ✅ Node attributes for two Mullvad nodes (VPN exit nodes)

**Good news**: Your existing wide-open ACL already allows GitHub Actions CI/CD network access! However, we need to configure SSH rules properly using tags.

---

## Prerequisites: Tag Your Production Server

Before modifying ACLs, you must tag your production server.

### Step 1: SSH into Production Server

```bash
ssh deploy@notes.engen.tech
```

### Step 2: Tag the Server

```bash
# Add tag:prod-server to this device
sudo tailscale set --advertise-tags=tag:prod-server

# Verify the tag was applied
tailscale status
# Look for "tag:prod-server" in the output
```

**Alternative: Tag via Tailscale Admin Console**
1. Go to https://login.tailscale.com/admin/machines
2. Find your production server (100.120.107.12)
3. Click the "..." menu → Edit machine
4. Add tag: `tag:prod-server`
5. Save

---

## Complete Updated ACL

```json
// ACLs for ParchMark with GitHub Actions CI/CD support
{
    // Declare static groups of users. Use autogroups for all users or users with a specific role.
    // "groups": {
    //      "group:example": ["alice@example.com", "bob@example.com"],
    // },

    // ============================================================================
    // ADDED: Define tags for GitHub Actions CI/CD and production server
    // ============================================================================
    "tagOwners": {
        "tag:ci": ["autogroup:admin"],          // GitHub Actions ephemeral nodes
        "tag:prod-server": ["autogroup:admin"],  // Production server
    },

    // Define access control lists for users, groups, autogroups, tags,
    // Tailscale IP addresses, and subnet ranges.
    "acls": [
        // EXISTING: Allow all connections (unchanged)
        // Comment this section out if you want to define specific restrictions.
        {"action": "accept", "src": ["*"], "dst": ["*:*"]},

        // NOTE: The rule above already allows tag:ci access.
        // When you're ready to tighten security, remove the "*" rule above
        // and uncomment this specific rule:
        // {"action": "accept", "src": ["tag:ci"], "dst": ["tag:prod-server:22"]},
    ],

    // Define users and devices that can use Tailscale SSH.
    "ssh": [
        // EXISTING: Allow all users to SSH into their own devices in check mode (unchanged)
        {
            "action": "check",
            "src":    ["autogroup:member"],
            "dst":    ["autogroup:self"],
            "users":  ["autogroup:nonroot", "root"],
        },

        // ============================================================================
        // ADDED: Allow GitHub Actions CI/CD to SSH as deploy user
        // CRITICAL: dst must use tag, NOT IP address!
        // ============================================================================
        {
            "action": "accept",
            "src":    ["tag:ci"],
            "dst":    ["tag:prod-server"],  // Use tag, NOT IP!
            "users":  ["deploy"],            // SSH username for deployment
        },
    ],

    // EXISTING: Node attributes (unchanged)
    "nodeAttrs": [
        {"target": ["100.116.209.17"], "attr": ["mullvad"]},
        {"target": ["100.91.23.64"], "attr": ["mullvad"]},
    ],

    // Test access rules every time they're saved.
    // "tests": [
    //      {
    //          "src": "alice@example.com",
    //          "accept": ["tag:example"],
    //          "deny": ["100.101.102.103:443"],
    //      },
    // ],
}
```

---

## What Changed? (Line-by-Line)

### Addition 1: tagOwners Section

```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
    "tag:prod-server": ["autogroup:admin"],  // NEW: Tag for production server
},
```

**Why**:
- `tag:ci` - Allows admins to create GitHub Actions ephemeral nodes
- `tag:prod-server` - Allows admins to tag the production server

**Impact**: None on existing devices. Only applies to newly tagged devices.

### Addition 2: SSH Rule for tag:ci

```json
{
    "action": "accept",
    "src":    ["tag:ci"],
    "dst":    ["tag:prod-server"],  // Must use tag, NOT IP!
    "users":  ["deploy"],
},
```

**Why**: Explicitly allows GitHub Actions runners (tag:ci) to SSH as the `deploy` user to the production server (tag:prod-server).

**Critical**: The `dst` field MUST use a tag, group, or autogroup. IP addresses like `"100.120.107.12"` will cause an error.

### Difference: Network ACLs vs SSH ACLs

**Network ACLs (the `acls` section)**:
- ✅ CAN use IP addresses: `"dst": ["100.120.107.12:22"]`
- ✅ CAN use tags: `"dst": ["tag:prod-server:22"]`
- ✅ CAN use wildcards: `"dst": ["*:*"]`

**SSH ACLs (the `ssh` section)**:
- ❌ CANNOT use IP addresses: `"dst": ["100.120.107.12"]` ← ERROR!
- ✅ MUST use tags: `"dst": ["tag:prod-server"]`
- ✅ MUST use groups/autogroups: `"dst": ["autogroup:self"]`

---

## Step-by-Step Application

### Step 1: Tag Your Production Server

**Via Tailscale Admin Console** (only method available):

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

**Note**: There is no CLI command to tag devices. Tags must be set via the admin console.

### Step 2: Open Tailscale ACL Editor

- URL: https://login.tailscale.com/admin/acls
- Click "Edit"

### Step 3: Make the ACL Changes

**Backup first**: Copy your current ACL to a text file

**Then replace with** the complete ACL above, which adds:
- `tag:prod-server` to `tagOwners`
- `tag:ci` to `tagOwners`
- SSH rule allowing `tag:ci` → `tag:prod-server`

### Step 4: Save and Validate

- Click "Save"
- Tailscale will validate the JSON
- Fix any syntax errors (usually missing/extra commas)

### Step 5: Verify Tag Applied

After saving ACL, check that your server's tag is recognized:

```bash
ssh deploy@notes.engen.tech "tailscale status"
# Should show tag:prod-server
```

---

## Validation After Applying Changes

### Test 1: Verify ACL Syntax
After saving, Tailscale will show:
- ✅ "Access controls updated successfully"
- ❌ Syntax error message (fix JSON and retry)

### Test 2: Verify Server Tag
```bash
ssh deploy@notes.engen.tech "tailscale status"
# Look for: 100.120.107.12  your-server  tag:prod-server  linux  -
```

### Test 3: Trigger Test Deployment
```bash
make deploy-trigger
make deploy-watch
```

Look for in GitHub Actions logs:
```
✅ Tailscale started
✅ Connected to Tailscale network
✅ SSH connection successful
```

### Test 4: Verify Existing Access Still Works
```bash
# From your machine
ssh deploy@notes.engen.tech
# Should still work normally
```

---

## Troubleshooting

### Error: "invalid dst \"100.120.107.12\""

**Cause**: SSH ACL rules cannot use IP addresses in `dst` field

**Fix**: Use a tag instead:
```json
// ❌ WRONG - IP address in SSH rule
"ssh": [
  {
    "dst": ["100.120.107.12"]  // ERROR!
  }
]

// ✅ CORRECT - Tag in SSH rule
"ssh": [
  {
    "dst": ["tag:prod-server"]  // Works!
  }
]
```

### Error: "tag:prod-server not allowed" or "tag ownership error"

**Cause**: Tag not defined in `tagOwners`

**Fix**: Ensure `tagOwners` includes both tags:
```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
    "tag:prod-server": ["autogroup:admin"],  // Must be here!
},
```

### Server tag not showing up in ACL

**Cause**: Tag may not have propagated yet

**Fix**: Wait 30 seconds, then check:
```bash
tailscale status
```

If still not showing, re-apply the tag via admin console.

### GitHub Actions still can't connect

**Verify in order:**
1. ✅ Production server tagged: `tailscale status | grep tag:prod-server`
2. ✅ ACL saved successfully (no errors)
3. ✅ `tag:ci` present in `tagOwners`
4. ✅ `tag:prod-server` present in `tagOwners`
5. ✅ SSH rule uses `tag:prod-server` in `dst` (not IP!)
6. ✅ SSH rule includes correct username (`deploy`)
7. ✅ GitHub secrets configured (`TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`)

---

## JSON Syntax Troubleshooting

### Common mistakes:

**Missing comma after tagOwners:**
```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
    "tag:prod-server": ["autogroup:admin"],
},  // ← Comma needed here

"acls": [
```

**Extra comma after last SSH rule:**
```json
"ssh": [
    { /* first rule */ },  // ← Comma needed here
    { /* second rule */ }  // ← NO comma here (last item)
],
```

**Using IP instead of tag in SSH dst:**
```json
// ❌ WRONG
"ssh": [{"dst": ["100.120.107.12"]}]

// ✅ CORRECT
"ssh": [{"dst": ["tag:prod-server"]}]
```

---

## Summary

**What you're adding:**
- Tag to production server: `tag:prod-server`
- `tagOwners` for `tag:ci` and `tag:prod-server` (5 lines)
- SSH rule for GitHub Actions using tags (6 lines)

**Total changes:**
- 1 server tag added
- 11 lines added to ACL
- 0 lines modified
- 0 lines removed

**Risk level:** ⚠️ **Very Low**
- No existing rules modified
- Only additive changes
- Wide-open ACL remains active
- Easy to revert (remove tag and added lines)

**Time to apply:** ~10 minutes
- Tag server: 2 minutes
- Update ACL: 5 minutes
- Validate: 3 minutes

---

## Future Security Tightening (When Ready)

When you're ready to move from wide-open access to restricted access:

### Replace wildcard network rule

Remove this:
```json
{"action": "accept", "src": ["*"], "dst": ["*:*"]},
```

Add specific rules:
```json
{
    "action": "accept",
    "src": ["autogroup:admin"],
    "dst": ["*:*"]  // Admins can access everything
},
{
    "action": "accept",
    "src": ["tag:ci"],
    "dst": ["tag:prod-server:22,443,8000"]  // GitHub Actions to prod
},
```

**Note**: Network ACLs CAN use IP addresses, but using tags is more maintainable:
```json
// Both valid in network ACLs:
"dst": ["100.120.107.12:22"]        // IP address - works
"dst": ["tag:prod-server:22"]       // Tag - recommended
```

---

## Quick Reference

### Key Concepts

| ACL Section | Can use IPs? | Can use Tags? | Example |
|-------------|--------------|---------------|---------|
| **Network ACLs** (`acls`) | ✅ Yes | ✅ Yes | `"dst": ["100.120.107.12:22"]` or `"dst": ["tag:prod-server:22"]` |
| **SSH ACLs** (`ssh`) | ❌ No | ✅ Yes (required!) | `"dst": ["tag:prod-server"]` |

### Commands

```bash
# Tag production server: Use admin console
# https://login.tailscale.com/admin/machines → Edit machine → Add tag:prod-server

# Verify tag applied (from server)
tailscale status

# Get server's Tailscale IP (for reference)
tailscale ip -4

# Test deployment
make deploy-trigger
make deploy-watch
```

### URLs

- **Machines (for tagging)**: https://login.tailscale.com/admin/machines
- **ACL Editor**: https://login.tailscale.com/admin/acls
- **OAuth Clients**: https://login.tailscale.com/admin/settings/oauth

---

**Pro Tips**:
1. Always tag servers before writing SSH ACL rules
2. Use tags instead of IPs in network ACLs too (more maintainable)
3. Backup your ACL before making changes
4. Test each change incrementally

**Next step**: Tag your production server, then apply the ACL above.
