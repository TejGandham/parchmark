---
name: karta-pipeline
description: "Run one feature through the Karta lean lane (spec-first). Gate map: pre-check → implementer → karta-spec-reviewer → safety-auditor → green gate → complete. Takes a single `WI## <binder>` argument exactly like keel-pipeline; declares every cut with a ledger marker."
---

# Karta Pipeline (lean lane)

Karta is the dialed-down-rigor sibling of `keel-pipeline`. It is **not** a
mode, a repo state, or a one-way flip — running this command *is* the lane
choice (see `docs/process/KARTA-LANE.md`). There is no lane registry, no
`Binder-exempt: auto-stack` tag, and no `Lane:`/`--lane` config; the ledger
markers in the tree record declared debt, not lane provenance — a feature with
no markers is equivalent whichever lane built it.

`karta-pipeline` runs **one feature per invocation**, exactly like
`keel-pipeline` — one `WI## <binder>` argument in, one feature completed
repo-locally out. Single-feature
**stacking** on an unmerged intra-Binder dependency is inherited from keel (see
the inheritance clause below / `--stack`); **sequencing a selected set** of
features in dependency order is `/karta-drive`, not this skill — `karta-pipeline`
still runs once per feature.

This skill is a **delta of `keel-pipeline`**, not a fork. It reuses
`keel-pipeline`'s single-WI machinery wholesale and authors only the lean gate
map (including the green gate), the conditional test-writer rule, and the halt
set. Read the keel-pipeline skill for every shared section
cited below — this file deliberately does not restate them (P4).

## Framework principles

Every halt here uses P7 (call-to-action) wording, exactly as
`keel-pipeline`. Conflict resolution follows P6. See
[`docs/process/KEEL-PRINCIPLES.md`](../../../docs/process/KEEL-PRINCIPLES.md).

## The lane's own discipline lives in KARTA-LANE.md

[`docs/process/KARTA-LANE.md`](../../../docs/process/KARTA-LANE.md) holds the
lane discipline this skill **executes**: the declare-and-owe rule, the two
human-OK sign-off gates, **bones-clean admissibility**, and the **refusal
protocol** (the verbatim responses to "skip the marker" / "just mock it" /
"hack the data model"). When speed pressure asks you to hide debt, fake the
product, cut the bones, or bless lean code as production, emit the matching
verbatim response from §"Refusal protocol" and halt — do not silently take
the shortcut. The **marker grammar** (the three tokens `KARTA-DEFER` /
`KARTA-PLACEHOLDER` / `KARTA-GUARD`, fields, delimiter rule, integrity hard
rules, and the `scripts/karta-deferred-ledger.py` scanner with its `--check`
knob) is shared, lane-agnostic doctrine in
[`docs/process/PIPELINE-DOCTRINE.md`](../../../docs/process/PIPELINE-DOCTRINE.md)
§"Declared-debt markers". Read marker shapes there; this skill references
them, never restates them.

## Handoff substrate, arguments, per-hop protocol — inherited

The handoff substrate (per-feature directory, `routing.json` mutated only
via `keel-routing.py`, `resolved-work-item.json` written once, agent
self-writes), the structured-JSON-Binder argument contract (with the
"`/keel-refine` first" halt for non-JSON or missing Binders — Karta's
authoring sibling is `karta-refine`, which produces the same JSON shape with
lean frames), and **the per-hop protocol** (the spawn-message preamble — the
`[KEEL-ROLE <agent>]` contract-acquisition prefix on every dispatch — dispatch
shape, file verification, routing update, next-stage dispatch) are inherited
**unchanged** from `keel-pipeline` §"Handoff substrate", §"Arguments", and
§"The per-hop protocol (every sequential agent)". Karta differs from those
sections only in *which* agents dispatch — never in how a hop is dispatched
or verified. `<dir>` carries the same meaning.

## Arguments — one feature, one Binder (inherited)

```
/karta-pipeline WI04 docs/exec-plans/binders/my-feature.json
```

The argument contract is inherited **unchanged** from `keel-pipeline`
§"Arguments": one `WI##` id, one structured JSON Binder path, the same
"`/keel-refine` first" halt for a non-JSON or missing Binder (Karta's
authoring sibling is `karta-refine`). One invocation builds and completes
exactly one feature.

