# Handoff Contract — doctrine

A KEEL feature's handoff is not a file. It is a **per-feature
directory** at `docs/exec-plans/active/handoffs/WI##-<slug>/`. Three
orchestrator-owned files hold all routing state; one file per
contributing agent holds that agent's work product. This doc defines
who writes what, what each agent returns, and how the orchestrator
verifies a hop before advancing.

## Why this contract exists

The pipeline's control plane (which agent ran, what verdict, whether to
kick back) and its work product (briefs, blueprints, findings) are
different kinds of data. Routing is field-shaped, read field-by-field by
the orchestrator; work product is prose absorbed wholesale by the next
agent. A single shared markdown file forced both into the wrong
substrate and made two agents writing it concurrently a race. This
contract separates them:

- **Lean orchestrator context.** Routing lives in `routing.json`,
  schema-validated, mutated through one helper. The orchestrator never
  greps prose to learn pipeline state.
- **Self-writing agents.** Every agent that produces work product writes
  its own `<agent>.md` with the `Write` tool — a full-file overwrite, no
  exact-match fragility, no shared-file race. There is one write
  contract for all agents, not four.
- **Deterministic routing state.** Updates go through
  `scripts/keel-routing.py`, which validates against the schema on every
  write. Typos and impossible transitions halt loudly instead of
  silently corrupting the control plane.

## The three orchestrator-owned files

Only the orchestrator (the `keel-pipeline` skill, running with shell
access) writes these. Agents may **read** them; agents never write them.

