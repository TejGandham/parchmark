---
name: karta-drive
description: "Build a Karta binder's remaining work items through `/karta-pipeline` in dependency order, each in its own git worktree, fail-fast. Done is repo-local — code on the WI's branch, handoff archived, backlog [x]; never a forge. Pure sequencer — owns order + selection; never merges or pushes, stores nothing. Args: `/karta-drive <binder>` (whole remaining binder) or `/karta-drive <binder> WI09,WI10,WI11` (narrowed)."
---

# Karta Drive (batch sequencer)

`karta-drive` builds a Binder's **remaining** work items (or a narrowed
sub-set) through `karta-pipeline` in dependency order, **each in its own git
worktree**, stopping at the first failure. It is a **pure sequencer**: it owns
*order and selection*; `karta-pipeline` (which it dispatches once per WI) owns
*stacking, gates, completion*. **Done is repo-local** — a WI is done when its
code is committed on its `keel/WI##-<slug>` branch, its handoff is archived to
`docs/exec-plans/completed/handoffs/`, and its backlog entry is `[x]`. No forge
is in the loop: pushing and opening PRs are ceremony that lives in the separate
human-invoked `/keel-submit`. The driver **never merges, never pushes, never
re-authors a per-WI mechanic, and stores nothing** — order, frontier, and
completion are re-derived from repo state every run.

This skill is a **delta of `karta-pipeline`**, not a fork (P4 — skills are
deltas, not forks). It re-authors none of the per-WI machinery: stacking, the
lean gate map, the halt set, and completion all live in
[the karta-pipeline skill](../karta-pipeline/SKILL.md) and are
cited below, never restated. Design provenance:
[`docs/design-docs/mvp-lane/2026-06-03-repo-local-done-design.md`](../../../docs/design-docs/mvp-lane/2026-06-03-repo-local-done-design.md)
§"Part 3".

## Framework principles

Every halt here uses P7 (call-to-action) wording, exactly as `karta-pipeline`.
Conflict resolution follows P6 — DONE reads backlog/branch reality, never a
narration of "last completed". See
[`docs/process/KEEL-PRINCIPLES.md`](../../../docs/process/KEEL-PRINCIPLES.md).

## Orchestration rules — inherited

The orchestration rules — **the orchestrator owns routing, agents write the
code, and you verify the filesystem (not the prose)** — are inherited
**unchanged** from `keel-pipeline` §"Rules" via `karta-pipeline` §"Rules". This
skill adds only the *cross-WI* sequencing layer; it does not restate them.

## The eight-step flow

`karta-drive` advances automatically; absent a halt it never asks. Each step
below either proceeds or HALTs with a specific P7 call-to-action.

### 1. Lane + stack gate

Read the `Lanes:` knob exactly as `karta-pipeline` §"Before Starting" does
(the project guide §"Pipeline Preferences"; `keel-only | both`, absent ⇒ `both`). If
`Lanes: keel-only` → HALT (P7): *"this project sets `Lanes: keel-only`,
restricting work to the full-rigor `keel-*` lane; the Karta driver cannot run —
run the WIs through `/keel-refine` → `/keel-pipeline WI## <binder>` instead."*
Absent or `both` → proceed. Policy: `docs/process/KARTA-LANE.md` §"The lane
knob".

The driver **implies stacking for its run**: every per-WI dispatch in step 7
passes `--stack`. This is a **transient per-run directive**, not a persistent
knob — invoking `/karta-drive` *is* the intent to stack, so the directive
overrides the persistent `Branching policy` default for this run only; bare
`/karta-pipeline` runs keep following the stored knob. No "forbid stacking"
knob is added (a project that does not want stacked autonomous runs simply does
not invoke the driver — it fails the two-org test).

### 2. Arguments

```
/karta-drive docs/exec-plans/binders/my-feature.json
/karta-drive docs/exec-plans/binders/my-feature.json WI09,WI10,WI11
```

