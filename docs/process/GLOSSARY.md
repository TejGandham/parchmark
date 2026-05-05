# KEEL Glossary

**KEEL** — Knowledge-Encoded Engineering Lifecycle. A structured process for Claude-driven software development where humans steer and agents execute through specialized pipelines. Adapted from OpenAI's harness engineering.

**Knowledge-Encoded** — The "K" in KEEL. The principle that everything agents need must be committed as versioned artifacts in the repository. If it's not in the repo, it doesn't exist.

**Knowledge Boundary** — The limit of what an agent can see. Anything outside the repo (Slack, Google Docs, verbal decisions, tacit expertise) is invisible. The only way to make it visible: encode as markdown in the repo.

**Agent Legibility** — Optimizing documentation and code for agent comprehension rather than human aesthetics. Specs must be unambiguous enough for agents to execute without clarification.

**Progressive Disclosure** — Information architecture where agents start with a small, stable entry point (CLAUDE.md ~80 lines) and are taught where to look next, rather than being overwhelmed with everything up front.

**North Star** — The vision document (`NORTH-STAR.md`, at the project root) that defines where the project is heading, what principles govern decisions, and how the process evolves through growth stages. Where taste is encoded before it becomes linters.

**Handoff** — An append-only markdown file (`docs/exec-plans/active/handoffs/F{id}-{feature-name}.md`) that persists context between pipeline agents. Each agent reads upstream context and appends its output. Never rewritten — only appended to.

**Pipeline Variant** — One of four execution paths a feature takes through the agent roster:
- **Bootstrap:** Three separate features, each dispatching one agent then landing-verifier then roundtable-review? then post-landing:
  - F01: docker-builder → landing-verifier → roundtable-review? → post-landing
  - F02: scaffolder → landing-verifier → roundtable-review? → post-landing
  - F03: config-writer → landing-verifier → roundtable-review? → post-landing
- **Backend:** pre-check → roundtable-precheck? → researcher? → arch-advisor? → backend-designer? → roundtable-review? → test-writer → implementer → code-reviewer → spec-reviewer → safety-auditor? → arch-advisor-verify? → landing-verifier → roundtable-review? → post-landing
- **Frontend:** pre-check → roundtable-precheck? → researcher? → arch-advisor? → frontend-designer → roundtable-review? → test-writer → implementer → code-reviewer → spec-reviewer → arch-advisor-verify? → landing-verifier → roundtable-review? → post-landing
- **Cross-cutting:** pre-check → roundtable-precheck? → test-writer → implementer → code-reviewer → landing-verifier → roundtable-review? → post-landing

**Execution Brief** — The structured output of the pre-check agent. Contains: intent classification, complexity tier, spec reference, dependencies, what to build, new/modified files, acceptance tests, edge cases, risks, constraints for downstream (MUST/MUST NOT), and routing decisions (designer needed? researcher needed? arch-advisor needed?).

**Orchestrator** — The human who steers the KEEL process: kicks off features and reviews the resulting PR. The `keel-pipeline` skill runs the pipeline end-to-end: dispatching agents, calling roundtable MCP tools when available, running the post-landing procedure (doc-gardener, archive, commit, push the feature branch, open a PR). The human's review surface is the PR on their forge. The orchestrator does not write code.

**Invariant** — A non-negotiable rule specific to the project's domain, enforced mechanically. Examples: "never force-pull" (git), "validate all input at boundaries" (API), "all transforms must be idempotent" (data pipeline).

**Golden Principle** — An opinionated, mechanical rule that keeps the codebase legible and consistent for future agent runs. Encoded in the repo and enforced continuously. From OpenAI: "Human taste is captured once, then enforced continuously on every line."

**Garbage Collection** — Periodic sweeps to detect and fix documentation drift. The doc-gardener agent scans for stale content; the orchestrator applies fixes. "Docs that lie are worse than no docs."

**Ralph Wiggum Loop** — Agent-to-agent review pattern where an agent reviews its own changes, requests additional agent reviews, and iterates until all reviewers are satisfied. Named by OpenAI. Enables increasing autonomy without human bottleneck.

**Oracle** — The per-feature block in the JSON PRD (`features[].oracle`) that names what makes the feature pass or fail. Required keys: `type` (`unit | integration | e2e | smoke`) and `assertions[]`; optional `tooling`, `setup`, `actions[]`, `gating`. Consumed by test-writer (translates `assertions[]` into failing tests), pre-check (emits each assertion as a JSON-pointer `/features/<idx>/oracle/assertions/<aidx>` in the execution brief), spec-reviewer (verifies implementation conforms), safety-auditor (scans the oracle for auth/credential/token surface that must be checked against domain invariants), and backlog-drafter (synthesizes one for each new feature). Paired with `contract` on the same feature: `contract` declares the surface (what exists), `oracle` declares what must hold true about it. The name is the formal-methods term-of-art (Howden, Weyuker) for the authoritative source of correctness, distinct from the tests that exercise it.