1. **`routing.json`** — pipeline state: status, variant, routing flags,
   gate verdicts, attempt counters, review verdicts, branch metadata,
   pretriage outcome. Mutated **only** via `scripts/keel-routing.py`
   (`init`, `set-gate`, `set-routing`, `merge-routing-flag`,
   `set-review`, `set-pretriage`, `incr-escalation`, and peers — run
   `keel-routing.py --help` for the full set). The helper takes an
   exclusive lock, applies the change, validates against
   `schemas/routing.schema.json`, and writes atomically. Never edit
   `routing.json` by hand. Two fields beyond the routing flags carry
   structural weight (both governed by `schemas/routing.schema.json`'s
   `allOf`):

   - **`source_hash`** — a write-once mirror of
     `resolved-work-item.json`'s `source_hash`, written by `init` **only**
     (no other subcommand updates it) and read by a later `init` to
     decide safe-merge vs. rebuild (see "Init: routing.json safe-merge
     boundary" below). **REQUIRED for non-bootstrap** pipelines, so its
     omission is a loud validation failure rather than a silent
     every-run derived-state wipe. P4: it is not a redundant cache of the
     resolver's value — it is the *prior-run* fingerprint init compares
     against; `resolved-work-item.json` remains the validator's authority
     for the *current* source state (`validate-handoff.py` recomputes the
     hash from the Binder/backlog/keel.json and checks it against
     `resolved-work-item.json`, not against this mirror).
   - **`bootstrap_agent`** — the bootstrap agent named in the backlog
     `Agent:` field (`scaffolder` | `config-writer`).
     **REQUIRED for `pipeline: bootstrap`** and absent otherwise; the
     validator reads it to know which single bootstrap agent file to
     expect. P4: it is the only place the chosen bootstrap agent is
     recorded in routing state — not derivable from any other field once
     the run is underway.

2. **`resolved-work-item.json`** — the deterministic output of
   `keel-work-item-resolve.py`: Binder slice, dependency classification,
   invariants, file paths, test tooling. Written **once at Step 0** and
   **immutable** thereafter. If it is wrong, fix the source (Binder or
   backlog) and re-run Step 0 — never patch this file. Schema:
   `schemas/resolved-work-item.schema.json`. (Bootstrap features have no
   Binder to resolve, so they omit this file.)

3. **`<touchpoint>-review/` deliberation subdirs** — one per review
   touchpoint (`precheck-review/`, `design-review/`, `landing-review/`).
   **Append-only**: each panel pass writes a new standalone
   `attempt-NN.md` (zero-padded; numbered from `01` with no gaps). Past
   attempts are content-immutable, guarded by SHA-256 hashes in a
   `.attempt-hashes.json` sidecar the orchestrator updates (via
   `keel-routing.py record-attempt-hash`) as the very next action after
   each attempt write. Read attempts in numeric order
   (`keel-query.py deliberation <dir> <touchpoint>` does the sort).

   The `.attempt-hashes.json` sidecar is **committed, write-once
   integrity state that moves with the archive.** Each entry is frozen
   when its attempt is written and is never rewritten; the file is
   committed alongside the attempt files and travels with the directory
   on the Step 9 `git mv` into `completed/handoffs/`. P4: it is a
   write-time hash record (a fingerprint frozen at write), **not** a
   cache derivable from current state — committing it is what makes the
   append-only guarantee real, because `validate-handoff.py
   docs/exec-plans/completed/handoffs/` is **fail-closed**: it HALTs when
   attempt files are present but the sidecar (or a per-attempt entry) is
   missing. There is no gitignore rule for it; do not add one.

## Init: routing.json safe-merge boundary

`keel-routing.py init` is the **only** writer of `routing.json`'s
identity fields and the `source_hash` mirror, and it is safe to re-run.
On re-invocation it branches three ways on the resolver's `source_hash`
(read from `resolved-work-item.json`). This is the authoritative
description of that branch; the keel-pipeline skill cites this heading.

| Condition | Behavior |
|-|-|
| `routing.json` absent | Create fresh. Seed identity (`feature`, `binder_ref`), `review_panel`, `source_hash`, and a neutral placeholder `routing` block. `init` does **not** write `pretriage` — the orchestrator records it via `set-pretriage` at first dispatch (keel-pipeline §"Per-hop dispatch protocol"). No merge concern. |
| Exists, `source_hash` **unchanged** | Safe-merge: **preserve** derived state (`gates`, `review`, `arch_retry`, `review_retry`, `precheck_escalation_count`, `status`, and an existing `pretriage` block if present — dropped from nothing); **refresh** identity (`feature`, `binder_ref`) and `review_panel`. |
| Exists, `source_hash` **changed** | Rebuild + wipe: INVALIDATE all derived state (clear `gates`, `review`, `arch_retry`, `review_retry`, and `pretriage`), delete stale on-disk agent/deliberation files, reset `precheck_escalation_count` to 0 (fresh budget for the new feature definition) and `status` to `IN-PROGRESS`, write fresh identity, and emit a P7 notice that the pipeline restarts at Step 1 against the new source. The orchestrator re-records `pretriage` at the next dispatch. |

`source_hash` comparison detects Binder edits, backlog edits to this
feature's entry, and security-sensitive-invariant set changes
(whitespace-insensitive — canonical JSON). Bootstrap features have no
resolver step, so init always safe-merges them on re-run and never
compares a `source_hash`.

## The envelope

Every **sequential** agent returns this terse object to the
orchestrator — and **only** this. It does not restate work product; the
prose lives in the agent's `<agent>.md`.

```yaml
verdict: pass | concerns | blocked
summary: "1-3 line plain-language outcome"
routing_hints:
  next: <agent-name> | null
  kickback_to: <agent-name> | null
  reason: "one-line rationale"
top_blockers: ["id-or-tag", ...]
wrote: "<filename>"        # advisory ack, e.g. "pre-check.md"
```

- **`wrote` is advisory.** It is the agent's claim of what it wrote; the
  orchestrator does not trust it — it verifies the file on disk (see
  Verification model). On a `Write` **failure**, the agent returns
  `verdict: blocked`, `top_blockers: ["write-failed"]`, a `summary`
  naming the cause, and **does not** claim `wrote:` for a file it failed
  to write.
- **Pre-check carries one extension.** Pre-check additionally returns a
  `routing_hints.metadata` block with the seven routing flags
  (`intent`, `complexity`, `designer_needed`, `researcher_needed`,
  `safety_auditor_needed`, `arch_advisor_needed`, `implementer_needed`)
  so the orchestrator can write `routing.routing` without reading
  pre-check's prose. No other agent uses `metadata`.

  **Envelope nesting vs. `set-routing` input — they differ in shape.**
  Pre-check's envelope **nests** these flags one level down, under
  `routing_hints.metadata`. But `keel-routing.py set-routing
  --from-envelope` consumes a **flat top-level mapping** of the same
  flags — it reads each flag from the YAML document's top level and
  HALTs (exit 4) if any of the seven is missing. The two shapes do not
  match, so the orchestrator does **not** pass pre-check's envelope to
  `set-routing` verbatim. Instead it **extracts** the
  `routing_hints.metadata` sub-block into a flat top-level mapping and
  passes *that* to `set-routing`. The flat shape `set-routing` expects
  is exactly:

  ```yaml
  intent: build
  complexity: standard
  designer_needed: false
  researcher_needed: false
  safety_auditor_needed: false
  arch_advisor_needed: false
  implementer_needed: true
  ```

  The orchestrator's exact extract-and-write sequence (and the worked
  example) lives in the keel-pipeline skill's per-hop protocol, step 3.

