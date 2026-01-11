# GitHub Actions Workflow - Future Improvements

**Last Updated**: 2025-10-26
**Expert Validation**: GPT-5 Pro (2025 DevSecOps Standards)
**Current State**: Production-ready (9/10 security score)

---

## Overview

This document outlines recommended improvements to the GitHub Actions deployment workflow based on expert validation from GPT-5 Pro. These improvements follow 2025 DevSecOps best practices for supply-chain security, reliability, and maintainability.

**Current Status**:
- ✅ **Phase 1 Applied**: Enhanced error handling and health checks
- 📋 **Phase 2 Pending**: Supply-chain security hardening
- 📋 **Phase 3 Pending**: Advanced security features (optional)

---

## Priority 1: Supply-Chain Security Hardening

**Impact**: High
**Complexity**: Low to Medium
**Time Required**: 30-60 minutes
**Security Score Improvement**: 9/10 → 10/10

### 1. Pin Actions to Commit SHAs

**Current State**:
```yaml
uses: actions/checkout@v4
uses: docker/setup-buildx-action@v3
uses: docker/login-action@v3
uses: docker/metadata-action@v5
uses: docker/build-push-action@v5
```

**Recommended State**:
```yaml
# Pin to specific commit SHAs for supply-chain security
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
uses: docker/setup-buildx-action@f95db51fddba0c2d1ec667646a06c2ce06100226  # v3.0.0
uses: docker/login-action@343f7c4344506bcbf9b4de18042ae17996df046d  # v3.0.0
uses: docker/metadata-action@96383f45573cb7f253c731d3b3ab81c87ef81934  # v5.0.0
uses: docker/build-push-action@0565240e2d4ab88bba5387d719585280857ece09  # v5.0.0
```

**Why This Matters**:
- Major version tags (like `@v4`) can be moved by compromised maintainers
- Commit SHAs are immutable - once committed, they cannot be changed
- Prevents supply-chain attacks via compromised GitHub Actions

**How to Get Commit SHAs**:

1. **Visit the action's GitHub releases page**:
   - Example: https://github.com/actions/checkout/releases

2. **Find the latest stable release** (e.g., v4.1.1)

3. **Click on the commit SHA** shown next to the tag

4. **Copy the full 40-character SHA** from the URL

5. **Replace in workflow**:
   ```yaml
   # Instead of:
   uses: actions/checkout@v4

   # Use:
   uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
   ```

**Maintenance with Dependabot**:

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "github-actions"
```

**Benefits**:
- ✅ Automatic pull requests to update pinned SHAs
- ✅ Review changes before merging
- ✅ Maintain security without manual tracking

**Action Items**:
1. [ ] Pin all 5 Docker actions to commit SHAs
2. [ ] Keep `appleboy/ssh-action@v1.2.2` as-is (specific version already)
3. [ ] Create `.github/dependabot.yml` for automatic updates
4. [ ] Document SHA update process for team

---

### 2. Add SSH Host Key Verification

**Current State**:
```yaml
- name: Deploy via SSH
  uses: appleboy/ssh-action@v1.2.2
  with:
    host: ${{ secrets.PROD_HOST }}
    username: ${{ secrets.PROD_USER }}
    key: ${{ secrets.PROD_SSH_KEY }}
    script_stop: true
```

**Recommended State**:
```yaml
- name: Deploy via SSH
  uses: appleboy/ssh-action@v1.2.2
  with:
    host: ${{ secrets.PROD_HOST }}
    username: ${{ secrets.PROD_USER }}
    key: ${{ secrets.PROD_SSH_KEY }}
    host_fingerprint: ${{ secrets.SSH_HOST_FINGERPRINT }}  # ADD THIS
    script_stop: true
```

**Why This Matters**:
- Prevents Man-in-the-Middle (MITM) attacks
- Verifies you're connecting to the correct server
- Default SSH behavior accepts unknown hosts (security risk)

**How to Get Host Fingerprint**:

**On your local machine**:
```bash
# Get the SHA256 fingerprint
ssh-keyscan notes.engen.tech 2>/dev/null | ssh-keygen -lf - -E sha256

# Output example:
# 256 SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8 notes.engen.tech (ED25519)

# Copy the SHA256 part (after "SHA256:")
# nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
```

**Add to GitHub Secrets**:
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SSH_HOST_FINGERPRINT`
4. Value: `nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8` (your actual fingerprint)
5. Click "Add secret"

