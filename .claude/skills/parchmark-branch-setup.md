---
name: parchmark-branch-setup
description: Set up a git worktree + branch for a new feature or fix, with BEADS_NO_DAEMON safety
---

# ParchMark Branch Setup

Use this skill whenever you begin implementing a feature, bug fix, or any code change that requires a new branch — before writing any code.

## Inputs

Determine from context:
- **type**: `feat` or `fix`
- **description**: kebab-case short name (e.g., `add-search`, `login-redirect`)

## Steps

### 1. Validate main is clean

```bash
git status --porcelain
```

- If there are uncommitted changes on main, **STOP** and warn the user. Do not proceed with a dirty working tree.
- If on a branch other than main, confirm with the user before branching from it.

### 2. Pull latest main

```bash
git pull origin main
```

### 3. Create the worktree

```bash
mkdir -p .worktrees
git worktree add .worktrees/{type}/{description} -b {type}/{description}
```

**If the worktree already exists:** Ask the user whether to reuse or remove it:
- Reuse: `cd .worktrees/{type}/{description}` and continue
- Remove: `git worktree remove .worktrees/{type}/{description}` then recreate

**If the branch already exists:** Ask the user — this usually means prior work exists.

### 4. Set BEADS_NO_DAEMON

```bash
export BEADS_NO_DAEMON=1
```

This is **mandatory**. Worktrees share the beads database and the daemon may commit to the wrong branch without this.

### 5. Verify setup

Run all checks — **do not proceed unless all pass**:

```bash
# Worktree exists
git worktree list | grep ".worktrees/{type}/{description}"

# Branch exists
git branch | grep "{type}/{description}"

# Env var is set
echo $BEADS_NO_DAEMON  # Must output "1"
```

### 6. Report

Print a summary:
- Branch name: `{type}/{description}`
- Worktree path: `.worktrees/{type}/{description}`
- Confirmation that BEADS_NO_DAEMON is set

Then change working directory to the worktree:
```bash
cd .worktrees/{type}/{description}
```

## Failure Modes

| Situation | Action |
|-|-|
| Uncommitted changes on main | Abort with warning, suggest stash or commit |
| Worktree already exists | Ask: reuse or remove? |
| Branch already exists | Ask: resume prior work or create new name? |
| BEADS_NO_DAEMON not confirmed | Retry export, never proceed without it |
| `git pull` fails | Warn about network/auth, ask user to resolve |