**Optional worktree-path contract (dispatch-time).** When `/karta-drive`
dispatches this skill it injects an **absolute worktree path** into the prompt
(never stored — runtime-derived; see `karta-drive` §"Worktrees"). If a path is
present, the **first action** asserts `git -C <path> rev-parse --show-toplevel`
equals that exact path → HALT (P7) on mismatch (the dispatch resolved to the
main checkout or a wrong tree): *"assigned worktree `<path>` but
`git rev-parse --show-toplevel` resolved elsewhere — refusing to build in the
wrong tree; re-dispatch with the correct worktree path."* Prefer `git -C <path>`
over `cd` for every subsequent git op. A bare `/karta-pipeline` invocation passes
no path and operates in-place exactly as today.

## Before Starting — inherited unchanged

**Lane gate (first, before anything else).** Read the project's project guide
§"Pipeline Preferences" for a `Lanes:` key (`keel-only | both`; absent ⇒ `both`,
the least-assuming default — both lanes available is the common case). If
`Lanes: keel-only`, the project restricts work to the full-rigor `keel-*` lane,
so this skill must not run → HALT (P7): *"this project sets `Lanes: keel-only`,
restricting work to the full-rigor `keel-*` lane; run `/keel-refine` →
`/keel-pipeline WI## <binder>` instead."* Absent or `Lanes: both` → proceed.
The knob only **restricts**; it never lowers a floor. Policy:
`docs/process/KARTA-LANE.md` §"The lane knob".

The preflight is inherited **unchanged** from `keel-pipeline` §"Before
Starting": read the project guide, read the feature title, resolve the feature
(sub-step 3.a) and `init` routing (sub-step 3.b), the **clean-tree check**,
the local-trunk base-branch resolution, the per-Need dependency classification,
the branch-collision check, and **cutting the per-feature branch** from the
**resolved stack target or local trunk** (keel-pipeline's
`<parent_branch_or_base>`, the "Create the feature branch" item). Two `init`
deltas — and only these two:

- Initialize routing with `--pipeline karta` (a lean-lane label; the lane is
  the command, not a stored mode). This selects the lean validation surface —
  `validate-handoff.py` expects no designer / reviewer / `landing-verifier`
  files for `karta`. The green gate is run **directly by the orchestrator**
  (see the green gate below), not by `landing-verifier`.
- Pass `--review-panel none` — Karta runs no review panel, so there is no
  Step 0.5 panel selection.

Everything else — the resolver, the clean-tree refusal, the dependency
classification and its halts, the single per-feature branch — is the
`keel-pipeline` preflight verbatim. Do not re-author any of it here. Karta
runs this preflight **once for the one feature**.

When invoked with `--stack` or under `Branching policy: stack`, the inherited
preflight resolves the stack target from the unmerged intra-Binder Needs exactly
as `keel-pipeline` §"Stack target resolution" specifies (base-on-trunk,
stack-on-tip, chain, or fan-out HALT), records `parent_branch`/`parent_sha` via
`keel-routing.py set-branch`, and restacks on a merged parent. Karta re-authors
none of this — it inherits keel's branching behavior in full. The lane lands via
the inherited Step 9.

## The lean gate map

`keel-pipeline` runs the full chain (pre-check → designers → researcher →
arch-advisor-consult → test-writer → implementer → the four parallel review
gates → landing-verifier → three review panels → post-landing).
`karta-pipeline` runs the lean **spec-first** map for the one feature:

```
pre-check → implementer → karta-spec-reviewer → safety-auditor → green gate → complete
```

(The two write-time **sign-off halts** — `KARTA-PLACEHOLDER` / `KARTA-GUARD` —
fire *during* the implementer, before a fake or a destructive effect is
written, not as a separate stage; see §"The halt set".)

**The structural conformance gate — `karta-spec-reviewer` (the spec-first
gate).** Karta is **spec-first**: the implementer builds from the Binder
`contract`/`oracle`, and this gate — run between `implementer` and
`safety-auditor` — is the lane's one **spec-side** blocking review. It is a
**delta of `spec-reviewer`** (the karta-spec-reviewer agent master):
inspection-only, it classifies each oracle assertion as inspection-verifiable or
execution-required, judges the former by reading, and forces the latter to be
test-covered or `KARTA-DEFER`-declared — never silently passing one. Dispatch it
via the inherited per-hop protocol; it writes `karta-spec-reviewer.md` and its
verdict is recorded with `keel-routing.py set-gate <dir> conformance <verdict>
<attempt>` (recorded verdicts: `CONFORMANT | DEVIATION | SPEC-SUSPECT`). A
`BLOCKED` envelope (missing input or write failure) is **not** a recorded gate
verdict — it halts the run without `set-gate`, exactly as `spec-reviewer`'s
BLOCKED does; re-run after fixing the input.
**Budget: max 2 attempts**, looping back to `implementer` on DEVIATION (see
§"The halt set" for the final-DEVIATION and SPEC-SUSPECT halts). It is the
**structural conformance** gate, never "primary acceptance" — the green gate is
the runtime floor. Lane policy: `docs/process/KARTA-LANE.md`.