## Agent obligations

1. **Read upstream.** Use the `Read` tool on the files in your feature
   directory you need: `resolved-work-item.json` for the structured
   feature data, and any sibling `<agent>.md` for upstream context. You
   have no shell — do not reach for `jq` or scripts. Read only what you
   need (P2).
2. **Write your own file.** Use the `Write` tool to overwrite
   `<your-agent>.md` in full. On a kickback re-run you write the new
   file whole; `Write`'s atomic overwrite replaces the prior content.
   Never append to your own file; never use "was X, now Y" framing — the
   file is a snapshot of current state (P5).
3. **Return the envelope only.** Nothing else goes back to the
   orchestrator.
4. **Touch nothing else.** Never write `routing.json`, another agent's
   `<agent>.md`, a deliberation file, the backlog, the Binder, code, tests,
   or git state — unless your role explicitly owns that artifact.

## Orchestrator obligations per hop

For each sequential agent, in this order:

1. **Escalation special-case first (pre-check only).** If the envelope
   is `verdict: blocked` with `model-upgrade-needed` in `top_blockers`,
   handle it *before* verifying any file: skip write-verification (no
   file is expected), skip the routing update (the standard tier's flags
   are not authoritative), and `incr-escalation`. If
   `precheck_escalation_count` would exceed 1 → **HALT** with a CTA to
   tune the pretriage rule. Otherwise re-dispatch pre-check at the
   high-reasoning tier.
2. **Verify the file** (normal returns only): it exists, is non-empty,
   and its mtime advanced past the pre-dispatch mtime. Any check fails →
   **HALT** naming the agent, the expected path, and the failed check.
3. **Update routing** from the envelope via `keel-routing.py` (gate
   verdict → `set-gate`; review verdict → `set-review`). For pre-check,
   **extract** the flat seven-flag mapping out of the envelope's
   `routing_hints.metadata` sub-block and pass that flat mapping to
   `set-routing --from-envelope` (see "The envelope" above — the nested
   envelope shape is not what `set-routing` reads).
4. **Dispatch next** — the `routing_hints.next` stage, or the
   `kickback_to` target on concerns.

Parallel gates write their own files concurrently (no race); the
orchestrator verifies each file and serializes the `set-gate` calls
through the helper's lock.

## Verification model

The orchestrator verifies a hop by **inspecting the filesystem**, never
by grepping agent prose for a heading:

- **File checks:** the expected `<agent>.md` exists, is non-empty, and
  its mtime advanced. This is what proves an agent actually wrote, not a
  `wrote:` claim. `validate-handoff.py` enforces the full directory
  shape (expected files per routing flags, `attempt-NN.md` sequencing,
  sidecar hash integrity).
- **The envelope is authoritative on verdict.** The orchestrator writes
  `routing.json` from the **envelope's** `verdict`, not from the
  `**Verdict:**` line in the gate's file body. If a gate's file body
  disagrees with its envelope verdict, that is a correctness signal:
  **HALT** with a CTA to re-dispatch the gate for consistent output, or
  (if the human judges the body correct) set the verdict manually via
  `keel-routing.py set-gate` and remove the divergent line. Routing
  never silently proceeds on conflicting state (P7).
