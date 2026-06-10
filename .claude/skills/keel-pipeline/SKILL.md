---
name: keel-pipeline
description: "Orchestrate the KEEL pipeline for a feature. Cross-cutting spine (the stages every variant runs): pre-check → test-writer → implementer → parallel review gates (code-reviewer, spec-reviewer, safety-auditor?, arch-advisor-verify?) → landing-verifier. Backend/frontend variants insert conditional research / arch-advisor-consult / designer stages before test-writer — see the per-variant diagrams below."
---

# KEEL Pipeline

KEEL — Knowledge-Encoded Engineering Lifecycle.

Orchestrate the full agent pipeline for a feature. You are the **orchestrator** — you dispatch agents, own the per-feature handoff directory's routing state, and enforce the pipeline order from the project guide.

## Framework principles

Every halt in this pipeline uses P7 (call-to-action) wording. See
[`docs/process/KEEL-PRINCIPLES.md`](../../../docs/process/KEEL-PRINCIPLES.md).
Conflict resolution follows P6 (authority hierarchy): code > spec > backlog > Binder (a bounded body of related work that decomposes into Work Items).

## Handoff substrate

A feature's handoff is a **per-feature directory**, not a single file.
See [`docs/process/HANDOFF-CONTRACT.md`](../../../docs/process/HANDOFF-CONTRACT.md)
for the canonical envelope schema, agent obligations, and orchestrator
obligations. This skill assumes that contract; read it once before
operating the pipeline. Summary:

- Per-feature **directory** at `docs/exec-plans/active/handoffs/WI##-<slug>/`.
- `routing.json` — orchestrator-owned pipeline state. Mutated **only**
  via `scripts/keel-routing.py` (never edit by hand). Run
  `uv run scripts/keel-routing.py --help` for the full subcommand set.
- `resolved-work-item.json` — written **once** at Step 0 from the resolver;
  immutable thereafter (bootstrap features omit it — no Binder to resolve).
- One `<agent>.md` per agent that contributes work product. **The agent
  writes its own file** with the `Write` tool; the orchestrator never
  transcribes agent output.
- One `<touchpoint>-review/attempt-NN.md` per review-panel attempt
  (`precheck-review/`, `design-review/`, `landing-review/`), guarded by a
  `.attempt-hashes.json` sidecar.

Every agent dispatch passes the feature **directory** path; agents
`Read` the JSON and sibling `.md` files directly — no shell exec, no
`jq`, no JSON pasted into prompts. The orchestrator alone runs shell
(its Bash tool) and mutates `routing.json` through `keel-routing.py`.

Throughout this skill, `<dir>` is shorthand for
`docs/exec-plans/active/handoffs/WI##-<slug>/`.

## Arguments

The user provides a feature ID and Binder path:
```
/keel-pipeline WI04 docs/exec-plans/binders/my-feature.json
```

The Binder path MUST be a structured JSON Binder. If the path ends in `.md`
or any non-JSON extension, HALT with:
> *"Binder path must be a structured JSON file at `docs/exec-plans/binders/<slug>.json`. If you have a markdown spec or prose input, run `/keel-refine` first — it converts non-JSON inputs into structured JSON Binders. See `docs/process/PIPELINE-DOCTRINE.md` §'Feature input canon — single path, JSON Binders only'."*

If no Binder exists yet, tell the user to run `/keel-refine` first — it
is the conversion hub that produces the structured JSON Binder this
pipeline expects.

**Optional `--stack` directive.** `/keel-pipeline WI## <binder> --stack` forces `Branching policy: stack` for **this invocation only**, overriding the project-guide default. It is a transient run intent — never written to the repo. Used by `/karta-drive` to drive a stacked chain without mutating the persistent knob; a bare invocation continues to read `Branching policy:` from the project guide.

**Bootstrap features take no Binder.** A feature whose backlog entry carries
`Binder-exempt: bootstrap` (scaffold / test-infra, run during greenfield
setup) is invoked as `/keel-pipeline WI##` with **no** Binder path. The
Binder-required halt and the "run `/keel-refine` first" message above apply only
to product features. Bootstrap features run orchestrator-direct (Step 0):
skip the Binder-path requirement, skip the JSON Binder read in "Before Starting",
and leave `binder_ref` unset (the handoff validator exempts bootstrap from
routing/`binder_ref`).

**Maintenance changes take no Binder either.** A feature whose backlog entry
carries `Binder-exempt: infra` or `Binder-exempt: trivial` is invoked as
`/keel-pipeline WI##` with **no** Binder path and runs the **maintenance lane**
(Step 0, Maintenance) — a reduced flow defined in
`docs/process/PIPELINE-DOCTRINE.md` §"The maintenance lane". It produces no
`resolved-work-item.json` and no `routing.json`; its record is the typed commit.
Incidental tooling churn with no card (e.g. a CLI that rewrote a tracked
config) lands through the same lane by following the contract's procedure
directly — no WI## is required. The maintenance lane is a sibling to the four
pipeline variants, **not a fifth variant**; it qualifies a change only against
the admissibility boundary in that doctrine section, and routes anything that
adds product behavior to `/keel-refine`.

## Before Starting

