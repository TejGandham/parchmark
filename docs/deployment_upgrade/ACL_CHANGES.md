# Tailscale ACL Changes for GitHub Actions CI/CD

## Current ACL Analysis

Your current configuration:
- ✅ Wide-open network access (`"*"` to `"*:*"`) - No restrictions
- ✅ SSH check mode for all members to their own devices
- ✅ Node attributes for two Mullvad nodes (VPN exit nodes)

**Good news**: Your existing wide-open ACL already allows GitHub Actions CI/CD access! However, we should add explicit rules for better security and clarity.

## Recommended Changes

### Option 1: Minimal Changes (Keep Wide-Open Access)

**What to add:**
1. `tagOwners` section to define `tag:ci`
2. Explicit SSH rule for `tag:ci` (for clarity and future tightening)

**What stays the same:**
- Your wide-open ACL rule (no disruption to existing access)
- Your existing SSH check rule
- Your Mullvad node attributes

### Option 2: Security-Enhanced (Recommended Long-Term)

Same as Option 1, but prepared for future ACL tightening when you're ready.

---

## Complete Updated ACL (Option 1: Minimal)

```json
// ACLs for ParchMark with GitHub Actions CI/CD support
{
    // Declare static groups of users. Use autogroups for all users or users with a specific role.
    // "groups": {
    //      "group:example": ["alice@example.com", "bob@example.com"],
    // },

    // ============================================================================
    // ADDED: Define tags for GitHub Actions CI/CD
    // ============================================================================
    "tagOwners": {
        "tag:ci": ["autogroup:admin"],  // GitHub Actions ephemeral nodes
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
        // {"action": "accept", "src": ["tag:ci"], "dst": ["100.120.107.12:22"]},
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
        // ============================================================================
        {
            "action": "accept",
            "src":    ["tag:ci"],
            "dst":    ["100.120.107.12"],  // Your production server's Tailscale IP
            "users":  ["deploy"],           // SSH username for deployment
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

### Addition 1: tagOwners Section (Lines 7-10)

```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
},
```

**Why**: Defines who can create devices with the `tag:ci` tag. Only Tailscale admins can create OAuth clients with this tag.

**Impact**: None on existing devices. Only applies to new ephemeral GitHub Actions nodes.

### Addition 2: SSH Rule for tag:ci (Lines 33-38)

```json
{
    "action": "accept",
    "src":    ["tag:ci"],
    "dst":    ["100.120.107.12"],
    "users":  ["deploy"],
},
```

**Why**: Explicitly allows GitHub Actions runners to SSH as the `deploy` user to your production server.

**Impact**: None on existing access. Your wide-open ACL already permits this, but this makes it explicit and survives future ACL tightening.

### No Changes To:
- ✅ Your `"*"` to `"*:*"` network rule (line 16)
- ✅ Your existing SSH check rule (lines 23-28)
- ✅ Your Mullvad node attributes (lines 42-45)

---

## Step-by-Step Application

1. **Get your server's Tailscale IP** (if you don't know it):
   ```bash
   ssh deploy@notes.engen.tech
   tailscale ip -4
   # Example output: 100.120.107.12
   ```

2. **Open Tailscale ACL Editor**:
   - URL: https://login.tailscale.com/admin/acls
   - Click "Edit"

3. **Make the changes**:
   - Add the `tagOwners` section after the commented-out `groups` section
   - Add the new SSH rule after your existing SSH rule
   - Replace `100.120.107.12` with your server's actual Tailscale IP
   - Replace `deploy` with your SSH username (if different)

4. **Save and Validate**:
   - Click "Save"
   - Tailscale will validate the JSON
   - Fix any syntax errors (usually missing/extra commas)

---

## Future Security Tightening (When Ready)

When you're ready to move from wide-open access to restricted access:

### Step 1: Document your current access needs
Identify all device-to-device connections you need:
- Your laptop → Production server
- Your phone → Home services
- Etc.

### Step 2: Replace the wildcard rule

Remove this:
```json
{"action": "accept", "src": ["*"], "dst": ["*:*"]},
```

Add specific rules:
```json
{
    "action": "accept",
    "src": ["autogroup:admin"],  // Admins can access everything
    "dst": ["*:*"]
},
{
    "action": "accept",
    "src": ["tag:ci"],
    "dst": ["100.120.107.12:22,443,8000"]  // GitHub Actions to prod
},
// Add other specific rules as needed
```

---

## Validation After Applying Changes

### Test 1: Verify ACL Syntax
After saving, Tailscale will show:
- ✅ "Access controls updated successfully"
- ❌ Syntax error message (fix JSON and retry)

### Test 2: Trigger Test Deployment
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

### Test 3: Verify Existing Access Still Works
Test your own access wasn't disrupted:
```bash
# From your machine
ssh deploy@notes.engen.tech
# Should still work normally
```

---

## Troubleshooting

### Issue: "tag:ci not allowed" or "tag ownership error"

**Cause**: Missing or incorrect `tagOwners` section

**Fix**: Ensure the `tagOwners` section is present and matches exactly:
```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
},
```

### Issue: JSON syntax error when saving

**Common mistakes:**
- Missing comma after `tagOwners` section
- Extra comma after last item in `ssh` array
- Missing comma between SSH rules

**Fix**: Check these specific locations:
```json
"tagOwners": {
    "tag:ci": ["autogroup:admin"],
},  // ← Comma needed here

"ssh": [
    { /* first rule */ },  // ← Comma needed here
    { /* second rule */ }  // ← NO comma here (last item)
],
```

### Issue: GitHub Actions still can't connect

**Verify in order:**
1. ACL saved successfully (no errors)
2. `tag:ci` present in `tagOwners`
3. SSH rule includes correct server IP
4. SSH rule includes correct username (`deploy`)
5. GitHub secrets configured (`TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`)
6. Server's Tailscale is running: `ssh deploy@notes.engen.tech tailscale status`

---

## Summary

**What you're adding:**
- `tagOwners` for `tag:ci` (3 lines)
- SSH rule for GitHub Actions (6 lines)

**Total changes:** 9 lines added, 0 lines modified, 0 lines removed

**Risk level:** ⚠️ **Very Low**
- No existing rules modified
- Only additive changes
- Wide-open ACL remains active
- Easy to revert (just remove added lines)

**Time to apply:** ~5 minutes

**Next step:** Copy the complete ACL above and paste into your ACL editor, replacing your current ACL.

---

**Pro Tip**: Before making changes, copy your current ACL to a text file as backup. If anything goes wrong, you can paste it back.
