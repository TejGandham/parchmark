# Quick Start: Your First Afternoon with KEEL

KEEL — Knowledge-Encoded Engineering Lifecycle. From install to first feature through the pipeline.

## Prerequisites

- A supported agent host — [Claude Code](https://claude.com/claude-code) or the OpenAI Codex CLI (pick one at install time via `install.py --host`); the host runs KEEL's agents and skills
- A reproducible dev environment for your stack — bring your own runtime: a local toolchain like `uv`, `mise`, `asdf`, or `nix`, or a container setup you add later as a product feature via `/keel-refine` → `/keel-pipeline`
- Python 3.14+ and [`uv`](https://docs.astral.sh/uv/) on PATH — KEEL's installer halts with a CTA if either is missing; `uv` can install 3.14 for you (`uv python install 3.14`)
- A product idea (even rough is fine)

## How KEEL Grows With Your Project

You don't need everything on day one. KEEL is designed to match the weight
of your project at each stage:

| Stage | What you add | What it unlocks |
|-|-|-|
| **Day 1** | the project guide + core-beliefs.md | Agent has project context and safety rules |
| **Day 2** | Product spec + ARCHITECTURE.md | Agent can reason about what to build and where it fits |
| **Week 1** | Backlog + first handoff files | Structured pipeline execution begins |
| **Week 2+** | Safety-auditor config + domain invariants | Mechanical enforcement of non-negotiable rules |
| **Month 2+** | Full pipeline + garbage collection | Institutional knowledge compounds across features |

Start with whatever you need now. Add the rest as complexity demands it.
The framework catches you when ad-hoc prompting stops scaling.

## The 3 Steps

### 1. Install KEEL

```bash
# New project
mkdir my-project && cd my-project && git init

# Existing project
cd my-project

# Install KEEL
git clone --depth 1 https://github.com/TejGandham/keel.git /tmp/keel
python3 /tmp/keel/scripts/install.py             # add --host codex for the Codex CLI
rm -rf /tmp/keel
```

The default install targets Claude Code; pass `--host codex` for the OpenAI
Codex CLI (one host per install — see [INSTALL.md](../INSTALL.md)).

The installer prompts for project name, stack, and description. It copies
agents, skills, doc structure, and template files into your project,
replaces placeholders, and cleans up instruction comments. It never
overwrites existing files.

### 2. Configure with your agent host

Open your agent host in your project directory and run the command the
installer printed:

- **New project (no existing code):** `/keel-setup`
- **Existing codebase:** `/keel-adopt`

Both skills walk you through everything interactively:
- The project guide refinement (project identity, safety rules, commands)
- North star (vision, growth stages, principles)
- Architecture (layers, modules, data flow)
- Domain invariants (per-item confirmation)
- Safety enforcement and agent configuration

Every phase drafts from context first, then asks you to review.
You confirm at every gate.

### 3. Your first feature via a Binder

1. **Draft the Binder.**

   ```
   /keel-refine "short description of what you're building"
   ```

   Or point at any non-JSON input material (legacy markdown spec,
   bundle directory with wireframes, image, etc.) — `/keel-refine`
   is the conversion hub that turns these into a structured JSON Binder:

   ```
   /keel-refine docs/exec-plans/binders/my-feature.md
   ```

   The skill will draft WI## entries, walk them with you card-by-card,
   and commit both the structured JSON Binder file (at
   `docs/exec-plans/binders/<slug>.json`) and the backlog entries when you
   type `commit`.

2. **Pipe each WI## independently.**

   ```
   /keel-pipeline WI## docs/exec-plans/binders/<slug>.json
   ```

   The pipeline reads the structured JSON Binder only; a `.md` path is a
   routing error (halt with CTA back to `/keel-refine`).

   Repeat for each WI## in dependency order.

3. **Review the completed features.**
   Each WI## completes on its own `keel/WI##-<slug>` branch (handoff archived, backlog `[x]`). Integrate them in dependency order however your workflow lands code; if you use a forge, `/keel-submit <binder>` pushes the branches and opens one PR per WI## for review.

## What Happens Next

After bootstrap lands, the pipeline becomes your daily workflow:
1. Pick next feature from backlog
2. Run `/keel-pipeline WI{id} docs/exec-plans/binders/<slug>.json`
3. Watch the pipeline — it runs end-to-end, self-corrects at gates, and stops in-session only on escalation
4. Review the completed feature — the pipeline archives the handoff to `completed/handoffs/` and commits on the feature branch; the work is done repo-locally (no forge required). To publish: run `/keel-submit <binder>` to push the branch and open a PR on your forge for review and merge

When the pipeline stalls, see [FAILURE-PLAYBOOK.md](FAILURE-PLAYBOOK.md) for the decision tree.

## Need to move faster? The lean lane

Everything above is the full-rigor `keel-*` lane. When you are building fast and willing to take **visible, recoverable** tech debt, run the lean lane instead — `/karta-refine` → `/karta-pipeline WI##` (same Binder shape, one feature per run):

```
pre-check → implementer → karta-spec-reviewer → safety-auditor → green gate → complete
```

It drops the design stages, the keel reviewers, and the review panel, and is **spec-first** (tests secondary, declared with a marker where skipped), but keeps a non-negotiable floor: the **`karta-spec-reviewer`** structural conformance gate; your project's tests/build must pass (the **green gate** — configure the command in the project guide §Development, or the lane halts), the **safety audit** still runs, and **every cut is declared inline** with a `KARTA-DEFER` / `KARTA-PLACEHOLDER` / `KARTA-GUARD` marker so nothing goes silent. Pick the lane per feature by which command you run; there is no graduation. Read [KARTA-LANE.md](KARTA-LANE.md) before your first lean run.

See [THE-KEEL-PROCESS.md](THE-KEEL-PROCESS.md) for the comprehensive guide.
