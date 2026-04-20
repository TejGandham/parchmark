# North Star: KEEL



KEEL — Knowledge-Encoded Engineering Lifecycle.
Adapted from [OpenAI's harness engineering article](https://openai.com/index/harness-engineering/).
This document defines where we're heading — not where we are today.

## The Principle

Humans steer. Claude executes. The repo is Claude's workspace, context, and
system of record. Everything Claude needs to make decisions lives here.

## What We Adopt (Fully)

**Repository = system of record.** If it's not in the repo, it doesn't exist
to Claude. Slack discussions, verbal decisions, tacit knowledge — all must be
encoded as markdown, code, or config in this repo.

**CLAUDE.md as table of contents.** ~80 lines, pointers to deeper docs. Not an
encyclopedia. Teaches Claude what this project is and where to look next.

**Progressive disclosure.** CLAUDE.md → ARCHITECTURE.md → specs → plans.
Claude reads what it needs when it needs it.

**Plans as first-class artifacts.** Active plans in `exec-plans/active/`,
completed plans in `exec-plans/completed/`. Progress and decisions logged
in the plan itself.

**Agent legibility is the goal.** Docs are written for Claude's comprehension,
not for a human audience. Clear, scannable, with explicit cross-references.

## What We Adapt (Scaled Down)

**Mechanical enforcement.** Three layers already wired:
1. Formatters as PostToolUse hooks (`ruff format` / `ruff check --fix` for
   Python; `prettier` for TS). Runs on every Edit/Write.
2. Test suites gate every PR via Forgejo CI (`make test` = UI lint+test +
   backend lint+format+types+pytest, 90% coverage floor both sides).
3. Domain-invariant grep rules via the `safety-auditor` agent and the
   PreToolUse `safety-gate` hook. Critical-file edits surface a reminder
   to run `/safety-check`; the auditor is a hard gate in `/keel-pipeline`.

**Garbage collection.** Manual at session boundaries today — the
`parchmark-land` skill includes a "docs still accurate?" prompt, and the
`doc-gate` PostToolUse hook reminds after commits. The `doc-gardener`
agent can be invoked explicitly for a repo-wide drift sweep; scheduling
it automatically is a Post-MVP item (see tech-debt-tracker).

**Agent review loops.** `/keel-pipeline` runs pre-check → test-writer
→ implementer → code-reviewer → spec-reviewer → safety-auditor →
landing-verifier. Roundtable (`challenge` / `hivemind`) is available as
a secondary review pass for invariant changes or architecture-tier
features — not every feature needs multi-model consensus, but anything
that amends the nine invariants or changes a layer boundary should get
one.

**Observability stack.** Backend logs to stdout/stderr via FastAPI's
default logger; k3s aggregates via `kubectl logs`. No structured logging
or metrics pipeline yet — added when we need per-user latency
attribution or SLO tracking (likely once self-hosters start reporting
OIDC edge cases).

## What We Skip (For Now)

- **Structured logging / metrics pipeline.** Stdout is enough until we
  hit a debuggability wall. Adding OpenTelemetry would be premature
  before we have real users asking us to reproduce incidents.
- **Schema-change CI gates.** Alembic migrations are hand-reviewed today;
  automating reversibility checks is deferred until we've broken at
  least one downgrade and felt the pain.
- **Per-user rate limiting.** The product is single-tenant-per-install
  or small-team self-hosted; rate limits matter when we run a
  multi-tenant SaaS, which is not the current deployment shape.

## Target Folder Structure (Fully Realized)

```
CLAUDE.md                           # ~80 lines, table of contents
ARCHITECTURE.md                     # Process model, layers, module map
Dockerfile                          # Dev container
docker-compose.yml                  # Orchestration

docs/
├── north-star.md                   # This document
├── product-specs/
│   └── [YOUR-SPEC].md
├── design-docs/
│   ├── core-beliefs.md             # Golden principles + testing strategy
│   └── [DESIGN-DOCS].md
├── exec-plans/
│   ├── active/                     # Plans being executed
│   │   ├── feature-backlog.md
│   │   └── handoffs/
│   ├── completed/                  # Finished plans
│   │   └── handoffs/
│   └── tech-debt-tracker.md        # Known shortcuts
├── references/                     # External docs, llms.txt files
└── process/                        # KEEL process docs (from kit)

[PROJECT_DIR]/                      # Your application source
├── [SOURCE]/                       # Business logic
├── [TESTS]/                        # Tests
└── [CONFIG]/                       # Configuration
```

## Growth Stages

| Stage | Trigger | KEEL Additions |
|-------|---------|----------------|
| **0: Foundation** | Before first code | Folder structure, CLAUDE.md, ARCHITECTURE.md, core-beliefs, Docker |
| **1: First Code** | Core module works | Tech debt updates, formatter checks |
| **2: Working App** | App renders/serves | Quality tracking, structural tests for module coverage |
| **3: MVP Complete** | All success criteria met | Move plans to completed/, garbage collection pass |
| **4: Post-MVP** | New features | New plans, periodic doc review, consider pre-commit hooks |

## The Four Loops

### 1. Validation Loop
```
Claude writes code → runs tests → checks output →
fixes failures → re-runs → repeats until green
```

ParchMark-specific validation tools:
- Backend: `pytest` (xdist + testcontainers, per-worker PostgreSQL), `ruff format`, `ruff check`, `mypy`.
- Frontend: `vitest` + React Testing Library, `eslint`, `tsc --noEmit`.
- Integration: Chrome DevTools MCP for manual visual QA before UI PRs
  (navigate localhost:5173 → take_snapshot → fill form → list_console_messages).

### 2. Knowledge Boundary
```
┌─────────────────────────────────┐
│    What Claude CAN see          │
│  Code, markdown, schemas,      │
│  exec plans, tests, configs    │
└─────────────────────────────────┘
        ↑ must encode ↑
┌─────────────────────────────────┐
│   What Claude CAN'T see        │
│  Slack, verbal decisions,      │
│  your head, Google Docs        │
└─────────────────────────────────┘
```

### 3. Layered Architecture

Two domains, each with its own layer stack. See
[ARCHITECTURE.md](../ARCHITECTURE.md) for full detail and dependency rules.

```
Frontend (ui/src)                  Backend (backend/app)
───────────────────                ───────────────────────
Router                             Main (lifespan, CORS)
Features (auth/notes/ui/settings)  Routers
Stores (Zustand)                   Services / Auth
Services (HTTP client)             Schemas
Utils                              Models (SQLAlchemy)
Config                             Database
Types                              ───────────────────────
───────────────────                       PostgreSQL + pgvector
```

Dependencies flow strictly downward within each stack. The two stacks
communicate only over the JSON REST boundary (`/api/*`). Known
cross-layer edges are documented explicitly in `ARCHITECTURE.md`.

### 4. Garbage Collection
After each implementation chunk:
- Re-read CLAUDE.md — still accurate?
- Re-read ARCHITECTURE.md — still matches code?
- Update tech-debt-tracker with new shortcuts
- Fix any docs that lie