**Action Items**:
1. [ ] Generate host fingerprint for `notes.engen.tech`
2. [ ] Add `SSH_HOST_FINGERPRINT` to GitHub Secrets
3. [ ] Update workflow to include `host_fingerprint` parameter
4. [ ] Test deployment with verification enabled
5. [ ] Document fingerprint rotation process

**Security Note**: Update the fingerprint if you:
- Migrate to a different server
- Reinstall SSH on the server
- Change server keys for security rotation

---

### 3. Add Job-Level Permissions (Least Privilege)

**Current State**:
```yaml
# Global permissions (applies to all jobs)
permissions:
  contents: read
  packages: write
```

**Recommended State**:
```yaml
# Default: no permissions
permissions: {}

jobs:
  build-and-push-backend:
    permissions:
      contents: read      # Read repository code
      packages: write     # Push to GHCR
    steps:
      # ...

  build-and-push-frontend:
    permissions:
      contents: read      # Read repository code
      packages: write     # Push to GHCR
    steps:
      # ...

  deploy-to-production:
    permissions:
      contents: read      # No package write needed
    steps:
      # ...

  notify-deployment:
    permissions: {}       # No permissions needed
    steps:
      # ...
```

**Why This Matters**:
- Follows principle of least privilege
- Limits blast radius if a job is compromised
- Deploy job doesn't need to write packages
- Notification job doesn't need any permissions

**Action Items**:
1. [ ] Remove global `permissions` block
2. [ ] Add `permissions: {}` as global default
3. [ ] Add job-specific permissions for build jobs
4. [ ] Test that deploy job works without `packages: write`
5. [ ] Verify notification job works with no permissions

---

### 4. Add Deployment Concurrency Control

**Current State**: Multiple deployments can run simultaneously

**Recommended State**:
```yaml
deploy-to-production:
  needs: [build-and-push-backend, build-and-push-frontend]
  runs-on: ubuntu-latest
  name: Deploy to Production
  environment: production

  # ADD THIS BLOCK
  concurrency:
    group: production-deployment
    cancel-in-progress: false  # Wait for current deployment to finish

  steps:
    # ...
```

**Why This Matters**:
- Prevents race conditions from simultaneous deployments
- Ensures deployments happen in order
- Avoids corrupted state from overlapping updates
- Single source of truth for current production state

**Behavior**:
- If deployment A is running and deployment B is triggered:
  - Deployment B will **wait** until A completes
  - Deployment B will then proceed
  - No deployments are cancelled

**Action Items**:
1. [ ] Add `concurrency` block to deploy job
2. [ ] Test behavior with rapid successive commits
3. [ ] Verify queued deployments execute in order
4. [ ] Document expected behavior for team

---

## Priority 2: Advanced Security Features (Optional)

**Impact**: Medium to High
**Complexity**: Medium to High
**Time Required**: 2-4 hours
**When to Implement**: After initial deployment success

### 5. Enable SBOM & Provenance

**Software Bill of Materials (SBOM)** - Lists all dependencies in your images
**Provenance** - Cryptographic proof of how images were built

**Implementation**:
```yaml
- name: Build and push backend image
  uses: docker/build-push-action@v5
  with:
    context: ./backend
    file: ./backend/Dockerfile.prod
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}

    # ADD THESE
    sbom: true                    # Generate SBOM
    provenance: mode=max          # Maximum provenance detail

    cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend:buildcache
    cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend:buildcache,mode=max
```

**Benefits**:
- ✅ Compliance readiness (SOC2, ISO 27001)
- ✅ Dependency tracking for security audits
- ✅ Supply-chain transparency
- ✅ Verify image authenticity

**Action Items**:
1. [ ] Add `sbom: true` to both build jobs
2. [ ] Add `provenance: mode=max` to both build jobs
3. [ ] Test SBOM generation (view in GHCR)
4. [ ] Document how to inspect SBOM/provenance

**How to View SBOM**:
```bash
# Install cosign
brew install cosign  # macOS
# OR
wget https://github.com/sigstore/cosign/releases/download/v2.2.0/cosign-linux-amd64

# View SBOM
cosign download sbom ghcr.io/tejgandham/parchmark-backend:latest

# View provenance
cosign download attestation ghcr.io/tejgandham/parchmark-backend:latest
```

---

### 6. Image Signing with Cosign

**What**: Cryptographically sign Docker images to verify authenticity

**Implementation**:

**Add signing step** (after build-push):
```yaml
- name: Install cosign
  uses: sigstore/cosign-installer@v3

- name: Sign backend image
  env:
    COSIGN_EXPERIMENTAL: "true"
  run: |
    # Sign with keyless signing (OIDC)
    cosign sign --yes \
      ghcr.io/tejgandham/parchmark-backend:${{ github.sha }}
```

