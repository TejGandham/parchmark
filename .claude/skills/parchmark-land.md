---
name: parchmark-land
description: Session completion — commit, push, sync beads, verify all work is landed
---

# ParchMark Land

Use this skill when ending any work session, before reporting completion to the user — ensures all work is committed, pushed, and beads are synced.

## Steps

### 1. File remaining issues

Ask: "Any unfinished work to file as issues?"

For each item, create a beads issue:
```bash
bd create --title="..." --description="..." --type=task --priority=2
```

If beads is unavailable (server not running), note this and continue — don't block on it.

### 2. Run quality gates

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

### 3. Update issue status

```bash
bd list --status=in_progress
```

- Close completed issues: `bd close <id>`
- Verify no orphaned in_progress issues remain

If beads is unavailable, skip this step.

### 4. Commit and push

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

### 5. Verify remote state

```bash
git status
```

Output **must** show "Your branch is up to date with" the remote. If not, diagnose and fix.

### 6. Hand off

Print summary:
- **Branch:** current branch name
- **PR:** link if one exists (`tea pr list` or `gh pr list`)
- **Remaining issues:** any open beads issues
- **Next steps:** what the next session should pick up

## Failure Modes

| Situation | Action |
|-|-|
| `make test` fails | Fix before proceeding, never skip |
| `git push` fails | Diagnose (diverged? auth?), resolve, retry |
| No changes to commit | Skip commit, still verify and hand off |
| Beads server unreachable | Verify Tailscale is up, skip beads steps if still down, note in handoff |