One structured **JSON** Binder path. **The whole binder is the default**: a bare
`/karta-drive <binder>` selects every work item in the binder (step 3 narrows it
to the *remaining* ones — backlog authority filters first, P6). An optional
comma-separated WI list **narrows** the run to those ids; each must match the
Binder's `work_items[].id` verbatim (the helper compares strings literally).
Narrowing reduces an already-granted authority — it never re-confirms. A
non-JSON or missing Binder gets the same **`/karta-refine`-first** HALT the
pipelines use (`karta-pipeline` §"Arguments": Karta's authoring sibling is
`karta-refine`, which emits the JSON shape).

### 3. Select — the remaining binder (or the narrowed set), no interactive confirm

The candidate set is the binder's WIs (or the narrowed list from step 2). From
it, **derive the *remaining* set**: drop every WI whose backlog entry is already
`[x]` (read `docs/exec-plans/active/backlog.md` from the trunk ref — see step 5
on anchoring; the trunk-side tick is the merged-and-done signal). **Backlog
authority filters before Binder membership (P6)** — a `[x]` WI is done and is
never rebuilt, whichever lane built it.

Print the derived selection as the run's **authorization record (P1)** — one row
per candidate, `build` / `skip(done)`, in the helper-derived order (step 4):

```
WI   | action     | reason
WI09 | skip(done) | backlog [x]
WI10 | build      | next
WI11 | build      | needs WI10
```

There is **no interactive confirm**. Printing the derived set *is* the legible
record; the human already authorized the run by invoking `/karta-drive` (asking
without choosing is the non-default the defaults+knobs rule rejects). A narrowed
list never re-confirms — it reduces an already-granted authority. If the
remaining set is empty (every candidate is `[x]`), print the table and the
terminal CTA (step 8) — there is nothing to build.

### 4. Validate (before any pipeline runs)

In order, before any WI is dispatched:

1. **`uv run scripts/validate-binder-json.py <binder>`** first — it is PEP 723
   with a `jsonschema` dependency, so a bare `python3` run fails on import; `uv
   run` is required. An invalid Binder (including any cross-Binder `needs[]`
   ref, which the schema forbids) is a clean upstream HALT here, not a
   misleading downstream pre-check failure.
2. **Order + subgraph checks** via the Task-1 helper:

   ```
   uv run scripts/keel-drive-order.py --order --binder <binder> --set WI09,WI10,WI11
   ```

   - `halt:cycle` → HALT (P7) naming the cycle (`cycle_candidates`);
   - `halt:missing` → HALT (P7) naming the absent WI(s) — a WI not present in
     the Binder dies here, not downstream.

   On success the helper returns `order` (the deterministic topological order,
   ascending-WI tie-break) and `external_needs` (per-WI `needs[]` that resolve
   in the Binder but fall **outside** the selected set). The driver adds **no**
   ordering or classification logic of its own — order is the helper's.
   For a **whole-binder** run `external_needs` is empty by construction; it is
   non-empty only for a **narrowed** run.
3. **`external_needs` floor (narrowed runs only)** — for each external-need WI,
   it must be **done** already (built or merged), or the narrowed set omits an
   unbuilt in-binder prerequisite. External WIs have no slug to interpolate, so
   determine done-state **without a slug**, anchored to **trunk** never the
   working tree: done iff a branch resolved by the `keel/WI##-*` prefix (local
   refs, as `keel-pipeline` §"Classify each Need" → "Branch existence" resolves
   branches by WI prefix) is an ancestor of trunk, **or** — when no branch ref
   remains — `git show <trunk>:docs/exec-plans/active/backlog.md` shows `[x]`
   **and** `git ls-tree <trunk> --name-only docs/exec-plans/completed/handoffs/`
   matches `WI##-*`. If any external need is **not done** → HALT (P7), and
   **compute the closure to author the resume command**: run
   `uv run scripts/keel-drive-order.py --order --binder <binder> --set <set ∪ all unbuilt external-need WIs>`
   to topo-order the enlarged set, then emit the CTA naming the missing
   predecessor(s) and the exact widened invocation, e.g.: *"WI11 needs WI09 and
   WI10, which this narrowed run omits and which are not built. Re-run with the
   closure: `/karta-drive <binder> WI09,WI10,WI11`."* (This is where the retired
   closure flag's job now lives — the P7 CTA at zero entry-point surface.)