**Add verification on server** (in deployment script):
```bash
# Before: docker compose up
# After: verify signatures first

echo "🔐 Verifying image signatures..."
cosign verify \
  --certificate-identity-regexp="https://github.com/TejGandham/parchmark/.*" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  ghcr.io/tejgandham/parchmark-backend:latest

cosign verify \
  --certificate-identity-regexp="https://github.com/TejGandham/parchmark/.*" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  ghcr.io/tejgandham/parchmark-frontend:latest

# Then proceed with deployment
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

**Benefits**:
- ✅ Guarantees images haven't been tampered with
- ✅ Verifies images came from your GitHub Actions
- ✅ Prevents deployment of malicious images
- ✅ Meets compliance requirements

**Prerequisites**:
1. Install `cosign` on production server:
   ```bash
   ssh deploy@notes.engen.tech
   wget https://github.com/sigstore/cosign/releases/download/v2.2.0/cosign-linux-amd64
   sudo mv cosign-linux-amd64 /usr/local/bin/cosign
   sudo chmod +x /usr/local/bin/cosign
   ```

**Action Items**:
1. [ ] Add cosign-installer step to workflow
2. [ ] Add image signing for both images
3. [ ] Install cosign on production server
4. [ ] Add signature verification to deployment script
5. [ ] Test end-to-end signing and verification
6. [ ] Document signature verification for team

---

### 7. Vulnerability Scanning with Trivy

**What**: Scan Docker images for known security vulnerabilities (CVEs)

**Implementation**:

**Add scanning step** (after build, before push):
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.GITHUB_USERNAME }}/parchmark-backend:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail build on high/critical vulnerabilities

- name: Upload Trivy results to GitHub Security
  uses: github/codeql-action/upload-sarif@v2
  if: always()
  with:
    sarif_file: 'trivy-results.sarif'
```

**Configuration Options**:
```yaml
# Strict mode (fail on high/critical)
exit-code: '1'
severity: 'CRITICAL,HIGH'

# Permissive mode (warn only)
exit-code: '0'
severity: 'CRITICAL,HIGH,MEDIUM,LOW'
```

**Benefits**:
- ✅ Detect vulnerabilities before deployment
- ✅ GitHub Security tab integration
- ✅ Automated CVE tracking
- ✅ Compliance requirements (PCI-DSS, HIPAA)

**Action Items**:
1. [ ] Add Trivy scanning for both images
2. [ ] Configure severity thresholds
3. [ ] Set up GitHub Security integration
4. [ ] Create allowlist for accepted CVEs (if needed)
5. [ ] Document vulnerability response process

**Example Allowlist** (`.trivyignore`):
```
# PostgreSQL base image CVE - accepted risk
CVE-2023-12345

# Python vulnerability - fixed in next release
CVE-2024-67890
```

---

## Priority 3: Enhanced Deployment Safety

**Impact**: Medium
**Complexity**: Medium
**Time Required**: 1-2 hours

### 8. Deploy Using Image Digests

**Current**: Deploy using `:latest` or `:sha-xxxxx` tags
**Recommended**: Deploy using immutable digests

**Why This Matters**:
- Tags can be overwritten (even SHA tags theoretically)
- Digests are truly immutable
- Guarantees exact image version

**Implementation**:

**Capture digest in build job**:
```yaml
- name: Build and push backend image
  id: build
  uses: docker/build-push-action@v5
  with:
    # ... existing config ...

- name: Export image digest
  run: |
    echo "BACKEND_DIGEST=${{ steps.build.outputs.digest }}" >> $GITHUB_OUTPUT
```

**Pass digest to deploy job**:
```yaml
deploy-to-production:
  needs: [build-and-push-backend, build-and-push-frontend]
  steps:
    - name: Deploy via SSH
      env:
        BACKEND_DIGEST: ${{ needs.build-and-push-backend.outputs.digest }}
        FRONTEND_DIGEST: ${{ needs.build-and-push-frontend.outputs.digest }}
      with:
        script: |
          # Pull by digest (immutable)
          docker pull ghcr.io/tejgandham/parchmark-backend@${BACKEND_DIGEST}
          docker pull ghcr.io/tejgandham/parchmark-frontend@${FRONTEND_DIGEST}

          # Tag for docker-compose
          docker tag ghcr.io/tejgandham/parchmark-backend@${BACKEND_DIGEST} \
            ghcr.io/tejgandham/parchmark-backend:latest

          # Deploy
          docker compose -f docker-compose.prod.yml up -d
```

