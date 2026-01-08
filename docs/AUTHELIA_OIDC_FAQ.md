# OIDC FAQ & Knowledge Base

Frequently asked questions and knowledge base for ParchMark OIDC implementation.

---

## General Questions

### Q: What is OIDC and why do we use it?

**A**: OpenID Connect is an authentication protocol built on top of OAuth 2.0. We use it to:
- Allow users to login via a central authentication provider (Authelia)
- Reduce password management overhead
- Improve security with professional token handling
- Support federated authentication

**Related**: [AUTHELIA_OIDC_IMPLEMENTATION.md](AUTHELIA_OIDC_IMPLEMENTATION.md)

---

### Q: Will I lose access to my account if I don't link OIDC?

**A**: No. Local login continues to work alongside OIDC:
- Your password-based login stays active
- Both methods access the same account
- You can use whichever method you prefer
- No action required unless announced

**Related**: [AUTHELIA_OIDC_QUICKSTART.md](AUTHELIA_OIDC_QUICKSTART.md)

---

### Q: Is OIDC mandatory?

**A**: No, OIDC is optional:
- Organization may default to SSO for new users
- Existing local users keep working
- You can choose which method to use
- Both methods remain available in hybrid mode

**Related**: [AUTHELIA_OIDC_MIGRATION_GUIDE.md](AUTHELIA_OIDC_MIGRATION_GUIDE.md)

---

## Technical Questions

### Q: How is my password handled with OIDC?

**A**: When using OIDC:
- Your password is NOT shared with ParchMark
- You authenticate directly with Authelia (the SSO provider)
- ParchMark receives a security token, not your password
- Your password is managed by Authelia, not ParchMark

**Security Note**: This is more secure than traditional password-based login

**Related**: [AUTHELIA_OIDC_SECURITY_HARDENING.md](AUTHELIA_OIDC_SECURITY_HARDENING.md)

---

### Q: What data does OIDC share with ParchMark?

**A**: Only the minimum needed:
- Username (from `preferred_username` or email)
- Email address
- Unique identifier (`sub` claim)

ParchMark does NOT receive:
- Your password
- Your phone number (unless explicitly requested)
- Your physical address
- Your authentication history

**Related**: [AUTHELIA_OIDC_API_REFERENCE.md](AUTHELIA_OIDC_API_REFERENCE.md)

---

### Q: How often are tokens refreshed?

**A**: Automatic refresh happens:
- Access token: Valid for 30 minutes
- Automatic refresh: 60 seconds before expiration
- Manual refresh: When you need it
- Logout: Immediate token invalidation

You won't notice token refresh - it's automatic and transparent.

**Related**: [AUTHELIA_OIDC_IMPLEMENTATION.md](AUTHELIA_OIDC_IMPLEMENTATION.md)

---

### Q: What happens if the OIDC provider is down?

**A**: If Authelia (SSO) is temporarily unavailable:
- OIDC login doesn't work
- Local login still works
- Resume using password-based login temporarily
- OIDC works again when Authelia is restored

We monitor Authelia uptime and alert on issues.

**Related**: [AUTHELIA_OIDC_MONITORING.md](AUTHELIA_OIDC_MONITORING.md)

---

## Troubleshooting

### Q: I keep getting redirected back to the login page

**A**: This typically means:

1. **Token expired**: Try clearing browser cache
   ```javascript
   // In browser console:
   localStorage.clear();
   window.location.reload();
   ```

2. **Cookies blocked**: Check browser cookie settings
   - Allow cookies for notes.engen.tech and auth.engen.tech
   - Check privacy mode - it blocks cookies

3. **Clock out of sync**: Device time might be wrong
   - Check system time is correct
   - Sync with time server if needed

4. **Authelia down**: Check status page
   - Temporary issue, try again in a few minutes

**Related**: [AUTHELIA_OIDC_TROUBLESHOOTING.md](AUTHELIA_OIDC_TROUBLESHOOTING.md)

---

### Q: SSO button doesn't appear on login page

**A**: This means OIDC isn't configured:

1. **Check browser console** (F12 → Console):
   ```javascript
   console.log('OIDC config:', window.__OIDC_CONFIG__);
   ```

2. **Possible causes**:
   - Environment variables not set
   - Frontend not updated
   - Browser cached old version

3. **Solution**:
   - Clear cache: Ctrl+Shift+Delete
   - Check environment variables
   - Restart browser

**Related**: [AUTHELIA_OIDC_FRONTEND_DEVELOPER_GUIDE.md](AUTHELIA_OIDC_FRONTEND_DEVELOPER_GUIDE.md)

---

### Q: "Invalid client_id" error when clicking SSO

**A**: The OIDC client isn't registered correctly in Authelia:

