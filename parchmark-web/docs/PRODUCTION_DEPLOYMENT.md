# ParchMark Production Deployment Runbook

How ParchMark is deployed, verified, rolled back, and maintained in production.

## Topology

| Piece | Where |
|-|-|
| Frontend | `https://notes.engen.tech` (Vue 3 app behind Nginx, k3s Deployment `parchmark-frontend`) |
| Backend API | Same origin, under `https://notes.engen.tech/api/*` (FastAPI, k3s Deployment `parchmark-backend`) |
| Artifact content | A separate host (the content origin) that routes only `/a/*` to `parchmark-backend`; see [Artifact Content Origin](#artifact-content-origin) |
| API docs | Not publicly exposed via production ingress |
| Images | Forgejo container registry (`forgejo.default.svc.cluster.local:3000/stackhouse`), tagged `latest` and `sha-<short-sha>` |
| Database | PostgreSQL, in-cluster |

The k3s manifests (Deployments, ingress, secrets) live **outside this repo** — this repo ships only the images and the CI that builds them.

## How a Deploy Happens

Every push to `main` on Forgejo triggers two workflows (`.forgejo/workflows/` at the repository root):

1. `test.yml` — full UI + backend quality gates.
2. `deploy.yml` — builds the backend (`backend/Dockerfile.prod`) and frontend (`ui/Dockerfile`) images with `GIT_SHA`/`BUILD_DATE` build args, pushes both tags to the Forgejo registry, then runs `kubectl rollout restart` on both Deployments and waits for rollout status. The final CI step curls `http://localhost:8000/health` inside the backend pod.

There is no manual deploy step: merging to `main` is the deploy.

## Verifying a Deploy

```bash
make deploy-verify          # curls prod /api/health + frontend /
```

Two health endpoints exist, on purpose:

- `GET /api/health` — public; checks DB connectivity and returns version info (`gitSha` shows the live commit — use it to confirm which build is serving).
- `GET /health` — liveness only (no DB); used by CI's in-pod verify step.

## Migrations

Alembic migrations run automatically on backend container startup when `APPLY_MIGRATIONS=true` (the entrypoint default is `false`, so extra replicas can skip them). Test migrations locally before merging: `cd backend && uv run alembic upgrade head`. Downgrades may fail if data violates constraints — treat rollback of a schema change as its own operation, not a given.

## Rollback

CI tags every image `sha-<short-sha>` in the Forgejo registry, so rollback is repinning, not rebuilding: point the k3s Deployment's image at the desired `sha-` tag (e.g. `kubectl set image`) and let it roll out. Confirm with `/api/health`'s `gitSha`. Reverting the offending commit on `main` also works and leaves history cleaner.

## Environment Configuration

Runtime env is supplied by the k3s manifests/secrets, not by files in this repo. The backend expects:

```env
DATABASE_URL=postgresql://parchmark_user:<password>@<db-host>:5432/parchmark_db
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://notes.engen.tech
ARTIFACT_CONTENT_ORIGIN=https://<content-host>   # required: the backend refuses to start without it
ARTIFACT_SIGNING_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(32))">   # required: never SECRET_KEY
APPLY_MIGRATIONS=true
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark
OIDC_OPAQUE_TOKEN_PREFIX=           # optional: restrict opaque token format (e.g. "authelia_at_")
OIDC_DISCOVERY_URL=                 # optional: separate discovery URL (e.g. internal cluster DNS)
OIDC_USERNAME_CLAIM=preferred_username
```

The frontend is built with `VITE_API_URL=/api`, so all API calls stay same-origin and Nginx in the frontend image proxies them to the backend. Never commit secrets; rotate `SECRET_KEY` and the DB password periodically (rotating `SECRET_KEY` invalidates all outstanding local JWTs).

## Artifact Content Origin

Published artifacts are untrusted HTML, SVG and Markdown. They are served by the backend's public `GET /a/{slug}` route, and that route must be reachable **only from its own host**, never from `notes.engen.tech` (whose Nginx forwards only `/api/`, so `/a/` there falls through to the SPA).

The content origin needs one ingress rule in the out-of-repo k3s manifests, with TLS:

- Host: a dedicated name, preferably on a registrable domain other than `engen.tech`, so no cookie scoped to `engen.tech` (for example an SSO session) is ever sent to it.
- Path: prefix `/a/` → service `parchmark-backend`, port 8000. Route nothing else; `/api` stays on the app host.

Set `ARTIFACT_CONTENT_ORIGIN` to the scheme plus the content host (for example `https://<content-host>`, no path) in the out-of-repo k3s secret for `parchmark-backend` before deploying; the backend refuses to start without it, and it builds every artifact's `share_url` from it. The isolation comes from the response itself: every `/a/` response carries a Content-Security-Policy with a `sandbox` directive, so even a share link opened directly runs in an opaque origin with no network access (policy details in [ARCHITECTURE.md](ARCHITECTURE.md#artifact-content-isolation)). Check it after a deploy with an unlisted artifact's slug:

```bash
curl -s -o /dev/null -D - https://<content-host>/a/<slug> | grep -i -e content-type -e content-security-policy -e set-cookie
```

Expect the artifact's media type, a policy containing `sandbox`, and no `set-cookie`.

Set `ARTIFACT_SIGNING_KEY` in the same out-of-repo k3s secret: a new random value of at least 32 characters, generated for this purpose and never `SECRET_KEY`. The backend refuses to start when it is missing, shorter than 32 characters, or equal to `SECRET_KEY`. It signs the five-minute view links through which the web viewer shows private artifacts; rotating it only invalidates links already handed out.

## User Management

Local (non-OIDC) users are managed with `backend/scripts/manage_users.py`, run inside the backend container (image workdir is `/app`):

```bash
kubectl exec deploy/parchmark-backend -- python scripts/manage_users.py list
kubectl exec deploy/parchmark-backend -- python scripts/manage_users.py create <username> '<password>'
kubectl exec deploy/parchmark-backend -- python scripts/manage_users.py update-password <username> '<new-password>'
kubectl exec deploy/parchmark-backend -- python scripts/manage_users.py delete <username>
```

## Backups

Back up the database with `pg_dump` wherever prod PostgreSQL runs (in-cluster pod):

```bash
# Backup
kubectl exec <postgres-pod> -- pg_dump -U parchmark_user parchmark_db | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup-YYYYMMDD.sql.gz | kubectl exec -i <postgres-pod> -- psql -U parchmark_user parchmark_db
```

## Legacy Artifacts

`docker-compose.prod.yml`, `deploy/update.sh`, and the SSH-based `make deploy-*` targets date from the retired docker-compose-on-VPS deploy (GHCR images behind Nginx Proxy Manager). They are not the live deploy path — do not follow them for production changes.
