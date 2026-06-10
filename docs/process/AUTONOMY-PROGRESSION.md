# Increasing Agent Autonomy Over Time

How to evolve your KEEL process from "human reviews everything" to increasing levels of agent self-sufficiency.

## The Progression

| Stage | Human Role | Agent Role | Typical Timeline |
|---|---|---|---|
| **1. Full Oversight** | Reviews every agent output, every completed feature | Executes single steps, waits for approval | First 5-10 features |
| **2. Pipeline Trust** | Reviews landed features, spot-checks handoffs | Runs full pipeline without step-by-step approval | Features 10-20 |
| **3. Agent Review** | Reviews agent review summaries | Agents review each other's work (spec-reviewer, safety-auditor) | Features 20-30 |
| **4. Self-Validation** | Reviews exceptions and escalations only | Agents validate their own work by driving the application | After MVP |
| **5. End-to-End** | Steers priorities, resolves judgment calls; submits + merges via `/keel-submit` when using a forge | Agent reproduces bug → fixes → validates → completes repo-locally → responds to feedback | Mature codebase |
| **6. Batch Orchestration** | Selects a set of WIs; reviews the stacked-branch chain, then submits + merges it via `/keel-submit` | Agent runs the selected set in dependency order as a stacked-branch chain (each WI completes repo-locally), halting fail-fast on the first failure | Mature codebase + a trusted lean lane |

## Stage 1: Full Oversight (Start Here)

Every KEEL project starts here. The human:
- Reads every execution brief from pre-check
- Reviews every design brief
- Reads every test before implementer runs
- Reviews every implementation
- Reads every spec conformance report
- Manually runs landing-verifier verification

This is intentional. You're calibrating: learning what the agents do well, where they struggle, and what capabilities are missing.

### When to move to Stage 2
- You've stopped finding issues in execution briefs
- Test-writer consistently produces the right tests
- Implementer consistently passes tests on first run
- You trust the handoff mechanism

## Stage 2: Pipeline Trust

Stop reviewing intermediate steps. Run the full pipeline and review the landed result:
- Read the handoff directory after landing-verifier reports VERIFIED
- Review the git diff (what changed)
- Run the app and verify behavior
- Commit if satisfied

### When to move to Stage 3
- Spec-reviewer consistently catches deviations you would have caught
- Safety-auditor has never missed a violation you found manually
- You trust the gate agents

## Stage 3: Agent Review

Let agents review each other. The human only reviews:
- Spec-reviewer output (not the code directly)
- Safety-auditor output (not scanning for violations manually)
- The final landing report

### When to move to Stage 4
- You've built validation infrastructure (browser automation, observability)
- Agents can drive the app and verify behavior programmatically
- Test coverage is comprehensive enough that "tests pass" means "it works"

## Stage 4: Self-Validation

Agents validate their own work by driving the application:
- Browser automation / DevTools integration for UI verification
- Observability stack queries for runtime behavior verification
- Performance benchmarks for non-functional requirements

From OpenAI: "We made the app bootable per git worktree, so Codex could launch and drive one instance per change."

In KEEL this is the frontend **served-bundle drive**: when a project has a
served verify command and a `ui` feature's `oracle.type` is `e2e`/`smoke`,
`landing-verifier` builds + drives the served bundle and verifies the
viewport/layout/console surface. It is **derived from the harness, not a knob**,
and the rendered floor (`PIPELINE-DOCTRINE.md` §"Frontend acceptance") is
achievable earlier — pre-Stage-4 — so an infra-less project still verifies
rendering and wiring in-process.

### When to move to Stage 5
- Agent validation catches issues before humans do
- The codebase has comprehensive golden principles
- Garbage collection runs automatically
- You trust the system enough to sleep while it works

## Stage 5: End-to-End

The agent drives a feature from bug report to a repo-local completed feature:
1. Validate current codebase state
2. Reproduce reported bug
3. Record evidence of failure
4. Implement fix
5. Validate fix by driving the application
6. Commit on the feature branch (the feature is now done repo-locally)
7. Respond to agent and human feedback
8. Detect and remediate build failures
9. Escalate only when judgment is required
10. Publish via `/keel-submit` (push + PR) and confirm the merge, when the workflow uses a forge

From OpenAI: "We regularly see single Codex runs work on a single task for upwards of six hours (often while the humans are sleeping)."

## Stage 6: Batch Orchestration

Stages 1-5 widen autonomy *within one feature*. Stage 6 widens it *across a
selected set* of features. The human picks the set — the authorization boundary
for the run — and the agent sequences it:

1. Human selects a set of work items (an explicit list, or the dependency
   closure of one leaf) from a Binder
2. Agent topologically orders the set by its `needs[]` dependencies
3. Agent runs each not-yet-done WI through the lean lane in order, each as its
   own branch stacked on top of its predecessor's branch (completion is
   repo-local — committed + archived, no PR)
4. Any single failure halts the whole run fail-fast, naming the failed WI, the
   un-run remainder, and the exact resume command
5. The agent never merges and never publishes — it ends with a concrete
   call-to-action: review the stacked-branch chain, and (if you use a forge)
   run `/keel-submit <binder>` to push the stack and open one PR per branch,
   then review and merge from the bottom up

In KEEL this is the Karta lane's `/karta-drive` (`docs/process/KARTA-LANE.md`):
a pure sequencer over `/karta-pipeline` that stores nothing — order, frontier,
and completion are re-derived from repo state every run, so a resumed run picks
up exactly where the last one halted. It is *batch* autonomy, not *parallel*:
the chain is sequential, and each WI's green gate must pass before the next
builds on it.

### When this stage fits

- The lean lane's gates (Stage 3's agent review) catch what you would have
- The stacked-branch review surface (bottom-up, published via `/keel-submit`) is one you trust
- The features in a set are genuinely a dependency chain, not racing siblings

## What Enables Each Stage

| Capability | Enables |
|---|---|
| Handoff files | Stage 2 (pipeline trust without step reviews) |
| spec-reviewer + safety-auditor | Stage 3 (agent-to-agent review) |
| Browser/app automation | Stage 4 (self-validation) |
| Observability stack | Stage 4 (runtime verification) |
| Golden principles + garbage collection | Stage 5 (autonomous quality) |
| Stacked-branch chains + a trusted lean lane | Stage 6 (batch orchestration of a selected set) |
| Comprehensive test coverage | All stages (the foundation) |

## The Key Insight

Autonomy isn't given — it's earned. Each stage builds on infrastructure from the previous one. Skip a stage and the foundation crumbles.

"When something failed, the fix was almost never 'try harder.' The primary job became: identify what capability is missing and make it legible and enforceable for the agent." — OpenAI Harness Engineering
