# Agent Skills Implementation Plan

Three reusable skills for ParchMark, ranked by ROI from the workflow audit.

## Skill 1: `parchmark-branch-setup`

**Problem:** Every feature/fix requires a 3-step ceremony (worktree + env var + branch naming). Forgetting `BEADS_NO_DAEMON=1` causes beads to commit to the wrong branch — destructive and silent.

### Implementation

**File:** `.claude/skills/parchmark-branch-setup.md`

**Inputs:**
- `type` — "feat" or "fix" (inferred from task context)
- `description` — kebab-case short name

**Steps the skill enforces:**
1. Validate `main` is clean and up-to-date (`git status`, `git pull origin main`)
2. Create worktree: `git worktree add .worktrees/{type}/{desc} -b {type}/{desc}`
3. Set `export BEADS_NO_DAEMON=1`
4. Verify: worktree exists, env var is set, cwd is inside worktree
5. Report branch name, worktree path, confirmation

**Failure modes to handle:**
- Worktree already exists → suggest reuse or removal
- Uncommitted changes on main → abort with warning
- BEADS_NO_DAEMON not confirmed → retry, never proceed

**AGENTS.md trigger:**
```
Use `parchmark-branch-setup` whenever you begin implementing a feature, bug fix, or any code change that requires a new branch — before writing any code.
```

**Smoke test:**
```bash
# Run skill with type=feat, description=test-smoke
git worktree list | grep ".worktrees/feat/test-smoke"
git branch | grep "feat/test-smoke"
echo $BEADS_NO_DAEMON | grep "1"
pwd | grep ".worktrees/feat/test-smoke"
# Cleanup
git worktree remove .worktrees/feat/test-smoke
git branch -D feat/test-smoke
```

---

## Skill 2: `parchmark-land`

**Problem:** Session completion is a 7-step checklist. Skipping `bd sync` before commit or forgetting `git push` strands work locally. AGENTS.md devotes two sections to this and still it goes wrong.

### Implementation

**File:** `.claude/skills/parchmark-land.md`

**Inputs:** None (operates on current branch state)

**Steps the skill enforces:**
1. **File remaining issues** — prompt: "Any unfinished work to file?" → `bd create` for each
2. **Run quality gates** — `make test` (skip if no code changed, detect via `git diff --name-only`)
3. **Update issue status** — `bd close` finished items, verify no orphaned `in_progress`
4. **Sync beads** — `bd sync` (mandatory, before commit)
5. **Commit & push**
   - `git add` relevant files
   - `git commit`
   - `git pull --rebase`
   - `git push -u origin <branch>`
6. **Verify remote state** — `git status` must show "up to date with origin"
7. **Hand off** — print summary: branch, PR link (if exists), remaining issues

**Failure modes to handle:**
- `make test` fails → fix before proceeding, never skip
- `git push` fails → diagnose (upstream diverged? auth?), resolve, retry
- `bd sync` fails → warn, proceed with manual note
- No changes to commit → skip commit steps, still sync beads and verify

**AGENTS.md trigger:**
```
Use `parchmark-land` when ending any work session, before reporting completion to the user — ensures all work is committed, pushed, and beads are synced.
```

**Smoke test:**
```bash
# Setup: branch with one staged file
git worktree add .worktrees/feat/land-test -b feat/land-test
cd .worktrees/feat/land-test
echo "test" > test.txt && git add test.txt
# Run skill, then assert:
git status | grep "nothing to commit"
git status | grep "up to date with"
# Cleanup
git worktree remove .worktrees/feat/land-test
```

---

## Skill 3: `parchmark-markdown-sync`

**Problem:** `markdown.ts` (frontend) and `markdown.py` (backend) must stay behaviorally in sync. Drift causes notes to render differently on frontend vs API. No automated check exists — bugs are only caught by users.

### Implementation

**File:** `.claude/skills/parchmark-markdown-sync.md`

**Inputs:** None (always checks the two known files)

**Files compared:**
- `ui/src/utils/markdown.ts`
- `backend/app/utils/markdown.py`

**Steps the skill enforces:**
1. **Extract function signatures** from both files
2. **Compare function inventory** — every public function in one must exist in the other
3. **Compare behavioral semantics** for each shared function:
   - `extractTitle` / `extract_title` — same regex/logic?
   - `removeH1` / `remove_h1` — removes FIRST H1 only in both?
   - Any other shared functions
4. **Report drift** — list mismatches with file:line references
5. **Suggest fix** — which file is "correct" (or flag for human decision)

**Failure modes to handle:**
- New function added to one side only → flag as drift
- Logic divergence (e.g., different regex) → flag with both implementations shown
- No drift found → report "in sync", exit

**AGENTS.md trigger:**
```
Use `parchmark-markdown-sync` after modifying any markdown processing logic in either `ui/src/utils/markdown.ts` or `backend/app/utils/markdown.py` — verifies both implementations stay in sync.
```

**Smoke test:**
```bash
# Positive: run on clean repo → "in sync"
# Negative: add a function to markdown.ts, run skill → reports drift
grep -oP 'export function \w+' ui/src/utils/markdown.ts | sort > /tmp/ts_fns
grep -oP 'def \w+' backend/app/utils/markdown.py | sort > /tmp/py_fns
diff /tmp/ts_fns /tmp/py_fns  # empty = pass
```

---

## Execution Order

| Phase | Skill | Rationale |
|-|-|-|
| 1 | `parchmark-branch-setup` | Highest frequency, simplest to implement, immediately useful |
| 2 | `parchmark-land` | Second highest frequency, prevents the most damaging failure mode |
| 3 | `parchmark-markdown-sync` | Lower frequency but unique — no other mechanism catches this class of bug |

## Per-Skill Checklist

For each skill:
1. [ ] Write the skill markdown file in `.claude/skills/`
2. [ ] Add trigger sentence to AGENTS.md
3. [ ] Run smoke test manually
4. [ ] Use the skill on a real task to validate
5. [ ] Iterate on edge cases discovered during real use