**Reused unchanged (cite the `keel-pipeline` section; never copy):**

- **`pre-check`** — `keel-pipeline` §"Step 1: Pre-check". Dispatched via the
  inherited per-hop protocol; writes `pre-check.md`; its
  `routing_hints.metadata` flags are recorded with `set-routing`. Karta
  *reads* the flags but routes differently (see §"The halt set").
- **`implementer`** — `keel-pipeline` §"Step 4: Implementer", when
  `implementer_needed: YES`. Same dispatch, same `implementer.md` with the
  `**Changed paths:**` list.
- **`test-writer` — optional, and never test-*first*.** Karta is **spec-first**:
  the implementer builds from the Binder `contract`/`oracle`, and tests are
  **secondary**. There is no test-writer-before-implementer hop. Tests, when
  written at all, are authored by the implementer (or a later optional pass) —
  but **never** by editing an inherited test (a prior feature's contract; see
  `implementer.md` §Rules),
  and are *owed* only where `karta-spec-reviewer` requires them — an
  **execution-required** oracle assertion that is neither test-covered nor
  `KARTA-DEFER`-declared (see §"The structural conformance gate" above and
  KARTA-LANE.md §"Declare-and-owe"). The absence of a `test-writer.md` is
  expected, not a per-hop verification failure.
- **`safety-auditor`** — the **one kept Step-5 gate**, run **before** the
  green gate so any safety-driven fix is re-greened. Cite `keel-pipeline`
  §"Step 5: Parallel review gates" for its dispatch and budget: verdict
  `PASS | VIOLATION`, **max 3 attempts, never negotiable**, always dispatched
  at the high-reasoning tier, routing gate name `safety`, looping back to `implementer` on
  VIOLATION. The other three Step-5 gates (`code-reviewer`, `spec-reviewer`,
  `arch-advisor-verify`) are **dropped** — do not dispatch them and do not
  repeat Step 5's multi-gate consolidation logic. Karta runs exactly one gate,
  so there is no parallel-gate slot to consolidate.