- **Pretriage-consistency bypass sentinels.** `validate-handoff.py`
  recomputes the pretriage score from `resolved-work-item.json`'s
  `pretriage_inputs` and HALTs if `routing.pretriage.recommended_model`
  disagrees with the recomputed model — **except** when
  `routing.pretriage.reason` contains the substring `self-escalated` or
  `backlog missing`. Those are the two legitimate-override sentinels: a
  pre-check self-escalation to the high-reasoning tier (score may be
  below the high-tier threshold) and a fail-safe-to-high-tier on a
  backlog entry missing structured pretriage inputs. When the
  orchestrator sets a pretriage
  override for either reason, it MUST keep one of those substrings in the
  `--reason` so the validator's scoring-rule check is bypassed rather
  than HALTing on a deliberate override. The bypass lives in the
  validator, not in `set-pretriage` (which stores `recommended_model`,
  `score`, and `reason` verbatim with no bypass logic of its own).

## Route-reset semantics

When a revised pre-check envelope (or a Step 1.3 panel routing-override)
flips a routing flag from **YES to NO**, downstream files written under
the old routing become stale and must be cleared *before* the pipeline
continues. NO→YES flips delete nothing — the newly-needed agent writes
its file when it is next dispatched. This is the algorithm the
keel-pipeline skill runs; it mirrors `validate-handoff.py`'s
`_compute_expected_file_set`.

1. **Recompute the entire expected file set** from the *new* routing
   flags — not just the file for the flipped flag. The reset is
   transitive: removing `implementer.md` also orphans the gate files
   (`code-reviewer.md`, `spec-reviewer.md`, and conditionally
   `safety-auditor.md` / `arch-advisor-verify.md`) that only exist
   because the implementer ran. The expected set is:
   - **Always:** `routing.json`, `resolved-work-item.json`, `pre-check.md`,
     `precheck-review/`, `landing-verifier.md`, `landing-review/`, and
     (after Step 9) `doc-gardener.md`.
   - `researcher_needed` → `+ researcher.md`.
   - `arch_advisor_needed` → `+ arch-advisor-consult.md` (and
     `arch-advisor-verify.md` once Step 5 has run with
     `implementer_needed` too).
   - backend pipeline AND `designer_needed` → `+ backend-designer.md`,
     `design-review/`.
   - frontend pipeline → `+ frontend-designer.md`, `design-review/`.
   - `implementer_needed` → `+ implementer.md`, `code-reviewer.md`,
     `spec-reviewer.md` (`+ safety-auditor.md` if `safety_auditor_needed`;
     `+ arch-advisor-verify.md` if `arch_advisor_needed`).
2. **Delete obsolete state.** For each `*.md` file or
   `<touchpoint>-review/` subdir in the directory that is NOT in the new
   expected set, delete it.
3. **Clear the matching routing entries.** Order matters — delete the
   on-disk files FIRST (step 2), then clear routing state:
   - For each gate whose file was deleted, run
     `keel-routing.py clear-gate <dir> <code_review|spec_review|safety|arch_verify|conformance>`
     (`merge-routing-flag` only touches `routing.routing.*`; gate
     verdicts live at `routing.gates.*`).
   - For each deliberation touchpoint whose subdir was deleted, run
     `keel-routing.py clear-review <dir> <precheck|design|landing>`
     (resets that touchpoint to `{attempt: 0, verdict: null}`).
4. **Log the reset** in the `precheck-review/attempt-NN.md` block being
   written: `route-reset: deleted <files>; cleared <routing entries>`.

## Per-agent model selection

Model tier is **decoupled from a single pretriage signal** so one
pretriage miss cannot downgrade every defense layer at once. Each agent
master declares its DEFAULT tier; the orchestrator's dispatch may
escalate an agent to the high-reasoning tier per the table below. The
orchestrator reads `routing.pretriage.recommended_model` and applies this
table:

