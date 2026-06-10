# North Star: ParchMark

Full-stack markdown note-taking app
Adapted from [OpenAI's harness engineering article](https://openai.com/index/harness-engineering/).
This document defines where we're heading — not where we are today.

## The Principle

Humans steer. The agent executes. The repo is the agent's workspace, context,
and system of record. Everything the agent needs to make decisions lives here.

## Framework Principles

KEEL operates under seven principles anchored at
[`docs/process/KEEL-PRINCIPLES.md`](docs/process/KEEL-PRINCIPLES.md)
(copied into this project by `install.py`). Every agent and skill
KEEL ships references these:

- **P1. Agent Legibility** — repo optimized for agent comprehension, not human aesthetics
- **P2. Progressive Disclosure** — small stable entry points, navigate deeper on demand
- **P3. Self-Sufficient Snapshot** — repo's current state is enough to reconstruct any view
- **P4. No Redundant Storage** — files author unique content; derivable data isn't stored
- **P5. Snapshot, Not Timeline** — `git log` has evolution; repo reflects what is
- **P6. Code/Specs/Backlog Win** — when artifacts disagree, lower-level wins
- **P7. Halt with Call-to-Action** — gates that block must emit actionable next-step messages

## Three-Tier Process (features and Binders)

|Tier|Unit|Property|Owner|
|-|-|-|-|
|Product design|**Binder**|Cohesion — why these features belong together|Human (product owner) writes|
|Implementation work|**WI##**|Isolation — smallest testable unit|Human accepts the slate once per Binder, authors each spec|
|Execution|**Pipeline**|Per-WI## (unchanged)|KEEL runs autonomously|

A Binder bundles cohesive WI## entries for one product slice. Each WI## retains isolation (independent spec, pipeline, PR). `/keel-refine` is the Binder-scope drafting gate; each WI## then pipes independently.

**Invariant 7:** every WI## traces to a Binder via `Binder: <slug>` pointing to `docs/exec-plans/binders/<slug>.json` (structured JSON Binder, schema v1), or declares `Binder-exempt: <reason>` where reason ∈ `{legacy, bootstrap, infra, trivial}`.

## What We Adopt (Fully)

**Repository = system of record.** If it's not in the repo, it doesn't exist
to the agent. Slack discussions, verbal decisions, tacit knowledge — all must be
encoded as markdown, code, or config in this repo.

**The project guide as table of contents.** ~80 lines, pointers to deeper docs.
Not an encyclopedia. Teaches the agent what this project is and where to look next.

**Progressive disclosure.** The project guide → ARCHITECTURE.md → specs → plans.
The agent reads what it needs when it needs it.

**Plans as first-class artifacts.** Active plans in `exec-plans/active/`,
completed plans in `exec-plans/completed/`. Progress and decisions logged
in the plan itself.

**Agent legibility is the goal.** Docs are written for the agent's comprehension,
not for a human audience. Clear, scannable, with explicit cross-references.

## What We Adapt (Scaled Down)

<!-- CUSTOMIZE: What parts of harness engineering do you adapt for your scale?
     Examples:
     - Mechanical enforcement: start with formatter + tests, add structural tests later
     - Garbage collection: manual review at session boundaries, automated sweeps later
     - Agent review: self-review before presenting to human
     - Observability: start with stdout/stderr, add structured logging later -->

**Mechanical enforcement.** PostToolUse hooks auto-run `ruff format` +
`ruff check --fix` on Python and `prettier` on TypeScript; `make test` gates
every PR with lint, format, types, and tests at a 90% coverage floor on both
frontend and backend.

**Garbage collection.** doc-gardener sweeps for doc drift after landings;
known shortcuts live in `docs/exec-plans/tech-debt-tracker.md`.

**Agent review loops.** Pipeline review gates (code-reviewer, spec-reviewer,
safety-auditor) plus the persona review panel; roundtable MCP is opt-in for
changes that amend invariants or cross layer boundaries.

**Observability stack.** `GET /api/health` (DB + version info), container
logs via `make deploy-logs`, SHA-tagged images for rollback.

## What We Skip (For Now)

- Headless/scheduled pipeline runs — pipelines run interactively in Claude Code.
- Codex host surface — this install targets Claude Code only.

## Growth Stages

| Stage | Trigger | KEEL Additions |
|-|-|-|
| **0: Foundation** | Before first code | Folder structure, the project guide, ARCHITECTURE.md, core-beliefs |
| **1: First Code** | Core module works | Tech debt updates, formatter checks |
| **2: Working App** | App renders/serves | Quality tracking, structural tests for module coverage |
| **3: MVP Complete** | All success criteria met | Move plans to completed/, garbage collection pass |
| **4: Post-MVP** | New features | New plans, periodic doc review, consider pre-commit hooks |

## The Four Loops

### 1. Validation Loop
```
The agent writes code → runs tests → checks output →
fixes failures → re-runs → repeats until green
```
<!-- CUSTOMIZE: Add your validation tools (e.g., LiveView test helpers, Playwright, Cypress) -->

### 2. Knowledge Boundary
```
What the agent CAN see:
  Code, markdown, schemas, exec plans, tests, configs.
        ↑ must encode ↑
What the agent CAN'T see:
  Slack, verbal decisions, your head, Google Docs.
```

### 3. Layered Architecture
<!-- CUSTOMIZE: Replace with your project's layer diagram -->
```
[UI Layer]
      ↓
[Runtime / Service Layer]
      ↓
[Foundation / Core Layer]
```
Dependencies flow strictly downward.

### 4. Garbage Collection
After each implementation chunk:
- Re-read the project guide — still accurate?
- Re-read ARCHITECTURE.md — still matches code?
- Update tech-debt-tracker with new shortcuts
- Fix any docs that lie