1. **Verify Authelia configuration**:
   ```bash
   docker logs authelia | grep parchmark-web
   ```

2. **Check client registration**:
   - Client ID must match: `parchmark-web`
   - Check authelia/configuration.yml
   - Restart Authelia after changes

3. **Verify frontend configuration**:
   - VITE_OIDC_CLIENT_ID should be `parchmark-web`
   - Environment variables correctly set

**Related**: [AUTHELIA_OIDC_CONFIG_EXAMPLE.md](AUTHELIA_OIDC_CONFIG_EXAMPLE.md)

---

### Q: I can't create an account with OIDC

**A**: OIDC doesn't require creating an account - auto-creation happens:

1. **On first OIDC login**:
   - You authenticate with Authelia
   - ParchMark automatically creates your account
   - You're logged in and ready to use

2. **If this doesn't work**:
   - Check database has required columns (oidc_sub, email, auth_provider)
   - Check database migrations applied
   - Review backend logs for errors

   ```bash
   docker logs parchmark-backend | grep -i "creating user\|oidc"
   ```

**Related**: [AUTHELIA_OIDC_QUICKSTART.md](AUTHELIA_OIDC_QUICKSTART.md)

---

## Security Questions

### Q: Is OIDC more secure than passwords?

**A**: Yes, for several reasons:

1. **No password sharing**: You never type your password on ParchMark
2. **Professional token handling**: Tokens are cryptographically signed
3. **Automatic expiration**: Tokens expire quickly and auto-refresh
4. **Centralized security**: Security managed by professional SSO provider
5. **Audit trail**: All logins logged and auditable

**Related**: [AUTHELIA_OIDC_SECURITY_HARDENING.md](AUTHELIA_OIDC_SECURITY_HARDENING.md)

---

### Q: What if my token gets stolen?

**A**: Token theft is mitigated by:

1. **Short expiration**: Token valid for only 30 minutes
2. **Automatic refresh**: New token issued regularly
3. **Secure channel**: HTTPS prevents interception
4. **Device binding**: Tokens tied to your device
5. **IP monitoring**: Suspicious IP addresses logged

If theft suspected:
1. Logout from all devices
2. Change password in Authelia
3. Contact support team

**Related**: [AUTHELIA_OIDC_SECURITY_HARDENING.md](AUTHELIA_OIDC_SECURITY_HARDENING.md)

---

### Q: Can someone login as me if they know my email?

**A**: No, your email alone isn't sufficient:

1. **Authelia authentication required**: They need Authelia login credentials
2. **Your password needed**: Email + password or SSO credentials
3. **No email login**: Email is only used for account linking, not authentication
4. **OIDC provider security**: Relies on SSO provider's security

Your email is public, but your Authelia credentials are private.

**Related**: [AUTHELIA_OIDC_SECURITY_HARDENING.md](AUTHELIA_OIDC_SECURITY_HARDENING.md)

---

## Performance Questions

### Q: Is OIDC slower than local login?

**A**: Minimal difference:

- **Local login**: ~50ms (no network call)
- **OIDC login**: First time ~200ms, subsequent ~50ms (cached)
- **Difference**: Barely perceptible to users

After first login, OIDC caches provider keys, making subsequent logins very fast.

**Related**: [AUTHELIA_OIDC_IMPLEMENTATION.md](AUTHELIA_OIDC_IMPLEMENTATION.md)

---

### Q: Will OIDC slow down my API requests?

**A**: No measurable impact:

- **Token validation**: <10ms (in-memory)
- **API request overhead**: <1ms additional
- **Typical API request**: 50-100ms total

OIDC adds negligible overhead to API requests.

**Related**: [AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md](AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md)

---

## Account & Data Questions

### Q: Will I lose my notes if I switch to OIDC?

**A**: No, your notes are preserved:

1. **Data not deleted**: Your notes stay in database
2. **Account merged**: Local and OIDC accounts can be linked
3. **Full access**: You immediately have access to all existing notes
4. **No action required**: Switching is seamless

**Related**: [AUTHELIA_OIDC_MIGRATION_GUIDE.md](AUTHELIA_OIDC_MIGRATION_GUIDE.md)

---

### Q: Can I have both local and OIDC login on the same account?

**A**: Yes, in hybrid mode:

1. **Account linking**: Local and OIDC accounts can be linked
2. **Same data**: Both methods access same account
3. **Full flexibility**: Use whichever method you prefer
4. **Shared notes**: All notes visible from either method

**Related**: [AUTHELIA_OIDC_MIGRATION_GUIDE.md](AUTHELIA_OIDC_MIGRATION_GUIDE.md)

---

### Q: What happens to my account if I'm deleted from Authelia?

**A**: Your ParchMark account becomes inaccessible:

1. **OIDC login**: No longer works (credentials invalid)
2. **Local login**: Still works (if not deleted from ParchMark)
3. **Your data**: Remains in database (can be recovered by admin)
4. **Re-adding**: Create new ParchMark account if re-added to Authelia

**Related**: [AUTHELIA_OIDC_TROUBLESHOOTING.md](AUTHELIA_OIDC_TROUBLESHOOTING.md)

---

## Support Questions

### Q: How do I get help with OIDC issues?

**A**: Multiple resources available:

1. **Self-service**:
   - Check this FAQ
   - Read TROUBLESHOOTING guide
   - Check browser console for errors

2. **Documentation**:
   - [AUTHELIA_OIDC_QUICKSTART.md](AUTHELIA_OIDC_QUICKSTART.md) - 10-min setup
   - [AUTHELIA_OIDC_LOCAL_TESTING.md](AUTHELIA_OIDC_LOCAL_TESTING.md) - Local testing
   - [AUTHELIA_OIDC_TROUBLESHOOTING.md](AUTHELIA_OIDC_TROUBLESHOOTING.md) - Diagnosis

3. **Contact support**:
   - Email: support@example.com
   - Slack: #parchmark-support
   - Office hours: Tuesday 2-4 PM

---

### Q: Where can I find more documentation?

**A**: Complete documentation available:

**Getting Started**:
- [AUTHELIA_OIDC_QUICKSTART.md](AUTHELIA_OIDC_QUICKSTART.md) - 10-minute setup

**Reference**:
- [AUTHELIA_OIDC_API_REFERENCE.md](AUTHELIA_OIDC_API_REFERENCE.md) - API endpoints
- [AUTHELIA_OIDC_CONFIG_EXAMPLE.md](AUTHELIA_OIDC_CONFIG_EXAMPLE.md) - Configuration

**Troubleshooting**:
- [AUTHELIA_OIDC_TROUBLESHOOTING.md](AUTHELIA_OIDC_TROUBLESHOOTING.md) - Problem diagnosis
- [AUTHELIA_OIDC_LOCAL_TESTING.md](AUTHELIA_OIDC_LOCAL_TESTING.md) - Local testing

**For Administrators**:
- [AUTHELIA_OIDC_DEPLOYMENT.md](AUTHELIA_OIDC_DEPLOYMENT.md) - Deployment
- [AUTHELIA_OIDC_SECURITY_HARDENING.md](AUTHELIA_OIDC_SECURITY_HARDENING.md) - Security

**For Developers**:
- [AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md](AUTHELIA_OIDC_BACKEND_DEVELOPER_GUIDE.md) - Backend
- [AUTHELIA_OIDC_FRONTEND_DEVELOPER_GUIDE.md](AUTHELIA_OIDC_FRONTEND_DEVELOPER_GUIDE.md) - Frontend
- [AUTHELIA_OIDC_ADVANCED_SCENARIOS.md](AUTHELIA_OIDC_ADVANCED_SCENARIOS.md) - Advanced usage

---

## Knowledge Base Entries

### KB001: Browser Cache Issues

**Problem**: After update, old version still showing

**Solution**:
```
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Clear cache: Ctrl+Shift+Delete
3. Restart browser
4. Try incognito/private mode
```

**Prevention**: Browser automatically clears cache after 1 hour

---

### KB002: Token Expiration Logout

**Problem**: Logged out automatically without clicking logout

**Solution**:
- This is intentional for security
- Access token expires after 30 minutes
- You're logged out 1 minute before expiration
- Login again to continue

**Prevention**: Keep using app to refresh token

---

### KB003: OIDC vs Local Login Choice

**Problem**: How to decide between OIDC and local login?

**Solution**:
- **Use OIDC if**: Authelia account exists, prefer SSO
- **Use Local if**: No SSO account, prefer password
- **Both work**: Both methods access same account in hybrid mode

**Recommendation**: Use OIDC when available (more secure)

---

### KB004: Forgot Password with OIDC

**Problem**: Can't reset password with OIDC

**Solution**:
- OIDC doesn't use ParchMark passwords
- Password reset in Authelia (SSO provider)
- Contact your SSO administrator
- Or use local login if password-based account exists

---

### KB005: Multiple Device Sessions

**Problem**: Logged out on other device when logging in here

**Solution**:
- This is expected behavior
- Each device has its own session
- Token refreshes per device
- Can have multiple active sessions

**Note**: Future feature may allow simultaneous sessions

---

## Additional Resources

- **Docs Directory**: `/docs/AUTHELIA_OIDC_*.md`
- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs on GitHub
- **Community**: Ask in #engineering channel

---

## Last Updated

Updated: January 2025
Version: 1.0
Maintainer: Platform Team