### 5. DONE predicate (per WI, repo-local, anchored + ref-guarded)

Done is **repo-local**: a WI is done when three repo-derivable signals agree —
code committed on its `keel/WI##-<slug>` branch, the handoff archived under
`docs/exec-plans/completed/handoffs/`, and the backlog entry `[x]`. No forge is
consulted (P3 — the repo reconstructs done with no remote). The archive + `[x]`
are **committed on the WI's own branch** by `karta-pipeline`'s completion step
and reach trunk only when a human merges, so they must be read from the right
**anchor**, **never the working tree**: a fresh trunk checkout shows `[ ]` for
*every* in-flight WI — that is normal stack state, not "not built"; and a stack
checkout *inherits* a prerequisite's archive + `[x]`, so a working-tree read
false-passes after a non-trunk merge-then-delete.

First resolve the WI's branch by the `keel/WI##-*` prefix (local refs, exactly
as `keel-pipeline` §"Classify each Need" → "Branch existence" resolves branches
by WI prefix), **ref-guarded**: `git rev-parse --verify --quiet <ref>` before
any use — **never run `is-ancestor` on a missing ref** (exit 128). Then a WI is:

- **DONE (skip it)** =
  - **merged-to-trunk**: the resolved branch is an ancestor of trunk
    (`git merge-base --is-ancestor` — the lane *reads* merges, never makes
    them); **or**
  - **branch-anchored**: the branch exists (unmerged) **and, read from that
    branch ref** — `git show <branch>:docs/exec-plans/active/backlog.md` shows
    the entry `[x]`, and `git ls-tree <branch> --name-only
    docs/exec-plans/completed/handoffs/` matches `WI##-*` — the WI is built and
    stacked. Skip it; step 6 guards its tip. **or**
  - **trunk-anchored fallback**: **no branch ref remains** (a squash-merge
    cleanup deleted it) — read the signals **from the trunk ref**
    (`git show <trunk>:docs/exec-plans/active/backlog.md` shows `[x]` **and**
    `git ls-tree <trunk> --name-only docs/exec-plans/completed/handoffs/`
    matches `WI##-*`), **never the working tree** (a stack checkout inherits a
    prerequisite's archive + `[x]`, so a working-tree read false-passes after a
    non-trunk merge-then-delete).
- **Half-built → re-dispatch (not a halt, not a skip)**: the branch exists but
  the branch-anchored signals are absent — the pipeline cut the branch at
  Step 0, then halted mid-build. The WI is NOT done; dispatching it (step 7)
  re-enters `karta-pipeline`, whose re-invocation handling **resumes** the
  existing branch when its `active/` handoff survives, or **HALTs with its
  branch-without-handoff repair CTA** when it does not — the driver surfaces
  that nested halt fail-fast, per step 7. (A bare branch-exists test would
  wrongly skip these — the anchor is what distinguishes built from
  half-built.)
- **Contradiction (a) → HALT (P7)** — evaluated on the same anchor: handoff
  archived but backlog `[ ]` (the WI was deliberately reopened) → *"WI## has a
  completed handoff but its backlog entry is reopened — rebuild it (delete the
  stale handoff and re-run) or reconcile the backlog before resuming."*
- **Contradiction (b) → HALT (P7)**: backlog `[x]` but the handoff is **not**
  archived under `completed/` **and** the branch is **not** merged (a hand-ticked
  box, or a completion halted mid-archive — see the crash-window recovery the
  completion step owns) → *"WI## is ticked `[x]` but neither archived nor merged
  — finish the archive step or reconcile the backlog before resuming."*

