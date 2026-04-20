---
name: parchmark-land
description: Session completion — commit, push, verify all work is landed
---

# ParchMark Land

Use this skill when ending any work session, before reporting completion to the user — ensures all work is committed and pushed.

## Steps

### 1. Run quality gates

Check if code changed:
```bash
git diff --name-only HEAD
git diff --name-only --cached
```

If any code files changed, run:
```bash
make test
```

**If tests fail:** Fix the issues before proceeding. Never skip tests.

If only non-code files changed (docs, config), skip tests.

### 2. Commit and push

```bash
# Stage relevant files
git add <specific-files>

# Commit
git commit -m "descriptive message"

# Rebase on latest
git pull --rebase origin main

# Push
git push -u origin <branch-name>
```

**If no changes to commit:** Skip commit steps, proceed to verification.

**If push fails:**
- Upstream diverged → `git pull --rebase` and retry
- Auth failure → ask user to resolve
- Other → diagnose and report

### 3. Verify remote state

```bash
git status
```

Output **must** show "Your branch is up to date with" the remote. If not, diagnose and fix.

### 4. Hand off

Print summary:
- **Branch:** current branch name
- **PR:** link if one exists (`tea pr list` or `gh pr list`)
- **Next steps:** what the next session should pick up

## Failure Modes

| Situation | Action |
|-|-|
| `make test` fails | Fix before proceeding, never skip |
| `git push` fails | Diagnose (diverged? auth?), resolve, retry |
| No changes to commit | Skip commit, still verify and hand off |
