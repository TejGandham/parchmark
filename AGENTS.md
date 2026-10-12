Guidance for Claude Code working in the ParchMark meta repository — the repository root that holds ParchMark's projects side by side.

## What lives where

| Path | What it is |
|-|-|
| `parchmark-web/` | The web application: Vue 3 + TypeScript UI, FastAPI + PostgreSQL backend, Docker/compose deployment, its own Makefile and docs |
| `Makefile` | Delegating Makefile — every target runs `make -C parchmark-web <target>` |
| `.forgejo/workflows/` | CI: `test.yml` (tests) and `deploy.yml` (images → Forgejo registry → k3s) |
| `.claude/skills/` | Project skills (`parchmark-branch-setup`, `parchmark-land`, `parchmark-markdown-sync`, `migration-check`) |
| `.karta/` | Karta binder state for planned work; a build run never edits it |
| `.mcp.json` | MCP servers (PostgreSQL) |

Project docs live with their project: `parchmark-web/AGENTS.md` is the contributor guide for the web app, and `parchmark-web/docs/` holds the architecture, design, OIDC and deployment references.

## Commands

Run from the repository root; `make` forwards to the project Makefile, so `make test` here is `make -C parchmark-web test`. The same targets work from inside `parchmark-web/`.

```bash
make dev              # PostgreSQL + backend (localhost:8000) + frontend (localhost:5173)
make test             # full CI pipeline: UI lint + tests, backend lint + format + types + pytest
make help             # every target (forwarded from parchmark-web/Makefile)
```

Requirements: Node 24, Python 3.14 with [uv](https://docs.astral.sh/uv/), and Docker for the compose-based dev environment (PostgreSQL runs in a container).

## Feature & Bug Workflow

The repository is the unit of review: branch from this root, and one PR covers the change even when it spans `parchmark-web/` and the root tooling.

**Every feature or bug fix MUST use a new branch. No exceptions.**

> **Docs-only exception:** If the change touches **only markdown / documentation files** and no code (`.ts`, `.tsx`, `.js`, `.py`, `.yml`, `.json`, etc.), you still need a branch + PR — the Forgejo pre-receive hook rejects direct pushes to `main`, docs included — but you may self-merge the PR as soon as CI is green, no review needed. The moment any code file is touched, the full branch + PR + CI workflow applies.

1. `git checkout main && git pull origin main && git checkout -b feat/<short-description>` (or `fix/…`) — branch off `main`, never commit to it. `.worktrees/<branch>` is gitignored if you want isolation.
2. Implement, then run `make test` from this root.
3. Push and open a PR with `tea`:

```bash
git push -u origin <branch-name>
tea pr create --title "PR title" --description "## Summary ..." --base main --head <branch-name>
tea pr view <number>           # check CI status
tea pr merge -s merge <number> # merge after CI passes
```

Use `tea` for all Forgejo PR management. Do **not** use `gh` (GitHub only) or raw `curl`.

4. **Work is NOT complete until CI is green on the PR.** If CI fails, fix on the branch, push again, wait for green.
5. After merge, delete the local branch and remove any worktree you added.

## Gotchas

- **Path prefixes.** A path in `parchmark-web/` docs is relative to `parchmark-web/`. From the root, spell it out (`parchmark-web/backend/app/…`).
- **CI paths are root-relative.** Workflows and `parchmark-web/backend/.pre-commit-config.yaml` resolve against the repository root, not the project directory.
- **Git remotes.** `origin` = Forgejo on brahma (`brahma.myth-gecko.ts.net:3000`) — the only remote developers push to; it hosts CI and deploy. GitHub (`github.com/TejGandham/parchmark`) is a read-only offsite backup mirror, populated by automated sync — no local remote is configured and developers never push to it manually.
- **Landing a session.** `git push` must succeed and CI must go green; the `parchmark-land` skill automates that sequence.