Reopening a built WI is always an **explicit repo edit** (delete the stale
handoff, or flip the backlog) — there is no forge in the loop, so there is no
forge-rejection signal to interpret. The contradiction halts above name the
exact reconciliation.

### 6. Stack-integrity preflight (per not-DONE WI with an existing branch)

Fail-fast leaves a **partial stack** on a halt; between runs a human may merge
or rewrite a lower branch out-of-band. keel restacks on parent *merge* but not
on parent *move*, so before running each not-DONE WI that already has a branch
(resolved by the `keel/WI##-*` prefix as in step 5), read its recorded parent
fields (resolve `<handoff_dir>` by the `*/handoffs/WI##-*` prefix, active or
completed):

```
uv run scripts/keel-query.py routing <handoff_dir> branch.parent_branch
uv run scripts/keel-query.py routing <handoff_dir> branch.parent_sha
```

- **both null** (bottom-of-stack, branched from trunk) → **skip** the preflight;
- **exactly one null** → HALT (P7): corrupt routing — reconcile before resuming;
- **both present**: the recorded `parent_sha` must equal the live parent tip
  (`git rev-parse <parent_branch>`), **or** the parent is merged to trunk (the
  pipeline's own restack-on-merge handles that case). On parent-*move* drift
  (recorded `parent_sha` ≠ live tip **and** parent not merged) → HALT (P7):
  *"WI##'s recorded base no longer matches `<parent_branch>`'s tip — re-run the
  parent or rebase before resuming."* The driver never builds a WI on a stale
  base; auto-restack-on-move is a deferred enhancement.

**Stack-parent bones.** Bones — a signature, schema, module boundary,
transaction edge, or auth guard other code depends on (see `KARTA-LANE.md`
§"Bones-clean admissibility"). This run inherits the stack-parent bones check —
`karta-pipeline` §"The halt set" item 5: if a stack parent carries a
`KARTA-DEFER` / `KARTA-GUARD` on **bones** the child builds on, that pipeline
run HALTs (harden the parent through `/keel-refine` → `/keel-pipeline` first).
The driver surfaces that nested halt fail-fast (step 7); it adds nothing.

### 6c. Worktrees (each not-DONE WI builds in its own)

Each not-DONE WI builds in its own git worktree at
`.keel/worktrees/WI##-<slug>/` — KEEL's host-neutral runtime namespace;
in-repo worktrees are mainstream (Crystal, SwarmGit). Everything below is plain `git` /
`git -C` — **no harness tool is required**; the substrate stays
markdown-portable.

- **gitignore preflight (P7).** Before creating any worktree, assert
  `.keel/worktrees/` is ignored: `git check-ignore -q .keel/worktrees/`. If
  it is **not** ignored (an install predating the `_ensure_worktree_ignored`
  helper) → HALT (P7) with the one-line fix: *"`.keel/worktrees/` is not
  gitignored — an un-ignored worktree stages as a bogus gitlink under the main
  checkout's `git add -A`. Add `.keel/worktrees/` to `.gitignore` (or re-run
  the KEEL installer) and resume."*
- **Create.** Unconditional `git worktree prune` first (idempotent ghost
  cleanup). Then
  `git worktree add --detach .keel/worktrees/WI##-<slug> <parent-tip|trunk>`,
  where `<parent-tip|trunk>` is the resolved stack parent's branch tip (when the
  WI stacks) or the local trunk ref (bottom-of-stack). On the
  registered-but-missing case, retry once with the same command plus `-f`:
  `git worktree add -f --detach .keel/worktrees/WI##-<slug> <parent-tip|trunk>`
  (the `--detach` flag and the path/ref operands are required — a bare
  `git worktree add -f` would create an unwanted branch from the path basename
  instead of a detached worktree). HALT on a
  non-zero result — **never swallow** the error. The pipeline remains the **sole
  brancher**: it creates `keel/WI##-<slug>` inside the worktree exactly as it
  does in-place; the driver only provisions the detached worktree.
