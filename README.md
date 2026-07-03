# ParchMark

A full-stack markdown note-taking app: Vue 3 + TypeScript frontend, FastAPI + PostgreSQL backend, deployed to k3s by Forgejo CI.

## Run it

You need Node 24, Python 3.14 with [uv](https://docs.astral.sh/uv/), and Docker (PostgreSQL runs in a container; no local install).

```bash
make dev     # PostgreSQL + backend (localhost:8000) + frontend (localhost:5173)
make help    # every other target: tests, user management, deploys
```

Log in with a seeded dev user — see `backend/app/database/seed.py`. While the backend runs, the API is documented at `localhost:8000/docs`.

## Documentation

| Doc | What it covers |
|-|-|
| [AGENTS.md](AGENTS.md) | Contributor guide: workflow, commands, testing, gotchas |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Domain and layer maps, dependency rules |
| [docs/design-docs/index.md](docs/design-docs/index.md) | Core beliefs, UI design, code patterns, design context |
| [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) | Deployment runbook |
| [docs/AUTHELIA_OIDC.md](docs/AUTHELIA_OIDC.md) | OIDC (Authelia) setup and local testing |
| [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) | Known debt and open decisions |

## Production

The app runs at <https://notes.engen.tech>; the API is served same-origin under `/api`. Interactive API docs are not publicly exposed in production.

## Contributing

Development happens on Forgejo (`origin`); `github.com/TejGandham/parchmark` is a read-only mirror — don't open PRs there. Branch off `main`, run `make test`, and open a PR with `tea`. Details in [AGENTS.md](AGENTS.md).