**The green gate — a direct orchestrator step, not an agent dispatch.** After
`safety-auditor` is PASS, the orchestrator runs the project's **configured gate
command** (its tests/build) and checks it is green. **Source the command the
same way the maintenance lane does** — the project's test/build command as
documented in its project guide (`docs/process/PIPELINE-DOCTRINE.md` §"The
maintenance lane" → "How it lands" step 4: *"Run the project's configured gate
command (tests + lint). It must pass."*). It must be an **actual runnable
command** — not a placeholder, an example for a different language, or a
comment. **Before running it, reject a known no-op.** The Karta green gate is
the *sole* catch for structural breakage (a bad import, a type error) when
tests are deferred (KARTA-LANE.md §"Green-gate note"), so a gate command that
does nothing cannot stand in for it. If the configured command, trimmed of
surrounding whitespace, is one of the enumerated trivial forms — exactly `true`,
exactly `:`, exactly `exit 0`, a bare `echo` whose only argument is a literal /
whitespace string (e.g. `echo`, `echo ok`, `echo "skipping"`), or empty /
whitespace-only — HALT (P7): *"the configured Karta green-gate command `<cmd>`
is a no-op; the green gate is the lane's only structural-breakage catch when
tests are deferred, so a no-op is rejected — configure a real build / typecheck
/ test command in the project guide, then re-run `/karta-pipeline WI## <binder>`."* This
is the only command-content check the orchestrator makes — it matches the
enumerated trivial forms by inspection and does **not** attempt to assert that a
non-trivial command actually "builds" (that is the command's job; a
runnable-but-non-building command is owned-but-open, per KARTA-LANE.md, never
papered over). Karta does **not** dispatch `landing-verifier` for this — there is no
agent hop, no `.test_tooling.verify_command` dependency, and no
`landing-verifier.md` artifact; the orchestrator runs the command itself. On
**GREEN** (the command exits zero) → record the result on the commit (§"Completion",
the green-gate delta) and proceed. On **RED** (non-zero) → HALT (P7) with the failing output,
naming the feature; a within-feature `implementer` re-dispatch — which re-enters
the gate sequence at `safety-auditor` — is the normal repair. If the project guide
documents **no runnable** gate command (absent, or only placeholder/comment/
wrong-language text) → HALT (fail-closed): the green gate cannot be verified, so
the feature cannot land. The green gate is a *floor*, not a knob — it never
narrows, the way `safety-auditor` never does.

**Dropped entirely:** the design agents (`backend-designer` /
`frontend-designer`), `code-reviewer`, the keel `spec-reviewer` (**replaced by
its delta `karta-spec-reviewer`** — see above), `arch-advisor-consult`,
`arch-advisor-verify`, `researcher`,
**`landing-verifier`** (the green gate is a direct command, not a verifier
dispatch — no `landing-verifier.md` is written in this lane), and the three
review panels (pre-check / design / landing). arch-advisor is redundant here —
bones-clean admissibility already halts any cut on the bones (KARTA-LANE.md
§"Bones-clean admissibility"). The **kept mechanical gates** are therefore: the
**`karta-spec-reviewer`** structural conformance gate, the
`safety-auditor` gate, the **green gate** (the project's configured gate
command), and the two write-time sign-off halts.

## Completion — inherited Step 9 (repo-local), with one explicit delta

Karta completes the one feature via `keel-pipeline` §"Step 9", which is
**repo-local** — no forge in the loop: doc-gardener GC → tech-debt log → backlog
`[ ]`→`[x]` tick → `feat(WI##): …` commit with the verdict block → **archive**
the handoff directory to `completed/` (folded into the feature commit by
`git commit --amend` — a plain local amend; the archive location is the done
signal). There is **no push, no PR, no PR-URL recording** — pushing and opening
PRs are ceremony that lives in the separate human-invoked `/keel-submit`. Do not
re-author the commit/amend/archive mechanics here — because Karta runs one WI
per invocation, the standard single-feature completion flow works as-is.

**Trigger.** `keel-pipeline` Step 9's **Karta-variant arm** fires when the
recorded gate verdicts `gates.safety.verdict == PASS`
and `gates.conformance.verdict == CONFORMANT` are both present in `routing.json`,
read directly (no routing `status` latch; the old landing-status latch is
retired framework-wide), AND the green gate ran GREEN this session. `gates.safety`
(alongside `gates.conformance`) is the first-instance routing record karta writes
via `set-gate`. The green gate is the direct-command result and writes **no**
routing verdict (`gates` has no `green` key — see the green-gate delta below);
its only durable
record is the commit verdict-block line, and a halt before commit just re-runs
the cheap command on resume. There is no Step-8.5 landing review in this lane and
no status to set before Step 9.

**The one delta — the green-gate line in the verdict block.** Step 9 builds the
commit verdict block from the gate verdicts recorded in `routing.json`. The
`safety` verdict is there — mirrored via `keel-routing.py set-gate <dir> safety
PASS <attempt>` exactly as `keel-pipeline` records it — so its line is emitted
automatically. The **green gate has no routing verdict** (it is a direct
command, like the maintenance lane's; `gates` has no `green` key), so
`karta-pipeline` adds **one explicit line** to the commit verdict block:
`green-gate: PASS (<command>)`, naming the command it ran. The dropped gates
emit no line. (Re-running the green gate is cheap, so it needs no durable
routing verdict — a halt before commit just re-runs the command on resume.)

## The halt set

`karta-pipeline` advances automatically; absent a halt it never asks. It
HALTs with a call-to-action (P7) only on:

1. **A sign-off marker** — writing a `KARTA-PLACEHOLDER` (any mock/stub/fake)
   or `KARTA-GUARD` (any destructive, irreversible, or PII/secret-touching
   effect, regardless of whose infra hosts it) **halts for a human OK
   before it is written**, then proceeds once confirmed. A plain
   `KARTA-DEFER` does **not** halt — declare it and keep moving. Mechanics:
   KARTA-LANE.md §"The two human-OK sign-off gates".
2. **A RED, no-op, or unconfigured green gate** — the project's configured
   gate command (its tests/build, from the project guide) exits non-zero, and a
   within-feature implementer re-dispatch (re-entering at `safety-auditor`)
   cannot make it green → HALT (P7) with the failing command output, naming the
   feature. A project with **no** gate command configured also halts here
   (fail-closed): the green gate cannot be verified. A configured command that
   is a **known no-op** (the enumerated trivial forms — `true`, `:`, `exit 0`, a
   bare `echo` of a literal, or empty/whitespace) halts **before** the command
   runs: the no-op cannot stand in for the lane's sole structural-breakage catch
   — configure a real build/typecheck/test command in the project guide (§"The lean
   gate map"). The green gate is a floor; it never relaxes.
3. **A safety-auditor VIOLATION past budget** — VIOLATION after 3 attempts
   on the kept Step-5 gate → STOP, escalate to human (the invariant rule or
   spec may need review). **safety-auditor is NOT a halt trigger by running —
   it always runs in this lane**; only an unresolved VIOLATION past its budget
   halts.
4. **A `karta-spec-reviewer` DEVIATION past budget, or a SPEC-SUSPECT.** The
   structural conformance gate loops back to `implementer` on DEVIATION with a
   **max of 2 attempts**. A DEVIATION still unresolved after attempt 2 → HALT
   (P7) emitting the unresolved oracle-assertion JSON-Pointer paths, the command
   to view `karta-spec-reviewer.md`, and the options (fix-and-rerun the
   implementer; `KARTA-DEFER` the cut; or route to `/keel-pipeline` for full
   test-first rigor). A **SPEC-SUSPECT** verdict (the code looks correct but the
   Binder appears stale) → HALT for human adjudication; the Binder is amended via
   `/keel-refine`, never hand-edited. Like `safety-auditor`, this gate **always
   runs** in the lane — its running is never the halt; only an unresolved
   DEVIATION past budget or a SPEC-SUSPECT halts.
5. **An inadmissible (bones) cut** — a shortcut that would change a
   signature, schema, module boundary, transaction edge, or auth guard that
   other code depends on. HALT; restructure the cut into leaf code behind a
   stable contract, or route the change to `karta-refine`/`keel-refine`. Test:
   KARTA-LANE.md §"Bones-clean admissibility".

   > **Stack-parent bones.** If a stack parent carries a `KARTA-DEFER`/`KARTA-GUARD` on **bones** (a signature, schema, module boundary, transaction edge, or auth guard) the child builds on, HALT (P7): the child would stack on an unstable contract under the lean review surface — harden the parent through `/keel-refine` → `/keel-pipeline` first, or restructure the cut.
6. **An unresolvable failure** — a feature that cannot be built or made to
   pass even its relaxed gates. HALT naming the feature and the failure.
7. **A lean-routing flag** — if `pre-check` flags `designer_needed`,
   `researcher_needed`, or `arch_advisor_needed` **YES**, this feature wants
   full-rigor machinery the lean lane deliberately drops. HALT (P7):

   > *"`pre-check` flagged WI## as needing
   > {designer|researcher|arch-advisor} — the Karta lean lane drops those
   > agents. Either narrow the feature's scope so the lean map suffices, or
   > run it through `/keel-pipeline WI## <binder>` for full rigor."*

   `safety_auditor_needed` is **not** a lean-routing halt — `safety-auditor`
   always runs in this lane regardless of the flag.

On any halt the run **stops cleanly**, exactly as `keel-pipeline` does: the
feature's handoff stays in `active/`, the feature branch is left in place,
nothing is committed past the halt. The halt CTA names the cause and the
concrete repair; the human resolves it and **resumes by re-running**
`/karta-pipeline WI## <binder>` — the inherited re-run handling (`keel-pipeline`
§"Re-run handling") picks up from the recorded routing state.

## Rules

- **Declare every cut.** An undeclared shortcut is the lane's cardinal
  violation (KARTA-LANE.md §"Declare-and-owe"). If you cut a corner, you mark
  it; no exceptions.
- **The bones stay clean.** Cuts live only in leaf code behind a stable
  contract. A cut on the data model, a cross-module contract, a transaction
  edge, or an auth guard halts (halt 4 above).
- **The green gate is a floor, not a toggle.** The orchestrator runs the
  project's configured gate command (its tests/build, from the project guide) before
  the feature lands; RED, no command configured, or a known-no-op command (the
  enumerated trivial forms) all halt (§"The lean gate map"). The lane trades
  away thoroughness of *implementation*, never a green build.
- **safety-auditor always runs; it is the floor, not a toggle.** The lane
  trades away thoroughness of implementation — never safety or architectural
  integrity.
- **One feature per invocation, completed repo-locally.** Karta runs one WI per
  invocation and completes it via the inherited `keel-pipeline` §"Step 9" —
  committed on its branch and archived, no push or PR (that is `/keel-submit`).
  Single-feature stacking on an unmerged intra-Binder dependency is inherited
  from keel (see the inheritance clause / `--stack`); sequencing a selected set
  of features in dependency order is `/karta-drive` — `karta-pipeline` still
  runs once per feature.
- **The orchestrator owns routing, agents write the code, and you verify the
  filesystem (not the prose).** These orchestration rules are inherited
  unchanged from `keel-pipeline` §"Rules"; this skill does not restate them.
- **Hardening is a separate path.** A clean ledger is not a hardened path. A
  Karta feature becomes production-grade only by being hardened through
  `keel-refine` → `keel-pipeline`, where the spec is derived from each
  marker's `real:` clause (KARTA-LANE.md refusal protocol, final row).
