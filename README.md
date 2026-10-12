# ParchMark

Meta repository for ParchMark — the app and its supporting projects live side by side here.

| Path | What it is |
|-|-|
| [`parchmark-web/`](parchmark-web/AGENTS.md) | The web application: Vue 3 + TypeScript frontend, FastAPI + PostgreSQL backend, Docker images |
| `Makefile` | Delegating Makefile: every target runs `make -C parchmark-web <target>` |
| `.forgejo/workflows/` | CI: tests, then image build + deploy to k3s on `main` |
| `.karta/` | Karta binder state for planned work |
| `.claude/skills/` | Project skills for agent sessions |

## Run it

You need Node 24, Python 3.14 with [uv](https://docs.astral.sh/uv/), and Docker (PostgreSQL runs in a container; no local install).

```bash
make dev     # PostgreSQL + backend (localhost:8000) + frontend (localhost:5173)
make test    # full CI pipeline: UI lint + tests, backend lint + format + types + pytest
make help    # every other target: user management, deploys, migrations
```

Log in with a seeded dev user — see `parchmark-web/backend/app/database/seed.py`. While the backend runs, the API is documented at `localhost:8000/docs`.

## Documentation

| Doc | What it covers |
|-|-|
| [AGENTS.md](AGENTS.md) | Contributor guide for this meta repository: layout, workflow, CI |
| [parchmark-web/AGENTS.md](parchmark-web/AGENTS.md) | Web app guide: commands, testing, gotchas |
| [parchmark-web/docs/ARCHITECTURE.md](parchmark-web/docs/ARCHITECTURE.md) | Domain and layer maps, dependency rules |
| [parchmark-web/docs/design-docs/index.md](parchmark-web/docs/design-docs/index.md) | Core beliefs, UI design, code patterns, design context |
| [parchmark-web/docs/PRODUCTION_DEPLOYMENT.md](parchmark-web/docs/PRODUCTION_DEPLOYMENT.md) | Deployment runbook |
| [parchmark-web/docs/AUTHELIA_OIDC.md](parchmark-web/docs/AUTHELIA_OIDC.md) | OIDC (Authelia) setup and local testing |
| [parchmark-web/docs/exec-plans/tech-debt-tracker.md](parchmark-web/docs/exec-plans/tech-debt-tracker.md) | Known debt and open decisions |

## Production

The app runs at <https://notes.engen.tech>; the API is served same-origin under `/api`. Interactive API docs are not publicly exposed in production.

## Contributing

Development happens on Forgejo (`origin`); `github.com/TejGandham/parchmark` is a read-only mirror — don't open PRs there. Branch off `main` from this root, run `make test`, and open a PR with `tea`. Details in [AGENTS.md](AGENTS.md).