1. Read the project guide to determine the correct pipeline variant
2. Read the target feature's **title only** from the structured JSON Binder via `jq` (`jq '.work_items[] | select(.id=="WI##") | .title' <binder-path>`) — that is all the orchestrator needs at this step (the commit subject); pre-check `Read`s the full slice itself and no longer pastes the JSON block. **Skip for bootstrap features** (`Binder-exempt: bootstrap`) and **maintenance features** (`Binder-exempt: infra`/`trivial`) — they have no Binder; take the title (and, for bootstrap, the agent) from the backlog entry.
3. **Create the handoff directory** at
   `docs/exec-plans/active/handoffs/WI{id}-{slug}/` (`<dir>`). Do NOT copy
   from a template file — the pipeline scaffolds the directory
   programmatically through the two sub-steps below. (Branch and base
   resolution happen in items 5–12; the directory and its files are
   created at item 11, after the dependency classification halts have
   passed. This item defines *what* to create; item 11 is *when*.)

   Sub-step 3.a — **Resolve the feature** (skip for bootstrap):
   ```
   uv run scripts/keel-work-item-resolve.py \
     --backlog docs/exec-plans/active/backlog.md \
     --binder <binder_ref_path> \
     --feature WI{id} \
     --v2-schema \
     --output <dir>/resolved-work-item.json
   ```
   `--v2-schema` requires `--output`; the script writes the file
   atomically (tmp + rename) and validates it against
   `schemas/resolved-work-item.schema.json` before exiting. Both flags are
   mandatory here: the resolver's default (no `--v2-schema`) prints
   **legacy stdout JSON**, which is **not** the v2 file that `init`'s
   `--pretriage-from` (sub-step 3.b) consumes — omit them and you write the
   wrong shape. On non-zero exit → HALT (P7) with the resolver's stderr and
   the exact path that failed to validate.

   **Worktree runs:** when this invocation was dispatched with an assigned
   worktree path (`/karta-drive` step 6c), every relative path above
   resolves against **that worktree** — run the command with its working
   directory inside the assigned worktree, or pass `--repo
   <worktree-root>`. The resolver anchors `--backlog`/`--binder`/`schemas/`
   to the repo root it resolves (default: the cwd's); a main-checkout cwd
   resolves the **wrong root** — stale binder bytes at best, the resolver's
   invocation halt at worst.

   This file is **immutable** for the run (see
   `docs/process/HANDOFF-CONTRACT.md`); if a re-run finds the Binder newer
   than it (`mtime(Binder) > mtime(resolved-work-item.json)`), regenerate it
   by re-running this sub-step — never patch it.

   Sub-step 3.b — **Initialize routing.json**:
   ```
   uv run scripts/keel-routing.py init <dir> \
     --feature WI{id} \
     --slug <slug> \
     --pipeline <variant> \
     --binder <binder_ref> \
     --review-panel <personas|roundtable> \
     --pretriage-from <dir>/resolved-work-item.json
   ```
   `init` applies the **safe-merge boundary** (see
   `docs/process/HANDOFF-CONTRACT.md` §"Init: routing.json safe-merge
   boundary"): if `routing.json` is absent it creates fresh; if it exists and
   the resolver `source_hash` is unchanged it preserves derived state
   (gates, review, escalation count, status) and refreshes identity +
   pretriage; if `source_hash` changed it invalidates derived state and
   restarts the run at Step 1. `--binder` is **required** for non-bootstrap
   features (the init command rejects a missing `--binder` for a non-bootstrap
   pipeline). `--review-panel` carries the value resolved in Step 0.5.

   **Bootstrap features** (`Binder-exempt: bootstrap`): **skip sub-step 3.a
   entirely** (no Binder to resolve). Invoke `init` with
   `--pipeline bootstrap`, `--review-panel none`, the
   `--bootstrap-agent <scaffolder|config-writer>` from the
   entry's `Agent:` field, and **no** `--binder` and **no** `--pretriage-from`.
   The validator exempts `pipeline: bootstrap` from `binder_ref`,
   `resolved-work-item.json`, and routing flags.

   **Maintenance features** (`Binder-exempt: infra`/`trivial`): **skip the entire
   handoff scaffold** — both sub-step 3.a (no Binder to resolve) and sub-step 3.b
   (no `routing.json`). The maintenance lane runs no agent handoff, so it
   creates no handoff directory and records nothing in `routing.json`; its
   record is the git commit. Go to Step 0, Maintenance.

4. **Clean-tree check.**
   Run `git status --porcelain`. The handoff directory is not created
   until item 11, so at this point the tree should be clean of any KEEL
   artifact. If the output is non-empty, STOP. Print:

     Pipeline requires a clean working tree. These changes are uncommitted:
     <paste the porcelain output>
     Pick the path that fits:
     - It is output from /keel-setup or /keel-adopt (the project guide, NORTH-STAR.md,
       ARCHITECTURE.md, core-beliefs.md, agent configs, backlog.md) → those
       skills own their configuration commit. If you just ran setup/adopt,
       finish its Phase 7 and bless the commit, or commit those files
       manually. Do NOT route initial configuration through the maintenance
       lane. Then re-run.
     - A tool rewrote a tracked file you want to keep — a dependency/lockfile
       bump, a formatter run, a CLI config rewrite (NOT setup output) → land
       it through the maintenance lane
       (docs/process/PIPELINE-DOCTRINE.md §"The maintenance lane"), then
       re-run this pipeline.
     - Tooling keeps rewriting it and you do not want it tracked → add it to
       .gitignore or local config, then re-run.
     - It is your in-progress feature work → stash it or move it to its own
       branch, then re-run.

   Do not proceed. Rationale: Step 9 uses `git add -A` to stage the feature,
   so any unrelated changes in the tree at pipeline start would be silently
   swept into the feature's commit. Phase 1 refuses that ambiguity.

   **Exempt for maintenance features** (`Binder-exempt: infra`/`trivial`): the
   working-tree delta is the lane's input, not contamination. Skip this check;
   Step 0, Maintenance confirms the delta is solely the maintenance change.

5. **Resolve base-branch (local trunk).**
   Resolve the local trunk branch name `<base-branch>` once; throughout this
   skill `<base>` is shorthand for the **local** ref `<base-branch>` (no
   remote-tracking prefix — completion is repo-local). Every base reference
   below (the `git ls-tree`, `git merge-base --is-ancestor`, the feature
   branch's source, `git rebase --onto`) uses it, and it is not hardcoded to
   `main`/`master`. Resolve in order, first hit wins:

   - **(a)** A `Base branch:` key under the project guide's Pipeline Preferences, if
     present → use its value verbatim.
   - **(b)** Else, **when a remote exists**, its recorded HEAD:
     `git symbolic-ref --short refs/remotes/<remote>/HEAD` (pick the sole
     remote, or the current branch's upstream remote on multi-remote repos)
     and strip the `<remote>/` prefix — the remote's default branch names the
     trunk even though landing never touches the remote.
   - **(c)** Else the local trunk by ref existence: `git rev-parse --verify
     --quiet refs/heads/main` → `main`; else `refs/heads/master` → `master`.
   - **(d)** None of the above resolves a name → HALT (P7): "Cannot resolve
     the trunk branch: no `Base branch:` key in the project guide, no remote-recorded
     HEAD, and neither `main` nor `master` exists locally. Add a
     `Base branch: <name>` line under Pipeline Preferences in the project guide (or
     create the trunk branch), then re-run."

   Hold the resolved `<base-branch>` for the remaining Step 0 items.

6. **Read WI##'s Needs from backlog.md.**
   Locate the WI## entry, read its `Needs:` line. Split into intra-Binder and
   cross-Binder per the existing backlog format (`Needs (intra-Binder): ...`
   and `Needs (cross-Binder): ...`). If the entry uses the legacy single
   `Needs: WI02, WI03` format, treat all as intra-Binder.

7. **Classify each Need (priority order — first match wins):**

   1. **Legacy cutoff.** Need's WI## id is ≤ `KEEL-INVARIANT-7:
      legacy-through=WI##` declared at the top of backlog.md →
      treat as `done`.
   2. **Archived handoff on trunk.** Run
      `git ls-tree -r --name-only <base-branch> -- docs/exec-plans/completed/handoffs/`
      and look for a `WI##-*/` directory entry (e.g. its `routing.json` at
      `completed/handoffs/WI##-<slug>/routing.json`). Found → `done`.
      Step 9's archive sub-step moves the handoff directory into
      `completed/`, so its presence on the local trunk is a strong built
      signal.
   3. **SHA ancestry.** Search any prior handoff's `routing.json` (active or
      archived) for `branch.parent_sha` recorded for this Need's WI## (read
      it with `keel-query.py routing <that-dir> branch.parent_sha`). If
      found and `git merge-base --is-ancestor <parent_sha> <base-branch>`
      returns 0 → `done`.
   4. **Branch existence.** Run
      `git for-each-ref --format='%(refname)' 'refs/heads/keel/WI##-*'`
      (match by WI## prefix only — slug churn is tolerated; quote the
      pattern — zsh aborts on an unmatched bare glob). Any match
      → `branch-exists-unmerged`.
   5. **Unknown.** None of the above → HALT with the brownfield-
      adoption CTA from §"Halt CTA wording" below.

   The classification computed HERE is authoritative. The resolver's
   `dependencies[].status` in `resolved-work-item.json` is base-resolved
   and may read `unknown` for a `branch-exists-unmerged` Need (the
   resolver resolves against base, not against unmerged sibling
   branches); downstream consumers treat that field as advisory.

8. **Cross-Binder halt.**
   If any cross-Binder Need is not `done` → HALT with the
   cross-Binder CTA below. Cross-Binder always halts regardless of policy.

9. **Intra-Binder policy decision.**
    If the invocation passed `--stack`, use `stack` for this run; else read `Branching policy:` from the project guide (default `halt` if absent).
    Among the WI##'s direct intra-Binder Needs, take the unmerged subset `U`:
    - `U` empty → branch from `<base>`; skip to item 11.
    - `U` non-empty + policy=`halt` → HALT with the intra-Binder CTA below.
    - `U` non-empty + policy=`stack` → resolve stack target per
      §"Stack target resolution" below; record `parent_branch` and
      `parent_sha` in `routing.json` via `keel-routing.py set-branch`
      (item 11 performs the write, after the directory exists).

10. **Branch-collision check.**
    `git for-each-ref 'refs/heads/keel/WI{id}-*'` — match the WI## prefix
    only (pattern quoted — zsh aborts on an unmatched bare glob). If a
    matching branch exists, see §"Re-run handling" below
    (handoff directory in `active/` → resume; no directory → halt with
    orphan-branch CTA).

11. **Create the handoff directory.**
    Now run sub-steps 3.a (resolver) and 3.b (`init`) defined in item 3 —
    the dependency-classification halts (items 7–10) have all passed, so
    the directory is safe to scaffold. `init` seeds `routing.json` with
    `status: IN-PROGRESS`, `pipeline: <variant>`, and `binder_ref` (omitted
    for bootstrap). If stacking happened (item 9), also record the parent
    fields:
    ```
    uv run scripts/keel-routing.py set-branch <dir> \
      --parent-branch <parent_branch> --parent-sha <parent_sha>
    ```
    No frontmatter, no `_TEMPLATE.md` copy — all routing state lives in
    `routing.json`.

12. **Create the feature branch.**
    `git checkout -b keel/WI{id}-{slug} <parent_branch_or_base>` where
    `<parent_branch_or_base>` is the stack target's branch when stacking,
    or the local `<base-branch>` otherwise. The pipeline never commits
    to base.

    The `keel/WI##-<slug>` branch prefix is load-bearing for re-run /
    restack / collision detection — every `refs/heads/keel/` matcher in
    Step 0 (branch-existence at item 7, collision at item 10, restack on
    re-invocation) depends on it, so changing it means editing every such
    matcher; it is intentionally not a per-project knob.

### Re-run handling

When `/keel-pipeline WI##` is re-invoked and the handoff **directory**
already exists at `<dir>` (`docs/exec-plans/active/handoffs/WI{id}-{slug}/`):

- Treat the existing directory as authoritative — do not re-create it.
  Re-running `init` is safe: it applies the safe-merge boundary (see
  item 3.b). If the resolver `source_hash` is unchanged, derived state
  (gates, review, escalation count, status) is preserved; if it changed,
  derived state is invalidated and the run restarts at Step 1.
- If `resolved-work-item.json` is missing (orphaned) or older than the Binder
  (`mtime(Binder) > mtime(resolved-work-item.json)`), re-run sub-step 3.a to
  regenerate it before resuming.
- Skip the dependency classification and policy decision steps (their
  results are already recorded in `routing.json` `branch.parent_branch` /
  `branch.parent_sha` if stacking happened — read them with
  `uv run scripts/keel-query.py routing <dir> branch`).
- If `branch.parent_sha` is recorded and now `git merge-base --is-ancestor
  <parent_sha> <base-branch>` returns 0 (parent merged into the local trunk
  since first run): run §"Restack on re-invocation" below. Otherwise
  resume from the halt point as today's pipeline does.
- If the directory exists in `active/` but no matching branch exists,
  HALT with the handoff-without-branch CTA below.
- If a branch matching `keel/WI{id}-*` exists locally but no handoff
  directory exists in `active/`, HALT with the branch-without-handoff CTA
  below.

### Stack target resolution

In `stack` mode, after classifying Needs, resolve which branch WI## stacks on:

1. Restrict to **direct, intra-Binder, unmerged** Needs (set `U`). Cross-Binder
   Needs are excluded — Step 9 above already halted if any was unmerged.
2. **|U| = 0:** branch from `<base>` (no stacking needed).
3. **|U| = 1:** stack on that Need's branch tip. Record in `routing.json`
   `branch` (written at item 11 via `keel-routing.py set-branch`):
   - `parent_branch` — the branch ref (e.g., `keel/WI01-oauth-pkce-flow`)
   - `parent_sha` — `git rev-parse <parent_branch>` at branch-creation time
4. **|U| > 1:** examine the dep graph among `U` (consult their `Needs:`
   lines in backlog.md). If exactly one element of `U` has every
   other element as an ancestor (the **chain case** — e.g., WI02 needs
   WI01, WI00; WI01 needs WI00; WI01 is the topmost unmerged Need), stack on
   it. Otherwise (the **fan-out case** — WI02 needs WI01 and WI00 where
   neither depends on the other), HALT with the sibling-fan-out CTA below.

### Restack on re-invocation

When the handoff records `parent_sha` and a re-run detects it as ancestor
of the local `<base>` (parent merged into the trunk since first run):

```
git checkout keel/WI{id}-{slug}

# Refuse if WI##'s history contains merge commits from the old parent
# branch — `git rebase --update-refs` would replay the merge and produce
# duplicate hunks. HALT with the restack-merge-history CTA below.
# Capture both git log errors and merge-commit presence in two separate steps
# so a `git log` failure (bad ref, missing object) HALTs rather than silently
# proceeding past the guard.
merges=$(git log --merges --format=%H <parent_sha>..HEAD) || HALT \
    "git log failed reading <parent_sha>..HEAD — bad ref or missing object."
if [ -n "$merges" ]; then
    HALT  # restack-merge-history CTA — see Halt CTA wording below
fi

git rebase --update-refs --onto <base-branch> <parent_sha>
# On non-zero exit (conflicts), HALT with the restack-conflict CTA below.
```

The restack is **local-only** — no fetch, no push, no PR retarget. A
merged parent is detected against the local trunk; the rebase rewrites the
feature branch in place. Integration (push/PR) is the human's separate
`/keel-submit` step.

`git rebase --update-refs` is universal across squash/merge/rebase merge
strategies; it requires Git ≥ 2.38, which `install.py` enforces as the
floor. Multi-level cascade is **per-level** — each WI##'s restack only
happens when its own pipeline runs. Out-of-order re-runs leave stale
stacks until each level's pipeline fires; this is documented behavior,
not a bug, and aligns with KEEL's no-daemon model.

### Step 0.5: Review panel selection

After the clean-tree and base-branch checks, before any agent dispatch,
resolve which review panel serves this feature's three checkpoints. See
`docs/process/REVIEW-PANEL.md` for the panels and this rule.

1. **Per-feature override wins.** If the backlog entry set a `Review:`
   field (`personas` | `roundtable`, surfaced by keel-work-item-resolve.py
   as the resolved feature's `review_panel`), use it.
2. **Else the project default.** Read `Review panel` from the project guide
   (`personas` | `roundtable`). Absent ⇒ `personas`.
3. The resolved value is passed to `init` (item 11) as
   `--review-panel <value>`, which writes it to `routing.json`
   `review_panel`. (Bootstrap features pass `--review-panel none`.)
   Resolve it here so it is in hand when item 11 runs.
4. If `review_panel: roundtable`, probe the roundtable MCP server now.
   If it is unavailable, fall back: set `review_panel: personas` and
   print a visible note to stderr —

     !! Roundtable MCP unavailable ({reason}) — using the persona panel.
     !! (roundtable was requested via the project guide / backlog marker.)

   The persona panel needs only your agent host's subagent dispatch, so it is
   always available — no probe, no skip. Review always happens (P7: never
   silently skipped).

## Pipeline Variants

Determine the variant based on what the feature touches:

**Bootstrap** — scaffolding, config. A feature is bootstrap iff its
backlog entry carries `Binder-exempt: bootstrap`, or (legacy untagged backlogs)
its `Agent:` field names a bootstrap agent (scaffolder /
config-writer) — **not** by Work Item-number. The set
is variable and its order differs by stack (e.g. a full-stack backlog runs one
scaffold per package then test-infra; a single-package backlog runs one scaffold
then test-infra):
```
scaffolder → landing-verifier              (app skeleton; one per package)
config-writer → landing-verifier           (test infrastructure)
```
Bootstrap features are orchestrator-direct: dispatch the agent named in the entry's `Agent:` field, then landing-verifier. No pre-check, no test-writer, no implementer. The bootstrap agent's report serves as the handoff context.

**Backend** — changes to core business logic, services, data layer:
```
pre-check → review-precheck? → researcher? → arch-advisor-consult? → backend-designer? → review? → test-writer → implementer → [code-reviewer ∥ spec-reviewer ∥ safety-auditor? ∥ arch-advisor-verify?] → landing-verifier → review? → complete
```

**Frontend** — changes to UI components, templates, styles, client-side logic:
```
pre-check → review-precheck? → researcher? → arch-advisor-consult? → frontend-designer → review? → test-writer → implementer → [code-reviewer ∥ spec-reviewer ∥ arch-advisor-verify?] → landing-verifier → review? → complete
```
A `ui`-layer feature's oracle carries the fidelity checklist (rendered / identity / wiring / Layout-bound, as applicable) and its tests render the composed component (test-writer Layer 4a/4b); `spec-reviewer` enforces both completeness and coverage, and `landing-verifier` reports a qualified verdict. See `docs/process/PIPELINE-DOCTRINE.md` §"Frontend acceptance". Viewport/layout/console verification via a served bundle runs when the feature's `oracle.type` is `e2e`/`smoke` and a served harness is configured (Stage-4, derived from the harness — not a knob); otherwise the rendered floor stands and `landing-verifier` reports the viewport surface as not verified.

**Cross-cutting** — test infrastructure, config, docs:
```
pre-check → review-precheck? → test-writer → implementer → code-reviewer → landing-verifier → review? → complete
```

**Full-stack** work (touching both backend and frontend) is **not a separate variant**: KEEL runs one pipeline per feature, and each feature has one layer. Decompose it into a backend feature and a frontend feature that declares `Needs:` the backend — each runs its own pipeline and its own handoff, and the frontend stacks on the backend's branch via §"Stack target resolution". A change too small to be worth splitting is just one feature in its dominant variant.

**Maintenance lane** — *not a variant.* Repo work that is not a feature
(`Binder-exempt: infra`/`trivial`, or incidental tooling churn): dependency/lockfile
bumps, tooling-generated config, formatter runs, ignore/editor-config edits,
license headers, typo sweeps. It runs a reduced flow, recorded in the commit
rather than in `routing.json`:
```
(adopt-or-make change) → green gate (tests + lint) → doc-gardener ad-hoc → commit (chore:/infra:)
```
No pre-check, designer, test-writer, implementer, Binder, resolved-work-item, or
handoff directory. The four variants above are the feature-execution paths; the
maintenance lane is their sibling. Qualification, procedure, and the review
knob are defined in `docs/process/PIPELINE-DOCTRINE.md` §"The maintenance lane"
and run via Step 0, Maintenance. If the change adds product behavior, HALT and
route to `/keel-refine`.

## Execution Steps

### Step 0: Bootstrap (`Binder-exempt: bootstrap` entries)
If the feature is a bootstrap feature per the variant rule above (its entry carries `Binder-exempt: bootstrap`, or — legacy untagged backlogs — its `Agent:` names a bootstrap agent), it is bootstrap regardless of its Work Item-number. Dispatch the agent named in its `Agent:` field (scaffolder or config-writer) and read no Binder. Its spawn message opens with the Spawn-message preamble defined under "The per-hop protocol" below (the `[KEEL-ROLE <agent>]` preamble, substituting the bootstrap agent's name). Pass it the feature directory `<dir>` and target filename `<agent>.md`; it self-writes its report to `<dir>/<agent>.md` per `docs/process/HANDOFF-CONTRACT.md`. Verify the file per the per-hop rule (exists, non-empty, mtime advanced), then skip directly to Step 8 (landing-verifier). Bootstrap features do not use pre-check, designers, test-writer, or implementer, and have no `resolved-work-item.json`.

### Step 0, Maintenance (`Binder-exempt: infra`/`trivial` entries, or incidental tooling churn)
The maintenance lane — defined canonically in
`docs/process/PIPELINE-DOCTRINE.md` §"The maintenance lane". Runs no agent
handoff, creates no handoff directory, and writes nothing to `routing.json`;
the typed commit is the record. Procedure:

1. **Qualify.** Confirm the change meets **every** clause of the admissibility
   boundary in that doctrine section (no new product behavior; mechanical and
   behavior-preserving; one of the allowed diff classes; not an
   intent-dependent bug fix). If you cannot explain why every changed hunk is
   maintenance, HALT and route to `/keel-refine` — **when in doubt, it is a
   feature.**
2. **Isolate the delta.** The change is the working-tree delta (adopt) or you
   make it now. Run `git status --porcelain` / `git diff` and confirm the delta
   is **solely** the maintenance change. If unrelated edits are present, HALT
   and tell the operator to separate them.
3. **Green gate.** Run the project's configured gate command (the test + lint
   commands documented in the project guide §Development). It must pass. On failure,
   HALT (P7) with the command output.
4. **Review (knob).** If the project guide sets `Maintenance review: reviewed`,
   dispatch `code-reviewer` on the diff and resolve `CONCERNS` before landing.
   The default (`gate-only`, or the key absent) skips this. The knob may only
   add review — it never lowers the green gate or the qualification boundary.
5. **Garbage-collect.** Dispatch `doc-gardener` in ad-hoc mode (repo-wide
   sweep; see Step 9 doc-gardener) and fold any drift fixes into the change.
6. **Land.** Commit with a `chore:`/`infra:` type (`chore(WI##): …` when a card
   exists, otherwise a plain `chore: …`), body noting `maintenance lane; gate:
   <command> green`. Completion is repo-local: the commit on the branch is the
   record. The pipeline does not push or open a PR — forge integration is the
   human's separate `/keel-submit` step, exactly as Step 9 now leaves it. There
   is no verdict table — no `routing.json` was written.

Maintenance features do not use pre-check, designers, test-writer, implementer,
or the review panel, and have no `resolved-work-item.json`. Done after landing —
do not continue to the feature steps below.

### The per-hop protocol (every sequential agent)

Each sequential-agent step below uses this protocol. The dispatch shape
and verification order are identical across agents — only the agent name,
target filename, and upstream-file list change.

**Spawn-message preamble (EVERY dispatch — sequential per-hop, the 4-lens
parallel review panel, and bootstrap — no exception).** Every spawn message you
construct OPENS with the KEEL-ROLE preamble (canonical text:
`docs/process/HOST-SURFACES.md` §"Subagent dispatch"), substituting `<agent>`
(the exact name of the agent being dispatched) for `<role>`:
```
[KEEL-ROLE <agent>] Operate as the `<agent>` role. Acquire your role contract by
the FIRST route that applies, then do the task below:
1. RESIDENT — your system prompt already identifies you as the `<agent>` agent
   and contains its contract (host loaded the master as your system prompt):
   proceed, do not re-read.
2. INJECTED — your context contains a line starting with `[KEEL-ROLE-INJECTED
   <agent> complete=true`: that injected text IS your complete contract — do not
   re-read.
3. POINTER — neither applies: BLOCKING READ `.keel/agents/<agent>.md` in full and
   follow it; if it cannot be read in full, STOP and report. Never improvise the role.
```
On Claude Code route 1 always applies (resident master) — the preamble is a
no-op there; it earns its keep on Codex, where it carries the role identity the
injector recovers and the read-fallback when injection is inactive. The task
context below is appended after the preamble.

**Dispatch shape.** After the preamble, every dispatch passes:
```
Dispatch <agent> with:
- Feature directory: <dir>   (docs/exec-plans/active/handoffs/WI##-<slug>/)
- Target filename:   <agent>.md  (the agent self-writes this with Write)
- Upstream files to read: [resolved-work-item.json, <upstream>.md, ...]
- Reasoning tier: the tier named by routing.pretriage.recommended_model
  (`<sonnet|opus>`), with the per-agent override table in
  docs/process/HANDOFF-CONTRACT.md §"Per-agent model selection"
  (designers/arch-advisor-consult/arch-advisor-verify/safety-auditor and
  the Architect+Adversary panel lenses are always at the high-reasoning
  tier regardless of pretriage).
```
**Record pretriage on first dispatch.** If `routing.pretriage` is absent
(first dispatch of a run — `init` never seeds it), compute the weighted
score from `resolved-work-item.json`'s `.pretriage_inputs` per the rule in
docs/process/HANDOFF-CONTRACT.md §"Per-agent model selection" (the
high-reasoning tier iff weighted score ≥ 2; weights per the pretriage rule),
and record it before reading it back:
```
uv run scripts/keel-routing.py set-pretriage <dir> <sonnet|opus> \
  --score <n> --reason "<truthy signals, or 'no signals'>"
```

Read the pretriage model first:
`uv run scripts/keel-query.py routing <dir> pretriage.recommended_model`.

Capture the pre-dispatch mtime of `<dir>/<agent>.md` (or note its
absence) so step 2 below can prove the agent wrote new content.

**After dispatch, in this order:**

1. **Escalation special-case FIRST (pre-check only).** If the envelope is
   `verdict: blocked` AND `top_blockers` contains `model-upgrade-needed`,
   handle it *before* verifying any file (a blocked early-abort return may
   have written nothing):
   - `uv run scripts/keel-routing.py incr-escalation <dir>`
   - On **exit 3** (budget exhausted): HALT (P7):
     > *"Pre-check self-escalated twice; the pretriage rule needs tuning.
     > Inspect `routing.pretriage` and the blocked envelope's summary;
     > manually adjust `routing.pretriage.recommended_model` if the issue
     > is data, or amend the pretriage scoring rule, then re-run."*
   - Delete any partial `<dir>/pre-check.md` if it exists.
   - Force the high-reasoning tier for the re-dispatch:
     ```
     uv run scripts/keel-routing.py set-pretriage <dir> opus \
       --score 0 --reason "pre-check self-escalated"
     ```
     (`set-pretriage` stores `recommended_model`, `score`, and `reason`
     verbatim — it has NO bypass logic of its own. `--score 0` is fine
     here because the `self-escalated` **substring in the reason** is the
     sentinel that `validate-handoff.py`'s pretriage-consistency check
     bypasses — without it the validator would HALT on this legitimate
     high-reasoning-tier override whose score is below the high-tier
     threshold. Keep the `self-escalated` substring in `--reason`. The tier
     override is what drives the high-reasoning-tier re-dispatch.)
   - Re-dispatch pre-check at the high-reasoning tier, then resume at step 1
     with the new envelope.
2. **Verify the file** (normal returns only): `<dir>/<agent>.md` exists,
   is non-empty, and its mtime advanced past the pre-dispatch mtime
   captured above. Any check fails → HALT (P7) naming the agent, the
   expected path, and the failed check. The envelope's `wrote:` field is
   advisory — the filesystem check is authoritative.
3. **Update routing** from the envelope via `keel-routing.py`:
   - **pre-check** → write `routing.json` `routing` block from the
     envelope's `routing_hints.metadata`. **The envelope nests the seven
     flags under `routing_hints.metadata`, but `set-routing` reads a
     FLAT top-level mapping and HALTs (exit 4) if any of the seven is
     missing** (see `docs/process/HANDOFF-CONTRACT.md` §"The envelope").
     So do NOT pass pre-check's envelope verbatim — **extract** the
     `routing_hints.metadata` sub-block into a flat top-level YAML and
     pass *that*. Concretely: take pre-check's returned envelope, lift
     `routing_hints.metadata` to the document root, and write only those
     seven keys to a temp file. For an envelope whose metadata block is
     `intent: build`, `complexity: standard`, all `*_needed` false except
     `implementer_needed: true`, the temp file you write is exactly:
     ```yaml
     intent: build
     complexity: standard
     designer_needed: false
     researcher_needed: false
     safety_auditor_needed: false
     arch_advisor_needed: false
     implementer_needed: true
     ```
     Then pass that flat file:
     ```
     uv run scripts/keel-routing.py set-routing <dir> \
       --from-envelope <flat-envelope-file>   # or '-' to read YAML from stdin
     ```
     (`set-routing` is a full-block replace, so a re-dispatched
     high-reasoning-tier pre-check cannot leave stale standard-tier flags
     behind.)
   - **gates** → `set-gate` (see Step 5).
   - **review touchpoints** → `set-review` (see Steps 1.3 / 2.5 / 8.5).
4. **Dispatch next stage** — the `routing_hints.next` agent, or the
   `kickback_to` target on concerns.

### Step 1: Pre-check (standard pipeline only)
Run the per-hop protocol above. Dispatch `pre-check` with `<dir>`, target
filename `pre-check.md`, and upstream files `[resolved-work-item.json]`
(pre-check `Read`s the structured feature data — it does not paste it into
its brief). Pre-check self-writes its execution brief to
`<dir>/pre-check.md` per the contract.

Pre-check's envelope carries a `routing_hints.metadata` block with the
routing flags. Step 3 of the per-hop protocol writes them to
`routing.json` `routing` via `set-routing --from-envelope`:
- `intent` ∈ {`refactoring`, `build`, `mid-sized`, `architecture`,
  `research`} and `complexity` ∈ {`trivial`, `standard`, `complex`,
  `architecture-tier`} — determine which optional agents run. Both are
  **schema-enforced enums** (`routing.schema.json`); there is no `feature`
  value — a scoped feature classifies as `mid-sized` (pre-check's intent
  table), and the post-write validation HALTs on any other token
- `designer_needed` — YES/NO (trivial complexity → always NO)
- `researcher_needed` — YES/NO (research intent → always YES)
- `safety_auditor_needed` — YES/NO
- `arch_advisor_needed` — YES if complexity is architecture-tier
- `implementer_needed` — YES/NO

Read routing decisions for all subsequent steps from `routing.json`
(e.g. `uv run scripts/keel-query.py routing <dir> routing.arch_advisor_needed`),
never by grepping pre-check's prose.

### Step 1.3: Review panel — pre-check review

Always runs. Stress-tests pre-check's routing classification BEFORE
downstream agents run — because the routing flags (`designer_needed`,
`researcher_needed`, `safety_auditor_needed`, `arch_advisor_needed`,
`complexity`) cascade through the whole pipeline. A misclassification
either wastes 5+ agent cycles or under-scrutinizes safety-critical
changes. One-way door.

Run the ONE panel selected in Step 0.5 (`review_panel`) — personas OR
roundtable, never both. Whichever runs follows the same synthesis →
verdict → kickback protocol in `docs/process/REVIEW-PANEL.md`; the
verdict is `APPROVED | CONCERNS`.

**Persona panel (`review_panel: personas`, the default):**
1. Dispatch FOUR `review-panelist` agents IN PARALLEL (one message,
   four tool calls), one per lens (Skeptic, Architect, Adversary,
   Pragmatist). Each panelist's spawn message opens with the Spawn-message
   preamble above (`[KEEL-ROLE review-panelist]`); the lens is task context.
   Give each its lens, touchpoint = `pre-check`, `<dir>`, and
   the files to read (`pre-check.md` + `resolved-work-item.json` for routing
   flags + the spec excerpt). Architect + Adversary run at the
   high-reasoning tier always; Skeptic + Pragmatist follow pretriage.
   Panelists write no file — they
   return their review to the orchestrator. Ask each
   to attack the classification through its lens: wrong intent, wrong
   complexity tier, missing research/safety/arch signal, designer
   flagged YES-but-no or NO-but-yes.
2. Synthesize the four returns (agreed/solo/tension, severity-ranked).

**Roundtable panel (`review_panel: roundtable`):**
1. Call `mcp__roundtable__roundtable-critique` with the brief + routing
   flags + spec excerpt — attack the classification, as above.
2. Call `mcp__roundtable__roundtable-canvass` with the critique + the
   `pre-check.md` brief to synthesize a consensus routing (keep, flip,
   or refine individual flags).

**Record, verdict, kickback (both panels):**
3. **Write the attempt file.** The orchestrator (not the panelists)
   composes the synthesis and writes it as a new standalone file
   `<dir>/precheck-review/attempt-NN.md` (zero-padded, numbered from `01`
   with no gaps; see `docs/process/HANDOFF-CONTRACT.md` §"The three
   orchestrator-owned files", item 3). The body is `# Pre-check review` then a `### Attempt N —
   <verdict>` block (personas: one line per lens + synthesized findings;
   roundtable: `#### Critique` / `#### Canvass`). Past attempt files are
   **content-immutable** — never edit them; each pass is a new file.
   **As the very next action after writing the file**, update the hash
   sidecar:
   ```
   uv run scripts/keel-routing.py record-attempt-hash <dir> precheck N
   ```
   (touchpoint arg is `precheck`; the file lives under `precheck-review/`.)
   Then record the verdict + attempt in `routing.json`:
   ```
   uv run scripts/keel-routing.py set-review <dir> precheck <verdict> N
   ```
4. If the result disagrees with pre-check's flags: send the findings to
   `pre-check`. It self-writes the revised brief to `<dir>/pre-check.md`
   (full-file overwrite, no "(revised, attempt N)" framing — rationale
   lives in the deliberation file). Re-run step 3 of the per-hop protocol
   to rewrite `routing.json` `routing` from the new envelope. Then **apply
   route-reset if any flag flipped** (see below), bump the attempt to 2,
   re-run the panel, and write `attempt-02.md` + its sidecar hash.
5. If still divergent after attempt 2: proceed with pre-check's latest
   classification (advisory, not blocking). `set-review <dir> precheck
   CONCERNS 2`, logging the override reason in the attempt file (P7 — not
   a silent skip). Roundtable panel only: the orchestrator MAY first
   invoke `mcp__roundtable__roundtable-converge` on the prior dispatch
   (opt-in; skip it for a single-model panel or a tight budget; see
   `docs/process/REVIEW-PANEL.md` §"When the panel splits") — if it clearly
   resolves the split, `set-review <dir> precheck APPROVED 2` instead.
6. If the panel agrees: `set-review <dir> precheck APPROVED N`.

**Panel routing-override (Step 1.3 only).** If the panel's synthesized
findings include an explicit routing-flag correction (e.g., "panel
recommends `arch_advisor_needed: true`"), the orchestrator MAY apply it
directly — WITHOUT re-running pre-check — via a single-field merge:
```
uv run scripts/keel-routing.py merge-routing-flag <dir> arch_advisor_needed=true
```
This is an explicit P6 override: the panel's finding is authoritative over
pre-check's classification *for that one flag* (the panel has the full
brief context; pre-check saw only the spec). Use `merge-routing-flag`, not
`set-routing` — `merge-routing-flag` preserves the other flags;
`set-routing` would wipe them. Log the override in the attempt file
(`route-override: arch_advisor_needed false→true (panel finding)`). If the
override flips a flag YES→NO, also run route-reset below.

**Route-reset on routing-flag flip (YES→NO).** Whenever a revised pre-check
envelope (step 4) or a panel override above flips any routing flag from
YES to NO, stale downstream files and routing entries must be cleared
before continuing (see `docs/process/HANDOFF-CONTRACT.md` §"Route-reset
semantics"):
1. Recompute the **entire** expected file set from the new routing flags
   (not just the flipped flag — dependent gate files and deliberation
   subdirs too; the full algorithm is in HANDOFF-CONTRACT.md).
2. Delete any `<dir>/*.md` file or `<dir>/<touchpoint>-review/` subdir
   that is NOT in the new expected set.
3. For each gate whose file was deleted, clear its routing entry:
   ```
   uv run scripts/keel-routing.py clear-gate <dir> <code_review|spec_review|safety|arch_verify>
   ```
   (`merge-routing-flag` only touches `routing.routing.*`; gate verdicts
   live at `routing.gates.*` and need `clear-gate`.)
4. For each deliberation touchpoint whose subdir was deleted:
   ```
   uv run scripts/keel-routing.py clear-review <dir> <precheck|design|landing>
   ```
5. Log the reset in the `precheck-review/attempt-NN.md` block being
   written: `route-reset: deleted <files>; cleared <routing entries>`.

Flags that flipped NO→YES delete nothing — the newly-needed agent writes
its file on dispatch.

The panel is advisory on verdict. Pre-check remains the authoritative
router for the *brief*; the panel override and route-reset above are the
only paths that mutate routing flags without re-running pre-check.

### Step 1.5: Researcher (if needed)
If `routing.routing.researcher_needed` is YES, run the per-hop protocol:
dispatch `researcher` with `<dir>`, target filename `researcher.md`, and
the specific questions from the execution brief. It self-writes its
research brief to `<dir>/researcher.md` (full-file overwrite on re-run).
Upstream files to read: `[resolved-work-item.json, pre-check.md]`.

### Step 1.7: Arch-advisor consultation (if architecture-tier)
If `routing.routing.arch_advisor_needed` is YES (or complexity is
architecture-tier), run the per-hop protocol: dispatch
`arch-advisor-consult` with `<dir>`, target filename
`arch-advisor-consult.md`, and upstream files
`[resolved-work-item.json, pre-check.md, researcher.md]` (researcher.md only
if it exists). It provides architecture-level guidance before
design/implementation and self-writes `<dir>/arch-advisor-consult.md`
(full-file overwrite on re-run). This agent is always dispatched at the high-reasoning tier.

### Step 2: Designer (if needed)
If `routing.routing.designer_needed` is YES, run the per-hop protocol:
dispatch `backend-designer` (backend pipeline) or `frontend-designer`
(frontend pipeline). Target filename is the agent name + `.md`
(`backend-designer.md` or `frontend-designer.md`); the other variant's
file is never created. Upstream files to read:
`[resolved-work-item.json, pre-check.md, arch-advisor-consult.md]` (the last
two only if present). The designer self-writes its blueprint as a
full-file overwrite on re-run (e.g. after a review-panel design kickback).
Designers run at the high-reasoning tier for standard+ complexity, the
standard tier only for trivial (per the per-agent override table).

### Step 2.5: Review panel — design review

Runs when `designer_needed: YES`. Reviews the designer's blueprint
before tests are written. Run the ONE panel selected in Step 0.5
(`review_panel`) — personas OR roundtable, never both; whichever runs
follows `docs/process/REVIEW-PANEL.md`, verdict `APPROVED | CONCERNS`.

**Persona panel (`review_panel: personas`, the default):**
1. Dispatch FOUR `review-panelist` agents IN PARALLEL (one message, four
   tool calls), one per lens. Each panelist's spawn message opens with the
   Spawn-message preamble above (`[KEEL-ROLE review-panelist]`); the lens is
   task context. Give each its lens, touchpoint = `design`,
   `<dir>`, and the designer file to read (`<dir>/backend-designer.md` or
   `<dir>/frontend-designer.md`). Each reviews the blueprint through its
   lens — Architect on structure/simplicity/fit, Adversary on failure
   modes and trust boundaries, Skeptic on missing cases, Pragmatist on
   scope. (Lens-to-tier: Architect + Adversary always at the high-reasoning
   tier; Skeptic + Pragmatist follow pretriage. Panelists write no file — they
   return
   their review to the orchestrator, which synthesizes the attempt file.)
2. Synthesize the four returns (agreed/solo/tension, severity-ranked).

**Roundtable panel (`review_panel: roundtable`):**
1. Call `mcp__roundtable__roundtable-blueprint` with the designer output.
2. Call `mcp__roundtable__roundtable-critique` with the designer output.

**Record, verdict, kickback (both panels):**
3. **Write the attempt file.** The orchestrator writes the synthesis to a
   new `<dir>/design-review/attempt-NN.md` (zero-padded from `01`, no
   gaps): `# Design review` then a `### Attempt N — <verdict>` block
   (personas: one line per lens + synthesized findings; roundtable:
   `#### Blueprint` / `#### Critique`). Past attempt files are immutable.
   **As the very next action**, update the sidecar and record the verdict:
   ```
   uv run scripts/keel-routing.py record-attempt-hash <dir> design N
   uv run scripts/keel-routing.py set-review <dir> design <verdict> N
   ```
4. If critical/major concerns: send findings to the designer. It
   self-writes the revised blueprint to `<dir>/<designer>.md` (full-file
   overwrite, no "(revised, attempt N)" framing). Bump the attempt to 2,
   re-run the panel, write `attempt-02.md` + its sidecar hash.
5. If still concerns after attempt 2: proceed (advisory, not blocking),
   `set-review <dir> design CONCERNS 2`, log unresolved items in the
   attempt file. Roundtable panel only: the orchestrator MAY first invoke
   `mcp__roundtable__roundtable-converge` (opt-in; skip for a
   single-model panel or tight budget; see `docs/process/REVIEW-PANEL.md`
   §"When the panel splits") — if it resolves the concerns,
   `set-review <dir> design APPROVED 2` instead.
6. If no concerns: `set-review <dir> design APPROVED N`.

The panel is advisory. It never directly blocks the pipeline — its
findings feed back through the designer for revision, not through
authoritative gates.

### Step 3: Test-writer
Run the per-hop protocol: dispatch `test-writer` with `<dir>`, target
filename `test-writer.md`, and upstream files
`[resolved-work-item.json, pre-check.md, <designer>.md]` (designer file only
if present). It writes tests, never implementation, and self-writes its
report to `<dir>/test-writer.md` (full-file overwrite on re-run).

### Step 4: Implementer (if needed)
If `routing.routing.implementer_needed` is NO, skip to Step 5 (review
gates) or Step 8 (landing-verifier).
Otherwise run the per-hop protocol: dispatch `implementer` with `<dir>`,
target filename `implementer.md`, and upstream files
`[resolved-work-item.json, pre-check.md, <designer>.md, test-writer.md]`. It
writes code to pass the tests, never modifies tests, and self-writes its
report to `<dir>/implementer.md` (full-file overwrite on re-run, e.g.
after a spec-reviewer DEVIATION or code-reviewer CONCERNS). The
report MUST include a `**Changed paths:**` list — doc-gardener reads it in
Step 9 for blast-radius scope.

### Step 5: Parallel review gates

The read-only review gates examine the SAME implementer diff and do not
depend on one another, so they run CONCURRENTLY, not in series. Dispatch
all applicable gates in one message (multiple tool calls), then
consolidate. This is a scheduling change only: every gate still runs,
every per-gate budget below is unchanged, and no gate's guarantee is
weakened — it collapses four sequential gate hops (and the orchestrator
round-trips between them) into one parallel slot.

**Gates — dispatch the applicable ones together.** Each writes its OWN
`<agent>.md` concurrently (no race — distinct filenames):
- `code-reviewer` — when `implementer_needed: YES`. `APPROVED | CONCERNS`.
  Quality: DRY, patterns, edge cases, architecture fit. Writes
  `code-reviewer.md`. Routing gate name: `code_review`.
- `spec-reviewer` — when `implementer_needed: YES`. `CONFORMANT |
  DEVIATION`. Conformance to spec. Writes `spec-reviewer.md`. Routing gate
  name: `spec_review`.
- `safety-auditor` — only if `safety_auditor_needed: YES`. `PASS |
  VIOLATION`. Writes `safety-auditor.md`. Routing gate name: `safety`.
  Always dispatched at the high-reasoning tier when it runs.
- `arch-advisor-verify` — only if `arch_advisor_needed: YES` AND
  `implementer_needed: YES` (it verifies *against* an implementation).
  `SOUND | UNSOUND`. Structural soundness, not just conformance. Writes
  `arch-advisor-verify.md`. Routing gate name: `arch_verify`. Always at the high-reasoning tier.

Pass each gate `<dir>` + its target filename + upstream files
`[resolved-work-item.json, pre-check.md, implementer.md, <designer>.md]`.

**1. Dispatch + verify + record.** Before each round, increment the
attempt counter you pass to `set-gate` for every gate dispatched that
round (`code_review`, `spec_review`, `safety`, `arch_verify` — the
arch-verify counter is SEPARATE from spec-review; they do not interact).
After they return: for each gate, verify its `<dir>/<agent>.md` per the
per-hop file-verification rule (exists, non-empty, mtime advanced) — HALT
on any failure — then run the verdict-divergence check (sub-step 4a
below). Finally write each verdict:
```
uv run scripts/keel-routing.py set-gate <dir> \
  <code_review|spec_review|safety|arch_verify> <VERDICT> <attempt>
```
`set-gate` takes the helper's exclusive lock, so concurrent calls
serialize safely.

**2. All pass → land.** If every gate that ran passed (APPROVED +
CONFORMANT + PASS + SOUND), proceed to Step 8 (landing-verifier).

**3. Any fail → one consolidated fix.** Collect the findings from ALL
failing gates' `<agent>.md` files and send them to `implementer` in a
SINGLE dispatch; it self-writes the revised `implementer.md`. The
implementer fixes everything at once — one fix cycle, not a serial
fix-per-gate ping-pong. Then run the next round: re-dispatch the gates
that failed, concurrently. A gate that passed is settled and does not
re-run — EXCEPT after a fix that includes a structural (arch UNSOUND)
change, which can ripple: re-run spec-reviewer and safety-auditor
alongside arch-advisor-verify that round (this preserves the prior
arch-verification re-run rule).

**4a. Verdict-divergence check.** After verifying each gate file and
BEFORE writing routing, confirm the gate's file body agrees with its
envelope. The envelope is authoritative on verdict (per
`docs/process/HANDOFF-CONTRACT.md` §"Verification model" verdict-authority
rule), but a disagreement is a correctness signal worth surfacing rather
than silently routing on one or the other. For each gate file:
```
actual=$(grep -m1 '^\*\*Verdict:\*\*' <dir>/<agent>.md | sed 's/^\*\*Verdict:\*\* *//')
```
Compare `actual` to the envelope's `verdict` translated to the gate's
verdict-string form (e.g. `pass`→`APPROVED` for code-reviewer,
`pass`→`CONFORMANT` for spec-reviewer, `pass`→`PASS` for safety-auditor,
`pass`→`SOUND` for arch-advisor-verify). If they differ → HALT (P7):
> *"Gate `<agent>` verdict divergence: envelope says `<envelope-verdict>`,
> file body says `<actual>`. The envelope is authoritative but this
> mismatch is a correctness signal. Re-dispatch the gate for consistent
> output, or — if you judge the body correct — set the verdict manually
> with `keel-routing.py set-gate` and fix the divergent `**Verdict:**`
> line, then continue."*
Only write `set-gate` once the body and envelope agree.

**4. Per-gate budgets — unchanged, tracked independently:**
- **code-reviewer — max 1.** Still CONCERNS after one fix → proceed
  anyway (spec conformance is the harder gate).
- **spec-reviewer — max 2.** Still DEVIATION after attempt 2 → STOP,
  escalate to human (decompose the feature or fix the spec; see
  docs/process/FAILURE-PLAYBOOK.md).
- **safety-auditor — max 3, never negotiable.** Still VIOLATION after 3 →
  STOP, escalate to human (the invariant rule or the spec may need review).
- **arch-advisor-verify — max 1.** Still UNSOUND after one fix → escalate
  to human.

Each fix and re-run happen on the same evolving diff, so the consolidated
verdicts always reflect the code that actually lands.

### Step 8: Landing-verifier
Run the per-hop protocol: dispatch `landing-verifier` with `<dir>`, target
filename `landing-verifier.md`, and upstream files
`[resolved-work-item.json, implementer.md]`. It runs tests and verifies
everything is complete, self-writing its report to
`<dir>/landing-verifier.md`. Its envelope verdict is `VERIFIED` (all gates
passed, tests pass) or `BLOCKED`. If BLOCKED, fix blockers and re-run.
landing-verifier runs at the standard tier always.

### Step 8.5: Review panel — landing review

Runs for every variant whose `review_panel` is `personas` or `roundtable`. **Bootstrap features set `review_panel: none` (Step 0.5 / init) and SKIP Step 8.5 entirely** — they record no landing-review verdict and trigger Step 9 on the `landing-verifier.md` artifact instead (see Step 9 Trigger). Reviews the landed implementation. Run the ONE panel selected in Step 0.5 (`review_panel`) — personas OR roundtable, never both; whichever runs follows
`docs/process/REVIEW-PANEL.md`, verdict `APPROVED | CONCERNS`.

**Persona panel (`review_panel: personas`, the default):**
1. Dispatch FOUR `review-panelist` agents IN PARALLEL (one message, four
   tool calls), one per lens. Each panelist's spawn message opens with the
   Spawn-message preamble above (`[KEEL-ROLE review-panelist]`); the lens is
   task context. Give each its lens, touchpoint = `landing`,
   `<dir>`, and `implementer.md` (for the summary + `**Changed paths:**`).
   Panelists get the diff themselves (scoped `git diff` over the
   implementer's changed-paths list). Adversary on production failure modes
   and security, Skeptic on completeness/edge cases, Architect on
   structural fit, Pragmatist on scope creep. Architect + Adversary run at
   the high-reasoning tier always; Skeptic + Pragmatist follow pretriage.
   Panelists write no file — they return their review to the orchestrator.
2. Synthesize the four returns (agreed/solo/tension, severity-ranked).

**Roundtable panel (`review_panel: roundtable`):**
1. Call `mcp__roundtable__roundtable-crosscheck` with the implementation summary.
2. Call `mcp__roundtable__roundtable-critique` with the implementation summary.

**Record, verdict, kickback (both panels):**
3. **Write the attempt file.** The orchestrator writes the synthesis to a
   new `<dir>/landing-review/attempt-NN.md` (zero-padded from `01`, no
   gaps): `# Landing review` then a `### Attempt N — <verdict>` block
   (personas: one line per lens + synthesized findings; roundtable:
   `#### Crosscheck` / `#### Critique`). Past attempt files are immutable.
   **As the very next action**, update the sidecar and record the verdict:
   ```
   uv run scripts/keel-routing.py record-attempt-hash <dir> landing N
   uv run scripts/keel-routing.py set-review <dir> landing <verdict> N
   ```
4. If critical concerns: send findings to implementer; it self-writes the
   revised `implementer.md`, then re-run the full gate chain (each re-run
   gate max 1 attempt; bump its `set-gate` attempt counter):
   `code-reviewer` → `spec-reviewer` → `safety-auditor?` →
   `arch-advisor-verify?` → `landing-verifier`. Verify + divergence-check +
   `set-gate` each per Step 5. If a re-run gate itself fails, escalate to
   human — do not loop further. After the chain passes, bump the landing
   attempt to 2, re-run the panel, write `attempt-02.md` + its sidecar
   hash.
5. If still concerns after attempt 2: proceed (advisory, not blocking),
   `set-review <dir> landing CONCERNS 2`, log unresolved concerns in the
   attempt file. Roundtable panel only: the orchestrator MAY first invoke
   `mcp__roundtable__roundtable-converge` (opt-in; skip for a
   single-model panel or tight budget; see `docs/process/REVIEW-PANEL.md`
   §"When the panel splits") — if it resolves the concerns,
   `set-review <dir> landing APPROVED 2` instead.
6. If no concerns: `set-review <dir> landing APPROVED N`.

The review panel always runs for `personas`/`roundtable` variants, so for
those the landing review always records a `review-landing` verdict in
`routing.json` — that recorded verdict (not a status latch) is what Step 9
triggers on; bootstrap (`review_panel: none`) skips this and triggers on the
`landing-verifier.md` artifact.

The panel is advisory, not authoritative. Its findings feed back through
the existing authoritative gates on re-run. It never directly blocks
landing; it triggers re-evaluation by the authoritative gates.

### Step 9: Completion procedure (doc GC → tech-debt → tick + commit → archive)

**Trigger (per lane), read from first-instance signals the repo already holds —
not a status latch:**
- **Standard variants** (backend / frontend / cross-cutting): the Step-8.5
  landing review records a `review-landing` verdict (`APPROVED` or `CONCERNS`
  — both proceed; `CONCERNS` after attempt 2 is advisory, not blocking, per
  Step 8.5 sub-step 5). The panel always records a landing verdict, so Step 9
  triggers on the verdict's presence, not specifically on `APPROVED`.
- **Karta variant** (lean lane; it skips Step 8.5 and dispatches no
  landing-verifier): the recorded gate verdicts `gates.safety.verdict == PASS`
  AND `gates.conformance.verdict == CONFORMANT` are both present in
  `routing.json` (written by `karta-pipeline` via `set-gate`). The green gate
  is a direct orchestrator command that writes no routing verdict (P4 — `gates`
  has no `green` key), so the arm keys on the safety + conformance gate records
  karta already writes, not on a stored green-gate key.
- **Bootstrap variant** (no review gates, no landing review): bootstrap records
  NO routing verdict — landing-verifier writes only `<dir>/landing-verifier.md`
  and calls no `set-gate`/`set-review`. The bootstrap signal is therefore the
  on-disk artifact: bootstrap reaches Step 9 directly once `landing-verifier`
  returns its `pass` envelope (body `Status: VERIFIED`) and
  `<dir>/landing-verifier.md` exists. There is no `routing.json` verdict to
  wait on.

Done is **repo-local**: the feature commit on the `keel/WI##-<slug>` branch,
the archived handoff under `completed/handoffs/`, and the backlog `[x]`. The
pipeline neither pushes nor opens a PR — integration through a forge is the
human's separate `/keel-submit` step. Sub-steps run in order. **Archive is
the last step** — it only happens once the feature commit lands. If any
earlier sub-step fails, STOP and print the error; the handoff stays in
`active/`, the orchestrator halts, and the human resolves the failure
before any further action.

1. **Doc garbage collection.**
   Dispatch `doc-gardener` agent unconditionally as a **self-writer**:
   pass it `<dir>` + target filename `doc-gardener.md`; it self-writes its
   Doc Garden Report to `<dir>/doc-gardener.md` per the contract. Verify
   the file per the per-hop rule. Always run; let the agent decide whether
   a sweep finds drift. doc-gardener runs at the standard tier.

   **Mode selection by pipeline variant:**
   - **Bootstrap variant** (features tagged `Binder-exempt: bootstrap`, which skip pre-check + implementer):
     dispatch in ad-hoc mode. The directory lacks the execution brief and
     implementer report that pipeline mode requires.
   - **Standard variants** (backend / frontend / cross-cutting): dispatch
     in pipeline mode, which scopes findings to the blast radius plus
     the repo-wide §P5 timeline-artifact sweep.
   - **Maintenance lane** (`Binder-exempt: infra`/`trivial` or incidental churn,
     run via Step 0, Maintenance): dispatch in ad-hoc mode. There is no handoff
     directory, so the gardener reports repo-wide drift and the orchestrator
     applies the fixes directly to the working tree before the maintenance
     commit (Step 0, Maintenance, step 5) — this Step 9 block does not run for
     the maintenance lane.

   Prompt shape (pipeline mode — standard variants):
   ```
   **Mode:** pipeline
   **Feature directory:** <dir>   (docs/exec-plans/active/handoffs/WI##-<slug>/)
   **Target filename:** doc-gardener.md

   Read implementer.md for `**Changed paths:**`. Run per your
   §Operating modes. Scope: blast-radius, feature-ID coverage,
   contract-surface coverage, plus the mandatory repo-wide §P5 sweep.
   Self-write the Doc Garden Report to <dir>/doc-gardener.md with stable
   subsection headers and a `doc_garden_verdict` line.
   ```

   Prompt shape (ad-hoc mode — bootstrap variant):
   ```
   **Mode:** ad-hoc
   **Feature directory:** <dir>
   **Target filename:** doc-gardener.md

   Run the full baseline sweep (the project guide / ARCHITECTURE.md / backlog
   / tech debt / design specs) plus the mandatory repo-wide §P5 sweep.
   Self-write the Doc Garden Report to <dir>/doc-gardener.md with stable
   subsection headers and a `doc_garden_verdict` line.
   ```

   **Verdict capture.** Parse `doc_garden_verdict:` from
   `<dir>/doc-gardener.md` (expect `CLEAN` or `DRIFT_FOUND`) and
   `drift_count:` (integer) and record both in `routing.json`:
   ```
   uv run scripts/keel-routing.py set-doc-garden <dir> \
     <CLEAN|DRIFT_FOUND> <drift_count>
   ```
   The commit-message verdict block in sub-step 3 emits `doc-garden:
   CLEAN` or `doc-garden: DRIFT_FOUND (N fixes applied)` so the outcome
   survives in git history.

   If the report lists STALE or MISSING items, the orchestrator applies
   the fixes to the working tree NOW (before commit, so they land in
   the same commit — no amend, no post-push mutation, stable PR diff
   from open).

   **Halt handling.** If the agent halts with a pipeline-mode precondition
   failure (missing handoff directory, missing `pre-check.md`, missing
   `implementer.md`), re-dispatch the agent in ad-hoc mode (second prompt
   shape above) — the full sweep produces a superset of what pipeline mode
   would have found. Only STOP Step 9 entirely if the ad-hoc re-dispatch
   also halts.

2. **Tech-debt log.**
   The orchestrator performs this update directly, using its full
   run context for which shortcuts were taken; doc-gardener is
   read-only (sub-step 1) and never writes the tracker.
   If `docs/exec-plans/tech-debt-tracker.md` exists, append any new
   shortcuts discovered during the run and DELETE any resolved items.
   Do not check resolved items off with `[x]` and do not move them
   to a "Resolved" / "Done" section — `git log` is the landing
   record. Accumulating a resolved-section is P5 drift the
   doc-gardener will flag.

3. **Stage and commit.**
   Because "Before Starting" enforced a clean tree, every modified or
   new file in the working tree now is this feature's work.

   First, **mark this feature complete in the backlog.** In
   `docs/exec-plans/active/backlog.md`, change this WI##'s checkbox
   from `- [ ]` to `- [x]`. This is the authoritative completion tick: the
   human never edits backlog checkboxes by hand, so the pipeline owns the
   `[ ]`→`[x]` transition for every feature (bootstrap and product alike).
   For bootstrap features this is what eventually flips the greenfield
   bootstrap gate to complete once the whole bootstrap set has landed.
   The tick happens here — before `git add -A` — so it lands in the feature
   commit. Idempotent: if the box is already `[x]`, no-op. If this WI## has
   **no** entry in the backlog, HALT with a P7 CTA naming the missing WI## (a
   landed feature must trace to a backlog entry) — do not commit. Halting
   here is pre-commit, so it leaves no half-landed state; the human adds the
   entry and re-runs Step 9.

   Then stage everything:

     git add -A

   then drop anything **tracked-but-now-ignored** from the index —
   `.gitignore` never untracks files committed before the rule existed
   (seeded bytecode, build outputs), and they would otherwise ride every
   feature commit as churn:

     if [ -n "$(git ls-files -ci --exclude-standard)" ]; then
       git ls-files -ci --exclude-standard -z | xargs -0 git rm --cached --
     fi

   `git add -A` sweeps the whole working tree, so the project's
   `.gitignore` must already cover generated artifacts (`__pycache__/`,
   build outputs, coverage dirs, etc.) or they land in the feature commit.
   KEEL ships no `.gitignore` of its own — that policy belongs to the
   project; if **untracked** junk appears in the staged set, the fix is a
   `.gitignore` rule, not a narrower `git add`; if **tracked** junk appears,
   the `git rm --cached` sweep above already owns that case.

   Compose the commit subject from the Binder:
   - The orchestrator was invoked with a full Binder path (e.g.,
     `docs/exec-plans/binders/my-feature.json`) — that's in conversation
     context from Step 1. Read the target feature's `title` via
     `jq '.work_items[] | select(.id=="WI##") | .title' <binder-path>`.
   - If the Binder or target feature is missing, fall back to the handoff
     slug with hyphens replaced by spaces (e.g., `WI42-oauth-pkce-flow`
     → `oauth pkce flow`). The fallback is lossy but deterministic.

   Message format (HEREDOC):

     feat(WI{id}): {feature title from Binder .work_items[].title}

     Binder: {binder_ref from routing.json, or "n/a (bootstrap)" when unset}
     Pipeline: {pipeline variant: bootstrap|backend|frontend|cross-cutting|karta}
     Verdicts:
     {verdict_lines}

     🤖 Generated with KEEL pipeline

   Read `binder_ref` and `pipeline` from `routing.json`
   (`uv run scripts/keel-query.py routing <dir> binder_ref`). Where
   `{verdict_lines}` is built by reading the `gates`, `review`, and
   `doc_garden` blocks of `routing.json` and emitting one line per verdict
   that is set. Skip any verdict whose field is unset (agent did not run in
   this pipeline variant). Format per line:

     spec-review: CONFORMANT (attempt 1)
     safety:      PASS (attempt 1)
     arch-advisor-verify: SOUND
     code-review: APPROVED (attempt 1)
     doc-garden:  CLEAN | DRIFT_FOUND (N fixes applied)
     review-precheck: APPROVED (attempt 1)
     review-design: APPROVED (attempt 1)
     review-landing: APPROVED (attempt 1)

   Record the panel used on its own line so it survives in git history.
   The review panel always runs (personas by default), so there is no
   SKIPPED case; if roundtable was requested but its MCP was unavailable,
   the fallback to personas is part of the record:

     review-panel: personas
     review-panel: personas (roundtable requested; MCP unavailable)

   If all verdict fields are unset (bootstrap variant), emit the single
   line: `Verdicts: n/a (bootstrap variant)`.

   Commit with the constructed message.

4. **Archive the handoff (folded into the feature commit).**
   With push and PR gone, archiving is a **plain local amend** — no remote
   ever sees the pre-amend commit, so no force-with-lease and no re-push.
   The archive location is the done signal.

   **Crash-window recovery (P7).** The amend creates one half-state: the
   `git mv` is done but the amend has not yet committed. On entry to this
   sub-step, detect it **before** moving anything: if the handoff directory
   already exists under `completed/handoffs/WI{id}-{slug}/` (staged or
   committed) but the current `HEAD` commit does not contain it
   (`git ls-tree -r --name-only HEAD -- docs/exec-plans/completed/handoffs/WI{id}-{slug}/`
   prints nothing), the prior run moved the directory but did not finish the
   amend. **Do NOT re-run the `git mv`** — the source is already gone.
   Complete the amend instead, or HALT (P7):

       Half-archived handoff detected for WI{id}-{slug}:
       docs/exec-plans/completed/handoffs/WI{id}-{slug}/ exists but HEAD
       does not contain it — a prior run moved the handoff and crashed
       before `git commit --amend`. Evidence:
         git status --porcelain docs/exec-plans/completed/handoffs/WI{id}-{slug}/
       Finish the archive:
         git add -A docs/exec-plans/
         git commit --amend --no-edit
       Then re-run /keel-pipeline WI{id} — Step 9 will see HEAD contains the
       archive and skip straight to completion. Do not re-run `git mv`; the
       source is already moved.

   Otherwise, move the entire handoff **directory** (all of `routing.json`,
   `resolved-work-item.json`, every `<agent>.md`, and every
   `<touchpoint>-review/` subdir):
   ```
   git mv docs/exec-plans/active/handoffs/WI{id}-{slug}/ \
          docs/exec-plans/completed/handoffs/WI{id}-{slug}/
   ```
   The `.attempt-hashes.json` sidecars are committed write-once integrity
   state and **move with the archive** — `git mv` carries them along with
   the rest of the directory. They MUST travel with it: `validate-handoff.py
   docs/exec-plans/completed/handoffs/` is fail-closed and HALTs if attempt
   files are present without their sidecar (see
   `docs/process/HANDOFF-CONTRACT.md` §"The three orchestrator-owned files",
   item 3). They are not gitignored; do not add a gitignore rule for them.

   Fold the move into the feature commit:
   ```
   git commit --amend --no-edit
   ```
   This is a local amend only — the commit was never pushed, so there is no
   remote to reject it and no force needed. If the amend itself fails (e.g.
   a pre-commit hook), STOP and print the raw error; the directory is already
   moved, so on re-run the crash-window detection above completes the amend.
   Archive is the LAST sub-step: it only runs after the feature commit
   exists (sub-step 3). Any earlier halt leaves the directory in `active/`
   so re-running picks up from where it stopped.

## Halt CTA wording

The exact wording emitted at each halt path. Step 0's halt branches and
the restack subsection reference these by name.

### Intra-Binder halt (policy=halt)

```
WI02 requires WI01 (intra-Binder).
WI01 status: branch keel/WI01-<slug> exists locally; parent_sha <SHA>
            is not an ancestor of <base-branch>.

Options:
  1. Merge or integrate WI01 to the local trunk, then re-run /keel-pipeline WI02.
  2. Set "Branching policy: stack" in the project guide to stack WI02 on WI01's
     branch. Note: stack applies to intra-Binder Needs only; cross-Binder
     Needs always halt.
```

### Cross-Binder halt (always)

```
WI05 requires WI04 (cross-Binder).
WI04 status: not merged to <base>.

Cross-Binder dependencies always halt regardless of branching policy —
cross-Binder work is reviewed as separate cohesive products. Merge WI04
first, then re-run /keel-pipeline WI05.
```

### Restack conflict

```
Restack of keel/WI02-<slug> onto <base> halted with conflicts.

Resolve in your editor and continue:
  git status                  # see conflicted paths
  # edit, then:
  git add <paths>
  git rebase --continue       # to finish
  # or:
  git rebase --abort          # to undo and halt the pipeline
```

### Restack — merge history in feature

```
WI02's branch contains a merge commit from its previous parent
(keel/WI01-<slug>) earlier in the stack history. Auto-restacking via
`git rebase --update-refs --onto` would replay that merge and produce
duplicate changes.

Resolve manually:
  git rebase -i <base>        # drop the offending merge commit
  # or start over from a clean branch off <base> and cherry-pick
  # WI02's unique commits.
```

### Sibling fan-out (stack mode)

```
Cannot stack WI02 — direct intra-Binder Needs WI00 and WI01 are both unmerged
and neither is an ancestor of the other in the backlog dep graph.

Stacking can only target one parent. Options:
  1. Switch to "Branching policy: halt" temporarily (default), merge one
     of WI00/WI01 first, then re-run.
  2. Edit backlog.md to declare a dep edge between WI00 and WI01
     if one exists in reality, then re-run.
```

### Branch-without-handoff (orphan branch)

```
Branch keel/WI##-<slug> exists locally, but no handoff directory at
docs/exec-plans/active/handoffs/WI##-<slug>/.

Either delete the branch (`git branch -D keel/WI##-<slug>`) and re-run
to start fresh, or move a previously-aborted handoff directory back from
docs/exec-plans/abandoned/ into active/ to resume.
```

### Handoff-without-branch (orphan handoff)

```
Handoff directory exists at docs/exec-plans/active/handoffs/WI##-<slug>/
but branch keel/WI##-<slug> has been deleted.

Either restore the branch (read the parent SHA with
`keel-query.py routing <dir> branch.parent_sha`, then
`git checkout -b keel/WI##-<slug> <sha>`) or move the handoff directory to
docs/exec-plans/abandoned/ and re-run to start fresh.
```

### Brownfield adoption (Need is "unknown")

```
Need WI## has no archived handoff on <base>, no recorded parent_sha,
no branch matching keel/WI##-*, and is past the
KEEL-INVARIANT-7: legacy-through=WI## marker in backlog.md.

Either WI## landed outside KEEL (in which case bump legacy-through, or
add an archived handoff stub directory at
docs/exec-plans/completed/handoffs/WI##-<slug>/ and commit to base), or
backlog.md has drift. Resolve and re-run.
```

## Rules

- **Never skip steps.** Every agent in the pipeline runs.
- **The handoff directory is the thread.** Each agent `Read`s the upstream
  files it needs (`resolved-work-item.json` + sibling `<agent>.md`) before
  writing its own. Agents **self-write** their `<agent>.md` with the
  `Write` tool — full-file overwrite, snapshot per re-run. The orchestrator
  never transcribes agent output into a file. Deliberation is append-only:
  each panel attempt is a new `<touchpoint>-review/attempt-NN.md`.
- **The orchestrator owns routing.** Only the orchestrator writes
  `routing.json`, and only through `keel-routing.py` (locked,
  schema-validated, atomic). Never hand-edit it. Read state with
  `keel-query.py`; branch on `routing.json` fields, never on agent prose.
- **Verify the filesystem, not the prose.** A hop is proven by the
  `<agent>.md` file existing, being non-empty, and its mtime advancing —
  not by the envelope's advisory `wrote:` claim. See the per-hop protocol.
- **Pre-check decides optionals.** Only skip designer/researcher/safety-auditor if pre-check says so.
- **Spec-reviewer and safety-auditor are gates.** If they find issues, loop back to implementer.
- **You don't write code.** Agents write code. You orchestrate.
- **Docs drive code.** If there's no spec, there's no pipeline. Write the spec first.
- **Envelope verdict is authoritative; divergence halts.** Gate agents
  emit `**Verdict:**` in their `<agent>.md` body AND return a `verdict` in
  their envelope. The orchestrator routes on the **envelope** verdict (via
  `set-gate`). If the body and envelope disagree, that is a correctness
  signal — HALT per Step 5's verdict-divergence check, never silently pick
  one (P7).
- **Max 2 spec-review loops.** After 2 DEVIATION verdicts, escalate.
  Don't try harder — decompose or fix upstream.
- **Downstream reads upstream.** Each agent reads upstream Decisions and
  Constraints FIRST before starting its own work.
- **Stage 4 auto-completion.** Once the landing review records its
  `review-landing` verdict — `APPROVED`, or `CONCERNS` proceeding advisory
  per Step 8.5 sub-step 5 (or, bootstrap, `landing-verifier.md` exists with a
  `pass` envelope), the orchestrator runs Step 9 end-to-end without asking. The
  human's review surface is the commit + archived handoff on the feature
  branch — and, if they use a forge, the PR that `/keel-submit` opens later;
  not a per-step prompt. To run the pipeline without auto-completing (e.g.,
  for debugging), interrupt before Step 9 — the orchestrator will stop at the
  completion boundary.
- **Clean tree, then branch, then build.** "Before Starting" refuses a
  dirty working tree and auto-branches from the resolved `<base-branch>`
  (Step 0 item 5) BEFORE any agent runs. This is the only automatic branch
  creation the pipeline performs. Once inside a feature branch, intermediate
  pipeline writes cannot pollute base even on a halt.
- **doc-gardener is unconditional.** Step 9 sub-step 1 always dispatches
  doc-gardener; no more "if the feature was substantial" judgment call.
  Drift fixes are applied to the working tree BEFORE the commit, so they
  land in the feature commit and the archived handoff is internally
  consistent.
- **The review panel is advisory.** It never directly blocks landing.
  Findings feed back through authoritative gates (spec-reviewer,
  safety-auditor) on re-run. If the panel has concerns after max
  attempts, proceed anyway.
- **Re-check the roundtable MCP before each call — roundtable panel only.**
  When `review_panel: roundtable`, don't rely on the Step 0.5 probe;
  probe availability immediately before each roundtable tool call (120s
  timeout). On failure, fall back to the persona panel and log the
  reason. The persona panel needs no probe — it is always available.
- **Completion is repo-local.** A feature is done when three repo signals
  agree: the feature commit on its `keel/WI##-<slug>` branch, the archived
  handoff under `completed/handoffs/`, and the backlog `[x]`. The pipeline
  never pushes and never opens a PR — integration through a forge is the
  human's separate `/keel-submit` step. To change completion mechanics, edit
  Step 9 in the installed skill file.
- **Done is the archive location, not a status field.** `routing.json`
  `status` is only `IN-PROGRESS | BLOCKED` — it never latches a terminal
  done value. Consumers key on the handoff's **archive location**
  (`completed/handoffs/…` means the pipeline finished commit + archive),
  never on a status field. Step 9 triggers off the recorded `review-landing`
  verdict (standard variants), the recorded `gates.safety`/`gates.conformance`
  verdicts (karta), or the on-disk `landing-verifier.md` artifact (bootstrap —
  which records no routing verdict), not a status latch.
- **Archive is the last step.** Step 9 `git mv`s the handoff **directory**
  to `completed/` and folds it into the feature commit with a plain local
  `git commit --amend` — only after the feature commit exists. Any earlier
  halt leaves the directory in `active/` so re-running the pipeline picks up
  from where it stopped; the amend crash-window (mv done, amend pending) is
  detected on re-entry per Step 9 sub-step 4.
