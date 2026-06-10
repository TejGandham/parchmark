---
name: keel-submit
description: Push built-but-unsubmitted keel/WI##-* branches and open one PR per branch, bottom-up, for a binder (or a narrowed WI list). The forge ceremony lifted out of the pipeline — read nothing, derive publication state from the repo + forge at runtime. Use after /keel-pipeline or /karta-drive has built and archived work locally and you want it on a forge as a stack of PRs. Serves both lanes; branches are keel/WI##-* in both.
---

# /keel-submit — the forge ceremony

`/keel-submit` is **ceremony**, not pipeline. Building a feature — code on its
`keel/WI##-<slug>` branch, handoff archived to `completed/handoffs/`, backlog
`[x]` — is *done* (repo-local; see
[`docs/design-docs/mvp-lane/2026-06-03-repo-local-done-design.md`](../../../docs/design-docs/mvp-lane/2026-06-03-repo-local-done-design.md) and
`keel-pipeline` §"Step 9"). Pushing to a remote and opening a PR are a
forge-specific ritual that bakes in one opinionated answer about where code must
end up. This skill performs that ritual on demand, for whoever uses a forge, and
**stores nothing**: publication state is fully derivable from remote-tracking refs
plus the forge's PR list (jj records publication the same way — bookmark position
against `refs/remotes`, no parallel field).

It serves **both** lanes. Branches are `keel/WI##-<slug>` in both `keel-pipeline`
and `karta-pipeline`/`karta-drive`, so there is no `karta-submit` fork (P4). This
skill is a **sibling** of `keel-pipeline`: where behavior already lives there, this
file **cites** the section rather than restating it.

```
/keel-submit <binder> [WI09,WI10,...]
```

- `<binder>` — path to the structured JSON Binder (e.g.
  `docs/exec-plans/binders/<slug>.json`). A `.md` path or missing file → HALT (P7)
  with the `/keel-refine`-first CTA, exactly as the pipelines do.
- `[WI09,WI10,...]` — optional comma-separated narrowing. Absent ⇒ **every** WI in
  the binder is a candidate. Present ⇒ exactly those WIs are candidates (an
  allow-list; narrowing never grants authority it reduces it).

## 1. Derive the candidate set + order (no state)

Candidates = the binder's WIs (optionally narrowed), in dependency order. Order is
**derived, never stored** — call the shipped helper:

```
uv run scripts/keel-drive-order.py --order --binder <binder> --set <ids>
```

where `<ids>` is the comma-separated WI list. **There is no `--all` mode** (YAGNI —
the helper requires `--set`; both callers, `/karta-drive` and this skill, enumerate
the binder's `work_items[].id`). To build `<ids>` for a non-narrowed run, read the
ids with `jq`:

```
jq -r '[.work_items[].id] | join(",")' <binder>
```

and pass that as `--set`. For a narrowed run, pass the user's list verbatim (the
helper HALTs `missing` if a listed WI is not in the binder — surface it as a P7
HALT naming the absent WI). A `cycle` halt → HALT naming the cycle candidates.

The helper's `external_needs` are **not** a submit concern here — submit publishes
whatever is built; dependency completeness was the pipeline's / `/karta-drive`'s
gate. Use only `order`.

Print the derived ordered set as the legible authorization record (P1) before any
side effect.

**Resolve the local trunk once** (`<trunk>` below). Submit reads merges, never
makes them, so trunk is the local ref — reuse `keel-pipeline` Step 0's local-trunk
ladder (first hit wins): (a) a `Base branch:` key under the project guide §Pipeline
Preferences → its value verbatim; else (b)
`git symbolic-ref --short refs/remotes/<remote>/HEAD` stripped of its `<remote>/`
prefix; else (c) `git rev-parse --verify --quiet refs/heads/main` → `main`, else
`refs/heads/master` → `master`; else (d) HALT (P7): cannot resolve the trunk
branch — add a `Base branch: <name>` line under Pipeline Preferences in the project guide
(or create the trunk branch), then re-run. (Ladder branch (b) names trunk from the
remote but does not push or fetch — it is the same trunk-naming read keel-pipeline's
Step-0 base ladder uses; `<remote>` for (b) is resolved in §3a — when a remote is
absent, branch (a) or (c) resolves trunk.)

## 2. Classify each candidate (4 arms — repo + forge state alone)

For each WI in `order`, classify from the repo and forge, **bottom-up**. Resolve the
WI's branch by **WI## prefix**, ref-guarded, as `keel-pipeline` §"Re-run
handling" / classification does — local heads only, since every arm reads local
state or the forge API, never a remote-tracking branch ref
(`git for-each-ref --format='%(refname)' 'refs/heads/keel/WI##-*'`
— quote the pattern; zsh aborts on an unmatched bare glob). The first arm that
matches wins:

1. **Already integrated → skip.** No `refs/heads/keel/WI##-*` ref **and** an
   archived handoff for the WI exists on trunk
   (`git ls-tree -r --name-only <trunk> -- docs/exec-plans/completed/handoffs/` shows
   a `WI##-*/` entry). The branch was squash-merged and cleaned up; nothing to push.

