# Remote Dolt Server for Beads Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a shared Dolt SQL server on brahma (k3s) so all Claude Code instances connect to one beads database over Tailscale — eliminating the need for a local `dolt sql-server`.

**Architecture:** Dolt runs as a k3s Deployment with a PVC for persistence, exposed via NodePort on 3307. Beads clients (on any Tailscale-connected machine) connect to `brahma.myth-gecko.ts.net:3307`. Local brew dolt service is removed.

**Tech Stack:** Dolt (dolthub/dolt Docker image), k3s, Tailscale

---

## File Structure

| File | Purpose |
|-|-|
| `brahma:/root/manifests/dolt/dolt.yaml` | k3s manifest (PVC + Deployment + NodePort Service) |
| `.beads/config.yaml` (parchmark) | Update `server-host` to brahma |
| `.beads/metadata.json` (parchmark) | Updated by `bd dolt set` |

---

## Chunk 1: Deploy Dolt on brahma

### Task 1: Create k3s manifest for Dolt

**Files:**
- Create: `brahma:/root/manifests/dolt/dolt.yaml`

- [ ] **Step 1: Create the manifest directory on brahma**

```bash
ssh brahma "mkdir -p /root/manifests/dolt"
```

- [ ] **Step 2: Write the k3s manifest**

Write `dolt.yaml` to brahma with these resources:

```yaml
# =============================================================
# Dolt SQL Server - Shared beads database for all projects
# =============================================================
# Deploy: kubectl apply -f dolt.yaml
# Verify: kubectl get pods -l app=dolt
# Connect: mysql -h brahma.myth-gecko.ts.net -P 3307 -u root
# =============================================================
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dolt-data
  labels:
    app: dolt
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dolt
  labels:
    app: dolt
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: dolt
  template:
    metadata:
      labels:
        app: dolt
    spec:
      containers:
      - name: dolt
        image: dolthub/dolt-sql-server:latest
        args:
        - "-l"
        - "info"
        - "--port"
        - "3307"
        - "--host"
        - "0.0.0.0"
        ports:
        - name: mysql
          containerPort: 3307
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            memory: 512Mi
        volumeMounts:
        - name: data
          mountPath: /var/lib/dolt
        readinessProbe:
          tcpSocket:
            port: 3307
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          tcpSocket:
            port: 3307
          initialDelaySeconds: 15
          periodSeconds: 30
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: dolt-data
---
apiVersion: v1
kind: Service
metadata:
  name: dolt
  labels:
    app: dolt
spec:
  type: NodePort
  ports:
  - name: mysql
    port: 3307
    targetPort: 3307
    nodePort: 30307
  selector:
    app: dolt
```

Note: NodePort 30307 maps to container port 3307. Since brahma is only reachable via Tailscale, no auth needed.

- [ ] **Step 3: Deploy to k3s**

```bash
ssh brahma "kubectl apply -f /root/manifests/dolt/dolt.yaml"
```

- [ ] **Step 4: Wait for pod to be ready**

```bash
ssh brahma "kubectl rollout status deployment/dolt --timeout=60s"
```

Expected: `deployment "dolt" successfully rolled out`

- [ ] **Step 5: Verify dolt is reachable from brahma**

```bash
ssh brahma "kubectl get pods -l app=dolt -o wide"
```

Expected: 1/1 Running

### Task 2: Verify connectivity from local machine

- [ ] **Step 1: Test MySQL connection from local machine to brahma NodePort**

```bash
mysql -h brahma.myth-gecko.ts.net -P 30307 -u root -e "SELECT 1"
```

If `mysql` client not installed, use dolt:
```bash
dolt sql -q "SELECT 1" --host brahma.myth-gecko.ts.net --port 30307 --user root
```

Expected: Returns `1`

- [ ] **Step 2: Create beads_parchmark database on remote**

```bash
mysql -h brahma.myth-gecko.ts.net -P 30307 -u root -e "CREATE DATABASE IF NOT EXISTS beads_parchmark"
```

Or via dolt:
```bash
dolt sql -q "CREATE DATABASE IF NOT EXISTS beads_parchmark" --host brahma.myth-gecko.ts.net --port 30307 --user root
```

---

## Chunk 2: Migrate beads to remote and clean up local

### Task 3: Point parchmark beads at remote dolt

- [ ] **Step 1: Reconfigure beads to use remote server**

```bash
cd /Users/tej/src/parchmark
bd dolt set host brahma.myth-gecko.ts.net
bd dolt set port 30307
```

- [ ] **Step 2: Test beads connection**

```bash
bd dolt test
```

Expected: `✓ Server connection OK`

- [ ] **Step 3: Re-initialize beads against the remote database**

```bash
rm -rf .beads
bd init --prefix parchmark --server-host brahma.myth-gecko.ts.net --server-port 30307
```

- [ ] **Step 4: Verify beads works**

```bash
bd list
bd doctor 2>&1 | head -10
```

Expected: 0 errors, connection to remote server

- [ ] **Step 5: Commit .gitignore update**

```bash
git add .gitignore
git commit -m "chore: gitignore .beads directory"
```

### Task 4: Remove local dolt service

- [ ] **Step 1: Stop and remove brew dolt service**

```bash
brew services stop dolt
brew services unregister dolt  # or: launchctl remove homebrew.mxcl.dolt
```

- [ ] **Step 2: Clean up local dolt data**

```bash
rm -rf /opt/homebrew/var/dolt/beads_parchmark
rm -rf /opt/homebrew/var/dolt/beads_homelab-docs  # migrate this too, or leave if not using beads there
rm -rf ~/.dolt/dbs/
```

- [ ] **Step 3: Optionally uninstall dolt**

```bash
brew uninstall dolt
```

Only if no other use for dolt locally. Keep if you want the `dolt sql` client for debugging.

- [ ] **Step 4: Verify no local dolt running**

```bash
lsof -i :3307 -P 2>&1
```

Expected: No output (nothing listening)

### Task 5: Update AGENTS.md with remote dolt info

- [ ] **Step 1: Add a note about remote dolt to AGENTS.md**

In the beads/bd section, add context that the dolt server is remote:

```
Beads uses a remote Dolt server at brahma.myth-gecko.ts.net:30307 (Tailscale).
No local dolt sql-server needed. If `bd` can't connect, verify Tailscale is up.
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add remote dolt server info to AGENTS.md"
```

---

## Chunk 3: Configure other projects (optional)

### Task 6: Migrate homelab-docs beads to remote (if applicable)

- [ ] **Step 1: In the homelab-docs repo, reconfigure beads**

```bash
cd ~/src/homelab-docs  # or wherever it lives
bd dolt set host brahma.myth-gecko.ts.net
bd dolt set port 30307
bd dolt test
```

This task is optional — only needed if homelab-docs actively uses beads.

---

## Rollback

If the remote dolt causes issues:

1. `brew install dolt && brew services start dolt` (restarts local)
2. `bd dolt set host 127.0.0.1 && bd dolt set port 3307` (points beads back to local)
3. `ssh brahma "kubectl delete -f /root/manifests/dolt/dolt.yaml"` (removes remote)