- **Env init (optional).** If the project's project guide §"Pipeline Preferences"
  sets a `Worktree init:` key (e.g. `uv sync`, `npm ci`), run that command
  **once per worktree** before any gate runs; absent ⇒ skipped. No env sharing
  across worktrees; no submodule handling. KEEL's own PEP 723 scripts need
  nothing — uv's machine-wide cache is worktree-independent.
- **Dispatch contract (wrong-tree guard, P7).** The driver derives the repo root
  at runtime (`git rev-parse --show-toplevel`) and **injects the absolute
  worktree path into each ephemeral dispatch prompt** — never stored in tracked
  markdown (P4). Each dispatched `karta-pipeline` run's first action **asserts**
  `git -C <path> rev-parse --show-toplevel` equals its assigned path, and HALTs
  if it resolves to the main checkout. `git -C` is preferred over `cd` **for
  the assert** so a bad path fails the git op rather than acting on the wrong
  tree. Once the assert passes, the dispatched run **anchors its working
  directory inside the worktree for everything else** — the per-hop
  protocol's relative paths (`docs/exec-plans/…`, `<dir>/…`) and the PEP 723
  script invocations (`uv run scripts/…`) are cwd-relative; a script that
  takes a repo root (e.g. `keel-work-item-resolve.py --repo`) may be passed
  the worktree root instead. `git -C` covers only git ops — it does not
  relocate script cwd.
- **Cleanup — remove on done, keep on halt** (knobless; policy follows from repo
  state). A **done** WI lives entirely on its branch, so its worktree is
  disposable scaffolding → `git worktree remove .keel/worktrees/WI##-<slug>`
  then `git worktree prune`. A **halted** WI's uncommitted `active/` handoff
  exists *only* in its worktree → **leave it** for resume, and name it in the
  halt CTA (step 7). A later re-run's prune-first + DONE derivation treats any
  surviving worktree as disposable scaffolding — cursorless resume is preserved,
  worktrees are never read as state.

### 7. Loop (sequential, fail-fast)

For each WI in `order` that is **not DONE** (step 5) and passes the preflight
(step 6), provision its worktree (step 6c), then dispatch:

```
/karta-pipeline WI## <binder> --stack
```

as **its own subagent invocation** — a fresh, isolated context returning a
single structured result — the same subagent dispatch the orchestrator already
uses per hop, with the **absolute worktree path injected** into the dispatch
prompt (step 6c) so the pipeline asserts-then-operates on the right tree.
`karta-pipeline` resolves its own stack parent from the unmerged intra-Binder
Needs (it inherits keel's §"Stack target resolution"); the driver passes only
the WI, the Binder, `--stack`, and the worktree path.

**Fail-fast.** Any non-success return — a nested P7 HALT or a RED green gate —
is **terminal**: stop the loop immediately. Do not advance to the next WI. On
the halted WI, **keep its worktree** (its uncommitted `active/` handoff lives
only there — step 6c). Surface the nested halt **verbatim**, then emit the
driver's own P7 CTA naming (a) the failed WI **and its surviving worktree path**,
(b) the failing gate, **read from evidence, never assumed** — the nested
halt's own wording plus the deepest gate artifact actually present in the
WI's `active/` handoff (a refusal can fire at the implementer's
admissibility floor before `safety-auditor` ever runs; naming the wrong gate
misdirects the repair — when the evidence is ambiguous, quote the nested
halt verbatim without labeling a gate), (c) the still-un-run WIs, (d) the
**exact resume command** — the *same* `/karta-drive` invocation, which
re-derives the frontier and continues at the first not-DONE WI (step 5 is
cursorless; surviving worktrees are disposable scaffolding the next run's
prune-first + DONE derivation reconciles — there is no stored position to
clear), and (e) when the repair edits the WI's spec, the **lineage rule**
below.