**RED → GREEN Flow** — The handoff between test-writer and implementer. Test-writer produces failing tests (RED state). Implementer writes code to pass them (GREEN state). Neither crosses the boundary: test-writer never writes implementation, implementer never modifies tests.

**Lifecycle** — The "L" in KEEL. The full arc: north star → spec → backlog → pipeline → landed feature → garbage collection. Every feature goes through this complete cycle.

**Arch-advisor** — Read-only architecture consultant agent with two invocation modes: CONSULT (Step 1.7, before design) provides architecture guidance for complex features; VERIFY (Step 7.5, before landing) performs independent structural review. Gated by pre-check's complexity classification — only runs for architecture-tier features.

**Intent Classification** — Pre-check's mandatory first step. Categorizes work as refactoring, build, mid-sized, architecture, or research. Determines pipeline routing: which optional agents run, complexity tier, and whether Arch-advisor is needed.

**Complexity Tier** — Pre-check's assessment of feature scope: trivial (skip designer), standard (normal pipeline), complex (all gates), architecture-tier (Arch-advisor consultation + verification). Drives pipeline routing decisions.

**Wisdom Accumulation** — Pattern where agents propagate context downstream through structured Decisions (choices made and why) and Constraints (MUST/MUST NOT for downstream agents) in the handoff file. Prevents agents from repeating upstream mistakes or violating upstream decisions.

**Structured Rejection** — Pattern where gate agents (spec-reviewer, safety-auditor) output a machine-readable `**Verdict:**` field as their first line. The pipeline branches on this verdict. Max 2 spec-review loops, max 3 safety-auditor loops before escalating to human.

**VERIFIED** — Handoff status emitted by landing-verifier. Indicates all pipeline gates passed and tests pass, but the feature has not yet been committed or pushed. The orchestrator runs roundtable review (if enabled) and then the post-landing procedure to transition through READY-TO-LAND to LANDED.

**Pragmatic Minimalism** — Arch-advisor's core decision framework: bias toward simplicity, leverage what exists, prioritize developer experience, one clear path, match depth to complexity. Ported from OMA (Oh My OpenAgent).

**Two-Org Test** — Proposal-evaluation gate from `AGENTS.md` §"Framework proposal design: defaults + knobs". A KEEL framework knob is licensed only when the proposer can name two real organizations that would make different durable choices for non-pathological reasons. Bikeshedding ("someone could prefer X") doesn't earn a knob. Distinguishes documented disagreement-in-practice from hypothetical preference.

**Least-Assuming Default** — From `AGENTS.md` §"Framework proposal design: defaults + knobs". The behavior requiring the fewest org-specific assumptions, not the cleanest UX or the proposer's preferred behavior. When a knob's default would force an org-specific assumption (rebase vs merge vs squash, monorepo vs polyrepo, gh vs forge-CLI), the default must be the path that assumes least; the assumption-laden behavior is opt-in.

**READY-TO-LAND** — Handoff status set by the orchestrator after roundtable landing review (Step 8.5) completes or is skipped. Indicates the feature has passed all gates, been reviewed (if roundtable enabled), and is ready for the post-landing procedure (Step 9). When roundtable is disabled, this state is skipped — VERIFIED triggers Step 9 directly.

**Roundtable Review** — Advisory multi-model review using the roundtable MCP server. Runs at three pipeline points: post-pre-check (Step 1.3, tools: `roundtable-critique` + `roundtable-canvass`), post-designer (Step 2.5, tools: `roundtable-blueprint` + `roundtable-critique`), and pre-landing (Step 8.5, tools: `roundtable-crosscheck` + `roundtable-critique`). Automatic when MCP server is available and enabled in CLAUDE.md. Advisory, not authoritative — findings feed back through pre-check, designer, or the existing gate chain respectively, never directly block landing. Gracefully skipped if MCP server is unavailable.

**Feature Slice (F##)** — The smallest independently testable, vertical-slice node in the backlog dependency DAG. The "F" prefix is historical (originally "feature"); the unit is a slice, not a whole product feature. Cross-slice cohesion comes from the shared `PRD: <slug>`. See `feature-backlog.md` and Step 0 of `.claude/skills/keel-pipeline/SKILL.md`.

**Branching Policy** — CLAUDE.md "Pipeline Preferences" key controlling how /keel-pipeline F## handles unmerged `Needs:`. `halt` (default — least-assuming) refuses to start F## with unmerged Needs and emits a CTA. `stack` (opt-in) branches F## from the unmerged intra-PRD ancestor's tip and sets the PR base accordingly. Cross-PRD Needs always halt regardless of policy. See Step 0 of `.claude/skills/keel-pipeline/SKILL.md`.

**Restack** — The `git rebase --update-refs --onto <base> <parent_sha>` operation that lifts a stacked feature branch onto base after its parent merged. Universal across squash/merge/rebase merge strategies; requires Git ≥ 2.38. /keel-pipeline runs the restack at re-invocation when it detects `parent_sha` has become an ancestor of base.
