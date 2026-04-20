---
name: parchmark-branch-setup
description: Create a fresh branch off main for a new feature or fix
---

# ParchMark Branch Setup

Use this skill whenever you begin implementing a feature, bug fix, or any code change that requires a new branch — before writing any code.

## Inputs

Determine from context:
- **type**: `feat` or `fix`
- **description**: kebab-case short name (e.g., `add-search`, `login-redirect`)

## Steps

### 1. Validate starting point is clean

```bash
git status --porcelain
```

- If there are uncommitted changes, **STOP** and warn the user. Do not proceed with a dirty working tree.
- If not on `main`, confirm with the user before branching from the current branch.

### 2. Pull latest main

```bash
git checkout main
git pull origin main
```

### 3. Create the branch

```bash
git checkout -b {type}/{description}
```

**If the branch already exists:** Ask the user — this usually means prior work exists.

Worktrees are optional. If the user prefers isolation, offer:

```bash
mkdir -p .worktrees
git worktree add .worktrees/{type}/{description} -b {type}/{description}
cd .worktrees/{type}/{description}
```

### 4. Verify setup

```bash
git branch --show-current   # must print "{type}/{description}"
```

### 5. Report

Print a summary:
- Branch name: `{type}/{description}`
- Location: repo root (or worktree path if used)

## Failure Modes

| Situation | Action |
|-|-|
| Uncommitted changes | Abort with warning, suggest stash or commit |
| Branch already exists | Ask: resume prior work or create new name? |
| `git pull` fails | Warn about network/auth, ask user to resolve |