**Spec repairs must reach the lineage.** Each WI reads the Binder and
backlog from its **own checkout** (worktree/branch), never from trunk — a
repair committed only on trunk leaves the halted WI re-resolving the same
refused slice on resume. Two sanctioned repairs, named in the CTA:
(a) **in-worktree** — make the binder/backlog repair inside the kept
worktree; re-dispatch re-resolves the changed slice and restarts the WI
cleanly; or (b) **on trunk** — commit the repair on trunk, rebase the
affected stack onto the repaired trunk bottom-up (`git rebase --onto
<trunk> <old-base> keel/WI##-…` per level; DONE WIs stay DONE — the
predicate reads archive + tick, not binder bytes), **delete the halted WI's
stale branch and worktree** (they carry no committed signals), then re-run —
the rebuild branches from the repaired lineage.

### 8. Output

**Never merge, never push.** Print a **live-derived status table** each run —
one row per WI in `order`, state ∈ {done, next}, computed from git + archive +
backlog (steps 5–6), e.g.:

```
WI   | state | note
WI09 | done  | merged-to-trunk
WI10 | next  | branch keel/WI10-… on keel/WI09-…
WI11 | next  | needs WI10
```

The table carries only `{done, next}` — under fail-fast, everything after the
first `next` is trivially waiting, so a third derived state would only imply
structure the run does not act on. The table is a **view**, not stored state
(P3 — re-derived every run; P4 — nothing cached), built from the **anchored**
reads of steps 5–6 — so it is correct from any checkout: trunk, a stack tip, or
a detached state.

When the set completes, emit the terminal CTA verbatim:

> *Binder complete — every selected WI is built and archived on its stacked
> branch. Integrate however your workflow lands code — locally:
> `git checkout <trunk> && git merge keel/<top-of-stack WI##-slug>` lands the
> whole chain in one move (every WI's commits, archived handoff, and backlog
> tick ride the lineage); on a forge: `/keel-submit <binder>` pushes the
> stack and opens PRs.*

**Store nothing** — no wave, no cursor, no run-branch.

## What this driver deliberately does NOT do

Per the design's §"Deliberately NOT built" — do not add any of these (YAGNI;
each fails a principle):

- **No stored `wave`/order** — re-derived each run (P4).
- **No resume cursor** — repo state *is* the cursor (P3/P5).
- **No stored worktree paths** — runtime-derived (`git rev-parse
  --show-toplevel`) and injected per-dispatch (P4).
- **No env sharing across worktrees** — each worktree pays its own
  `Worktree init:`; **no submodule handling** (out of scope).
- **No `EnterWorktree` / harness-tool dependency** — plain `git`/`git -C`
  suffices (probe-verified), so the substrate stays markdown-portable.
- **No push / no PR open** — that is `/keel-submit`'s job; done is repo-local.
- **No intra-layer parallelism** — sequential only; KEEL has no planner
  guaranteeing disjoint file sets, so parallel siblings risk file/branch races.
- **No auto-merge** — the human merges (P6).
- **No run-branch umbrella** — per-WI stacked branches already express the chain
  (P3/P4).

## Halt summary (all P7)

The driver HALTs — naming cause + concrete next step — only on: `Lanes:
keel-only` (step 1); non-JSON / missing Binder (step 2); an invalid Binder, a
cycle, a missing WI, or a narrowed set omitting an unbuilt in-binder predecessor
(step 4, the closure-computing CTA); a DONE contradiction (step 5); a
not-ignored `.keel/worktrees/` or a non-zero `git worktree add` (step 6c);
corrupt routing or parent-move drift (step 6); and any per-WI pipeline failure
(step 7, surfaced verbatim, naming the surviving worktree). Resume by re-running
the same `/karta-drive` invocation — it re-derives the remaining set and frontier
and continues at the first not-DONE WI.
