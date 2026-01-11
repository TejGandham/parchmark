# Archived Deployment Documentation

**Archived on:** January 2026

## Why These Are Archived

These documents describe a **planned automated deployment system** using GitHub Actions + SSH/Tailscale that was designed but **never fully implemented**. The actual deployment process uses:

1. **GitHub Actions** - Builds and pushes Docker images to GHCR (this part works)
2. **Manual SSH deployment** - Admin manually pulls images and restarts containers

The planned SSH-based automated deployment from GitHub Actions was not configured.

## Current Documentation

For the **actual deployment process**, see:
- `/PRODUCTION_DEPLOYMENT.md` - Comprehensive production deployment guide

## What's Archived Here

| File | Description |
|------|-------------|
| `DEPLOYMENT.md` | Watchtower-based auto-deployment (rejected approach) |
| `DEPLOYMENT_VALIDATED.md` | GitHub Actions + SSH deployment (planned, not implemented) |
| `DEPLOYMENT_PROGRESS.md` | Progress tracker for the planned system |
| `PHASE3_SERVER_SETUP.md` | Server setup for SSH deployment (not used) |
| `PHASE4_GITHUB_SECRETS.md` | GitHub secrets config (partially used - GHCR works) |
| `phase3_server_commands.sh` | Server setup commands (not used) |
| `FUTURE_IMPROVEMENTS.md` | Future security enhancements (still relevant for reference) |
| `TAILSCALE_SETUP.md` | Tailscale VPN setup for deployment (not implemented) |
| `ACL_CHANGES.md` | Tailscale ACL configuration (not implemented) |
| `TROUBLESHOOTING.md` | Troubleshooting for planned system (not applicable) |

## Historical Context

These documents represent extensive planning and research into deployment options:

1. **Watchtower approach** - Rejected due to being unmaintained and having config drift issues
2. **What's Up Docker (WUD)** - Rejected as better suited for homelabs  
3. **GitHub Actions + SSH** - Chosen but not fully implemented
4. **Tailscale VPN** - Explored for secure deployment, not implemented

The current manual process works well for the scale of this project.

## Should We Implement Automated Deployment?

If automated deployment becomes necessary in the future, these documents provide a solid foundation. Key decisions already made:

- Use GitHub Actions (not Watchtower/WUD)
- Use SSH for deployment (not Tailscale for now)
- Use GHCR for image storage
- Use manual approval for production deployments

The `FUTURE_IMPROVEMENTS.md` contains a roadmap for security enhancements that would apply to any automated deployment implementation.