**Action Items**:
1. [ ] Capture image digests in build jobs
2. [ ] Pass digests to deployment job
3. [ ] Update deployment script to use digests
4. [ ] Record digests in deployment summary
5. [ ] Test digest-based deployment

---

### 9. Automatic Rollback on Health Check Failure

**Current**: Deployment fails, but bad version remains deployed
**Recommended**: Automatically rollback to previous version on failure

**Implementation**:

**Track previous deployment**:
```bash
# Before deployment
echo "📝 Recording current deployment..."
PREVIOUS_BACKEND=$(docker inspect parchmark-backend --format='{{.Image}}')
PREVIOUS_FRONTEND=$(docker inspect parchmark-frontend --format='{{.Image}}')

# Deployment attempt
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# Health checks
if ! curl -f -s --retry 12 https://assets-api.engen.tech/api/health; then
  echo "❌ Health check failed - rolling back..."

  # Rollback to previous images
  docker tag $PREVIOUS_BACKEND ghcr.io/tejgandham/parchmark-backend:latest
  docker tag $PREVIOUS_FRONTEND ghcr.io/tejgandham/parchmark-frontend:latest

  docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

  # Verify rollback succeeded
  curl -f -s --retry 5 https://assets-api.engen.tech/api/health || {
    echo "❌ Rollback also failed - manual intervention required!"
    exit 1
  }

  echo "✅ Rollback successful"
  exit 1
fi
```

**Action Items**:
1. [ ] Add previous image tracking
2. [ ] Implement rollback logic
3. [ ] Test rollback scenario
4. [ ] Add alerts for failed deployments
5. [ ] Document manual recovery process

---

## Implementation Timeline

### Immediate (This Week)
- [x] Enhanced error handling ✅ **COMPLETED**
- [x] Strengthened health checks ✅ **COMPLETED**
- [ ] SSH host key verification (5 minutes)

### Short-Term (Next 2 Weeks)
- [ ] Pin actions to commit SHAs (30 minutes)
- [ ] Setup Dependabot (5 minutes)
- [ ] Job-level permissions (15 minutes)
- [ ] Deployment concurrency control (5 minutes)

### Medium-Term (Next Month)
- [ ] SBOM & Provenance (30 minutes)
- [ ] Image digest deployment (1 hour)
- [ ] Automatic rollback (1 hour)

### Long-Term (As Needed)
- [ ] Image signing with Cosign (2 hours)
- [ ] Vulnerability scanning with Trivy (1 hour)
- [ ] Blue-green deployment (4+ hours)

---

## Success Metrics

**Current Security Score**: 9/10
**Target Security Score**: 10/10

| Improvement | Security Impact | Effort | Status |
|-------------|----------------|--------|--------|
| Enhanced error handling | High | Low | ✅ Complete |
| Strengthened health checks | High | Low | ✅ Complete |
| SSH host key verification | High | Low | 📋 Pending |
| Pin actions to commit SHAs | High | Low | 📋 Pending |
| Job-level permissions | Medium | Low | 📋 Pending |
| Concurrency control | Medium | Low | 📋 Pending |
| SBOM & Provenance | Medium | Low | 📋 Optional |
| Image signing | High | Medium | 📋 Optional |
| Vulnerability scanning | High | Medium | 📋 Optional |
| Digest deployment | Medium | Medium | 📋 Optional |
| Automatic rollback | High | Medium | 📋 Optional |

---

## Resources

### Documentation
- **GitHub Actions Security**: https://docs.github.com/en/actions/security-guides
- **Dependabot**: https://docs.github.com/en/code-security/dependabot
- **Cosign**: https://docs.sigstore.dev/cosign/overview
- **Trivy**: https://aquasecurity.github.io/trivy/

### Tools
- **Cosign**: https://github.com/sigstore/cosign
- **Trivy**: https://github.com/aquasecurity/trivy
- **Docker Buildx**: https://github.com/docker/buildx

### Best Practices
- **SLSA Framework**: https://slsa.dev/
- **NIST Supply Chain**: https://csrc.nist.gov/projects/supply-chain-risk-management
- **CIS Docker Benchmark**: https://www.cisecurity.org/benchmark/docker

---

## Notes

- All improvements are **optional enhancements** to an already production-ready workflow
- Implement based on your security requirements and risk tolerance
- Some features (SBOM, image signing) may be required for compliance (SOC2, ISO 27001)
- Start with high-impact, low-effort improvements first
- Test each improvement in a non-production environment first

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Validated By**: GPT-5 Pro (2025 DevSecOps Standards)
**Next Review**: After Phase 6 completion
