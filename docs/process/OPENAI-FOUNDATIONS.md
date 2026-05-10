# OpenAI Foundations: The Harness Engineering Origin

KEEL is adapted from OpenAI's "Harness Engineering: Leveraging Codex in an Agent-First World" (February 11, 2026), by Ryan Lopopolo, Member of Technical Staff.

## The Experiment

OpenAI's team built and shipped an internal beta product with zero manually-written code over five months. The results:
- ~1 million lines of code (application logic, tests, CI, docs, observability, tooling)
- ~1,500 pull requests merged
- 3 engineers (growing to 7), averaging 3.5 PRs per engineer per day
- Built in roughly 1/10th the time it would have taken manually

## Core Principles

### "Humans Steer. Agents Execute."
Engineers describe tasks via prompts. Agents execute and open PRs. Humans prioritize work, translate user feedback into acceptance criteria, and validate outcomes. When the agent struggles, the fix is never "try harder" — identify what capability is missing and build it.

### "Give the Agent a Map, Not a 1,000-Page Manual"
AGENTS.md (~100 lines) serves as a table of contents, not an encyclopedia. The knowledge base lives in a structured docs/ directory. Progressive disclosure: agents start with a small, stable entry point and navigate to deeper sources as needed.

### "Repository as System of Record"
Anything not in the repo doesn't exist to the agent. Slack discussions, Google Docs, verbal decisions, tacit knowledge — all must be encoded as versioned repo artifacts.

### "Agent Legibility is the Goal"
The repo is optimized for agent comprehension, not human aesthetics. "Boring" technologies are preferred — composable, stable APIs, well-represented in training data. In some cases, reimplementing a subset of functionality is cheaper than working around opaque upstream behavior.

### "Enforce Invariants, Not Implementations"
Strict architectural boundaries enforced mechanically. Local autonomy within those boundaries. "You care deeply about boundaries, correctness, and reproducibility. Within those boundaries, you allow agents significant freedom."

### Entropy and Garbage Collection
"Technical debt is like a high-interest loan: almost always better to pay it down continuously in small increments." Golden principles encoded in the repo, recurring background agents scan for deviations, open targeted refactoring PRs. Human taste captured once, enforced continuously.

### Throughput Changes the Merge Philosophy
Minimal blocking merge gates. Short-lived PRs. Corrections cheap, waiting expensive. Agent-to-agent review (the "Ralph Wiggum Loop").

## Key Diagrams

### Diagram 1: The Knowledge Boundary
"What Codex can't see doesn't exist." Agent knowledge is a bounded bubble. Outside the bubble: Google Docs ("This document outlines our approach to feature prioritization"), Slack messages ("We will follow @PaulM's guidance on security posture"), and tacit knowledge ("Ryan is responsible for the overall architectural direction"). Arrow: "Encode into codebase as markdown" feeds into the bubble.

### Diagram 2: The Validation Loop
Sequence diagram with three actors: CODEX, APP, CHROME DEVTOOLS. Flow: Select target + clear console → Snapshot BEFORE → Trigger UI path → Runtime events (during interaction) → Snapshot AFTER → Apply fix + restart → LOOP UNTIL CLEAN: Re-run validation. The agent closes its own feedback loop by observing before/after state.

### Diagram 3: The Observability Stack
APP sends three signal types: LOGS (HTTP), METRICS (OTLP), TRACES (OTLP) → VECTOR (aggregator) → fans out to: Victoria Logs (LogQL API), Victoria Metrics (PromQL API), Victoria Traces (TraceQL API). CODEX queries all three APIs to Query, Correlate, Reason → Implement change (PR) → CODEBASE. Each git worktree gets its own ephemeral observability stack, torn down when the task completes.

### Diagram 4: Layered Domain Architecture
Business logic domain contains three tiers: {Types → Config → Repo} at bottom, {Service → Runtime → UI} in middle, {Providers → App Wiring + UI} at top. Utils sits outside the boundary and feeds into Providers. Dependencies flow strictly forward. Cross-cutting concerns (auth, telemetry, feature flags) enter via the single Providers interface. Enforced by custom linters and structural tests.

## How KEEL Adapts These Principles

| OpenAI Concept | KEEL Mechanism |
|---|---|
| AGENTS.md as table of contents | CLAUDE.md ~80 lines with pointers to docs/ |
| Structured docs/ directory | docs/exec-plans/prds (JSON PRDs), design-docs, exec-plans hierarchy |
| Execution plans with progress logs | Handoff files (per-feature; agent output sections snapshot, deliberation sections append-only) |
| Custom linters for architecture | safety-auditor agent + PreToolUse hooks |
| Background doc-gardening agents | doc-gardener agent (periodic batch sweeps) |
| Agent-to-agent review | spec-reviewer agent in pipeline |
| Quality scoring | Tech debt tracker |
| Golden principles | Core beliefs doc (docs/design-docs/core-beliefs.md) |

## Further Reading

The full article: "Harness Engineering: Leveraging Codex in an Agent-First World" — OpenAI Engineering Blog, February 11, 2026.