2. **Merged-but-unpruned → skip.** A local branch ref exists **and** it is an
   ancestor of trunk. **Guard the ref first** — never run `is-ancestor` on a missing
   ref (exits 128):

   ```
   git rev-parse --verify --quiet refs/heads/keel/WI##-<slug> >/dev/null \
     && git merge-base --is-ancestor keel/WI##-<slug> <trunk> && echo MERGED
   ```

   Merged locally → never re-PR a merged branch; skip.

3. **Pushed + open PR exists → skip.** The branch is on the remote and a PR already
   exists for its exact head. Probe with **`--state all`** (works on both `gh` and
   `tea`; `--state merged` is gh-only, so do not use it):

   ```
   gh pr list --state all --head keel/WI##-<slug>        # GitHub
   tea pr ls --state all                                  # Forgejo/Gitea (filter rows by head)
   ```

   Read each returned row's PR **state** (`gh pr list … --json state` gives
   `OPEN`/`CLOSED`/`MERGED`; `tea pr ls --state all` prints a state/status column).
   Branch on the matched-head row's state:
   - state **OPEN** → up to date; skip (the next pipeline run updates the open PR in place).
   - state **MERGED** → already integrated; skip (arms 1/2 normally catch this first; treat a merged row as terminal here too).
   - state **CLOSED (not merged)** → the PR was rejected/closed without merging; the built branch is unpublished. Do **not** skip and do **not** silently re-open — HALT (P7) naming the WI, e.g.:

     ```
     HALT: keel/WI##-<slug> is built but its only PR was closed without merging.
       Reopen the existing PR and re-run /keel-submit, or delete the closed PR
       and re-run /keel-submit to open a fresh one.
     ```

4. **Built + unsubmitted → SUBMIT.** A `keel/WI##-<slug>` branch exists (built,
   archive + `[x]` present), it is **not** an ancestor of trunk, and no PR exists
   for its head. This is the only arm that acts — push it and open its PR (§4).

Anything that matches none of the above (e.g. a branch with no archive) is a
**pipeline** concern, not a submit concern → HALT (P7) naming the WI and pointing
back to `/keel-pipeline`/`/karta-drive` to finish building it. Never push a
half-built branch.

## 3. Preflight — BEFORE any push (P7, no half-states)

Run these once, up front, for the whole run — a push that would later fail on auth
must never leave the stack half-published:

### 3a. Resolve the remote (runtime ladder)

There is **no stored remote** (`branch.remote_name` was deleted in v5 — see the
design). Derive it at runtime, in order:

1. `git config branch.<branch>.remote` for a candidate branch (the recorded upstream
   remote), else
2. the branch's tracking upstream (`git rev-parse --abbrev-ref <branch>@{upstream}`,
   take the remote segment), else
3. the **single** configured remote: `git remote` returns exactly one name → use it.

**0 remotes, or >1 with no upstream to disambiguate → HALT (P7)**, naming the
ambiguity and the exact next step:

```
HALT: cannot resolve a push remote for this run.
  Remotes found: <none | name1, name2, ...>.
  Add one and re-run:   git remote add origin <url>
  Or set an upstream:   git push -u <remote> keel/WI##-<slug>   (then re-run /keel-submit)
```

### 3b. Forge auth (host match) — BEFORE any push

KEEL does not infer the forge from the URL (a self-hosted Forgejo and a self-hosted
GitLab are indistinguishable by URL) — it asks each installed CLI whether it owns the
remote's host. Resolve the
remote host: `git remote get-url <remote>` (handle both `https://host/…` and
`git@host:…`). A **bare filesystem / path remote** (`/srv/…`, `file://…`, `../x.git`)
has no forge host — HALT (P7): there is nothing to open a PR against. The CTA
names both concrete no-forge paths: mirror-push the built stack manually
(`git push <remote> 'refs/heads/keel/*'`) or land it locally
(`git checkout <trunk> && git merge keel/<top-of-stack WI##-slug>` — the
whole chain rides the lineage); add a forge remote and re-run only if PRs
are wanted.

Probe the supported CLIs; the first whose **authenticated host equals the remote
host** wins (at most one authenticates per host):

- **`tea` (Forgejo/Gitea):** `command -v tea` succeeds **and** `tea logins list` has
  a login whose server host equals the remote host.
- **`gh` (GitHub):** `command -v gh` succeeds **and** `gh auth status` lists the
  remote host as authenticated.

No authenticated CLI for the host → **HALT (P7)** with the exact login command — do
not push:

```
HALT: no forge CLI is authenticated for <remote> (<host>).
  Checked: tea (not installed | no login for <host>), gh (not installed | not authenticated for <host>).
  Authenticate, then re-run /keel-submit:
    Forgejo/Gitea:  tea login add --url https://<host> --token <token>
    GitHub:         gh auth login --hostname <host>
```