**The pretriage rule.** `recommended_model` is `opus` iff the weighted
score over `resolved-work-item.json`'s `.pretriage_inputs` is ≥ 2, where
weights are `cross_module_touch=1`, `security_sensitive_inv=2`,
`novel_dependency=2`, `frozen_seam_impact=1`, `architecture_tier_hint=3`
(a truthy signal contributes its weight; this is a weighted sum, not a
flat OR). `validate-handoff.py` enforces consistency against this exact
rule and must stay in sync with it.

| Agent | Default | Override |
|-|-|-|
| `pre-check` | standard | high-reasoning tier when `pretriage.recommended_model == opus`; self-escalates to the high tier via `top_blockers: ["model-upgrade-needed"]` |
| `researcher` | standard | high-reasoning tier when `pretriage.recommended_model == opus` |
| `arch-advisor-consult` | **high** | always high-reasoning — only runs under architectural risk |
| `arch-advisor-verify` | **high** | always high-reasoning — same reasoning |
| `backend-designer` / `frontend-designer` | **high for standard+** complexity; standard tier only for trivial | decoupled from pretriage — designer is on the critical path; a cheap-tier blueprint kickback erases the right-sizing win |
| `test-writer` | standard | per pretriage (high-reasoning tier when `recommended_model == opus`) |
| `implementer` | standard | high-reasoning tier when `pretriage.recommended_model == opus` |
| `code-reviewer` | standard | high-reasoning tier when `pretriage.recommended_model == opus` |
| `spec-reviewer` | standard | high-reasoning tier when `pretriage.recommended_model == opus` |
| `safety-auditor` | **high** | always high-reasoning when the gate runs (conditional on `safety_auditor_needed`; do not depend on pretriage agreeing) |
| `landing-verifier` | standard | standard tier always (mostly tool execution) |
| `doc-gardener` (pipeline + ad-hoc) | standard | standard tier always (sweep is mostly file walking) |
| review panel — **Architect, Adversary** lenses | **high** | always high-reasoning — the safety net against confident misroutes |
| review panel — **Skeptic, Pragmatist** lenses | standard | high-reasoning tier when `pretriage.recommended_model == opus` |

Always high-reasoning regardless of pretriage: `arch-advisor-consult`,
`arch-advisor-verify`, `safety-auditor` (when it runs),
`backend`/`frontend-designer` for standard+ complexity, and the
Architect + Adversary panel lenses. Everywhere else pretriage controls.
Bootstrap agents (`scaffolder`, `config-writer`) stay
on the standard tier.

## P1-P7 audit

- **P1 (legibility):** one directory per feature, one file per agent,
  routing as named JSON fields; agents read inputs by filename, not by
  parsing a monolith.
- **P2 (progressive disclosure):** the directory is the table of
  contents; agents `Read` only the siblings they need; the envelope is
  the minimal hop summary.
- **P3 (self-sufficient):** the directory's files fully reconstruct the
  feature's state; `keel-query.py` is a possible synthesizer, not a
  required cache.
- **P4 (no redundant storage):** routing lives only in `routing.json`,
  resolver data only in `resolved-work-item.json`, prose only in
  `<agent>.md`; no field is duplicated. `.attempt-hashes.json` is a
  committed write-time hash record (a fingerprint frozen when each
  attempt is written, not a cache derivable from current state), so it
  is authored integrity state, not a stale-able derivation; `source_hash`
  is the prior-run fingerprint init compares against, not a duplicate of
  the resolver's current value.
- **P5 (snapshot, not timeline):** agents overwrite their file whole;
  deliberation appends per-attempt files rather than editing history;
  no changelogs or "was X, now Y" in any body.
- **P6 (code/specs/backlog win):** `resolved-work-item.json` is derived
  from the Binder and backlog and fixed by re-running Step 0, never
  patched; the envelope verdict governs routing over any prose
  restatement.
- **P7 (halt with call-to-action):** every verification failure,
  escalation cap, and verdict divergence halts with the exact cause and
  a concrete next step — no silent fallthrough.