### 3c. Fetch once

`git fetch <remote>` **once** for the run (not per WI), so §2's arm-3 PR-existence
probe sees branches just pushed in a prior run (arm-2 `is-ancestor` is against the
local `<trunk>`, not remote-tracking).

## 4. Submit — bottom-up, one PR per branch

For each **arm-4** WI, in `order` (bottom-up so a parent is published before its
child):

1. **Push** (a no-op when already up to date):

   ```
   git push -u <remote> keel/WI##-<slug>
   ```

2. **Open one PR**, `--base` = the parent branch when the WI stacked, else trunk.
   Read the parent from the **archived** handoff's routing — `parent_branch` /
   `parent_sha` survive into schema v5 (only `pr_url` and `branch.remote_name` were
   deleted). Resolve the handoff dir by `*/handoffs/WI##-*` prefix (active or
   completed) and read:

   ```
   uv run scripts/keel-query.py routing <handoff_dir> branch.parent_branch
   ```

   Non-null → `--base <parent_branch>`; null (bottom of stack) → omit `--base` (the
   CLI targets trunk / the repo default branch).

   **PR title/body:** reuse the WI's **feature-commit subject** — `tea` has no
   `--fill`, so title and body are passed explicitly from the commit. The subject
   follows the pipeline's commit-message convention (`keel-pipeline` §"Step 9"
   sub-step 3, *Stage and commit*): `feat(WI{id}): {feature title}`. Read it
   straight off the branch tip rather than reconstructing it:

   ```
   SUBJECT=$(git log -1 --format=%s keel/WI##-<slug>)
   BODY=$(git log -1 --format=%b keel/WI##-<slug>)
   ```

   Then:

   ```
   # Forgejo/Gitea (no --fill — pass title/body explicitly):
   tea pr create --remote <remote> --head keel/WI##-<slug> \
       [--base <parent_branch>] --title "$SUBJECT" --description "$BODY"

   # GitHub (--fill takes title/body from the commit):
   gh pr create [--base <parent_branch>] --head keel/WI##-<slug> --fill
   ```

3. Continue to the next WI.

**Writes nothing.** No `pr_url`, no routing mutation — archived handoffs are frozen
history (P5). Re-running `/keel-submit` re-classifies: arms 1–3 skip everything
already published, so a re-run submits only the **unpublished tail**. Idempotent by
construction.

## 5. Failure handling — per-candidate, fail-fast

A push or `pr create` error stops the loop immediately (fail-fast). Surface the **raw
error**, the **pushed-branch fact**, and the **resume command** (P7):

```
HALT: PR creation failed for WI##.
  <raw CLI error>
  Branch keel/WI##-<slug> is pushed to <remote>.
  Resolve the error (auth, branch policy, rate limit, network), then re-run:
    /keel-submit <binder> [<the original narrowing, if any>]
  Re-classification skips the WIs already submitted.
```

Branches pushed before the failure stay pushed (that is a fact, not a half-state to
roll back); the next run's §2 classification treats them as arm-3 and skips them.

## 6. Epilogue — the review-and-merge CTA

When the loop completes, end with the **review-and-merge-bottom-up** CTA (this is the
*human's* forge workflow; it moved here from the old pipeline ending):

> Stack submitted: one PR per WI, bottom-up, each based on its parent branch.
> Review and merge **bottom-up** — merge the base PR first; each child re-targets to
> trunk automatically as its parent merges. Re-run `/keel-submit <binder>` any time
> to publish newly built WIs.

## Orchestration rules & deltas-not-forks

This skill inherits the orchestrator's standard halt/CTA and read-discipline
conventions (cite `keel-pipeline` §"Halt CTA wording" and AGENTS.md §Framework
Principles) and authors **only** its own ceremony loop — it copies no paragraph from
`keel-pipeline`/`karta-pipeline`. Branch resolution, forge-auth host matching, the
subject convention, and the `parent_branch` semantics are all cited, not restated.

## P1–P7 notes

- **P1 (legibility):** prints the derived candidate set + order before any side
  effect — a legible authorization record.
- **P2 (progressive disclosure):** zero new entry-point surface beyond the one
  skill; classification cites `keel-pipeline` rather than re-enumerating.
- **P3 (self-sufficient):** publication state is reconstructed every run from
  remote-tracking refs + the forge PR list; nothing is read from stored state.
- **P4 (no redundant storage):** writes nothing — no `pr_url`, no remote name, no
  routing mutation. One skill serves both lanes (no `karta-submit` fork). Order is
  derived by the helper, not stored.
- **P5 (snapshot):** archived handoffs are frozen; submit reads `parent_branch` but
  never rewrites the archive.
- **P6 (authority):** the binder names the candidates; backlog `[x]` + the
  branch-anchored archive are the build signals; submit never overrides them.
- **P7 (halt with CTA):** every preflight miss (remote, auth, path-remote) and every
  per-candidate failure HALTs with the exact next command before any half-published
  state can form.
