# Service Layer Migration: Fix Dual-Session Inconsistency

## TL;DR

> **Quick Summary**: Complete the service layer migration by removing all `Depends(get_async_db)` from settings.py and dependencies.py, creating SettingsService, and extending AuthService with OIDC user creation.
> 
> **Deliverables**:
> - New `backend/app/services/settings_service.py`
> - Extended `backend/app/services/auth_service.py` with OIDC methods
> - Migrated `backend/app/routers/settings.py` (remove 4 db dependencies)
> - Migrated `backend/app/auth/dependencies.py` (remove 1 db dependency)
> - Updated `backend/app/services/__init__.py` exports
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: NO - sequential (each task depends on previous)
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5

---

## Context

### Original Request
Complete the service layer migration by fixing dual-session inconsistency in PR #8. Two files still use the old `Depends(get_async_db)` pattern, causing dual-session scenarios.

### Interview Summary
**Key Discussions**:
- User chose to create `SettingsService` for consistency with existing NoteService/AuthService pattern
- User chose to move OIDC user creation to `AuthService` (consolidates user operations)

**Research Findings**:
- Exactly 5 usages: 4 in settings.py, 1 in dependencies.py
- No circular import risk (services don't import from dependencies.py)
- Tests patch `AsyncSessionLocal` in middleware - will work automatically
- 595 tests must pass

### Metis Review
**Identified Gaps** (addressed):
- Circular import risk: VALIDATED - no services import from dependencies.py
- IntegrityError pattern: PRESERVED - rollback-retry stays as explicit db.rollback()
- Incremental migration: ADOPTED - each task verified before proceeding
- Acceptance criteria: ADDED - explicit grep checks, test runs, type checks

---

## Work Objectives

### Core Objective
Eliminate dual-session inconsistency by migrating all remaining `Depends(get_async_db)` usages to the ContextVar-based `get_db()` pattern via service layer.

### Concrete Deliverables
- `backend/app/services/settings_service.py` (new file)
- `backend/app/services/auth_service.py` (extended with OIDC methods)
- `backend/app/routers/settings.py` (migrated)
- `backend/app/auth/dependencies.py` (migrated)
- `backend/app/services/__init__.py` (updated exports)

### Definition of Done
- [ ] `rg 'Depends\(get_async_db\)' backend/app/` returns ZERO matches
- [ ] `rg 'from.*get_async_db' backend/app/` returns ZERO matches (except database.py definition)
- [ ] `pytest` passes with 595 tests
- [ ] `mypy app/` passes with exit code 0
- [ ] `ruff check app/` passes with exit code 0
- [ ] App starts without import errors

### Must Have
- SettingsService follows exact same singleton pattern as NoteService
- AuthService OIDC methods handle IntegrityError rollback-retry pattern
- All routes maintain identical API contract (same params, responses, status codes)
- No test modifications (tests should pass via middleware patching)

### Must NOT Have (Guardrails)
- DO NOT change route response shapes or status codes
- DO NOT modify DBSessionMiddleware
- DO NOT modify test files
- DO NOT "improve" or refactor code while migrating
- DO NOT add new functionality - extract exactly as-is
- DO NOT consolidate similar routes - each migrates independently
- DO NOT change error handling patterns - keep exact try/except
- DO NOT add type hints that weren't there (unless mypy requires)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: YES (pytest, 595 tests)
- **Automated tests**: Tests-after (existing tests, no new tests needed for this refactor)
- **Framework**: pytest

### Verification Commands
```bash
# After EACH task:
cd backend && source .venv/bin/activate

# 1. Tests pass
pytest -x -q

# 2. Type check passes  
mypy app/

# 3. Lint passes
ruff check app/

# 4. App starts
timeout 10 python -c "from app.main import app; print('OK')"
```

---

## Execution Strategy

### Sequential Execution (No Parallelization)

Each task builds on the previous. Must execute in order with verification between each.

```
Task 1: Create SettingsService (no dependencies)
    ↓ verify tests pass
Task 2: Migrate settings.py routes (depends: Task 1)
    ↓ verify tests pass  
Task 3: Extend AuthService with OIDC methods (no dependencies on 1-2)
    ↓ verify tests pass
Task 4: Migrate dependencies.py (depends: Task 3)
    ↓ verify tests pass
Task 5: Final cleanup and exports update (depends: Task 2, 4)
    ↓ verify all criteria
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize |
|------|------------|--------|-----------------|
| 1 | None | 2 | No |
| 2 | 1 | 5 | No |
| 3 | None | 4 | Could with 1-2, but sequential safer |
| 4 | 3 | 5 | No |
| 5 | 2, 4 | None | No |

---

## TODOs

### - [ ] 1. Create SettingsService

**What to do**:
- Create `backend/app/services/settings_service.py`
- Define `SettingsService` class following NoteService singleton pattern
- Add methods:
  - `get_user_note_count(user_id: int) -> int` - counts notes for user
  - `change_user_password(user: User, current_password: str, new_password: str) -> None` - validates and updates password
  - `collect_notes_for_export(user_id: int) -> tuple[list[tuple[str, str]], list[dict]]` - collects notes data for export
  - `delete_user_account(user: User) -> str` - deletes user, returns username
- Each method uses `get_db()` from context, NOT a db parameter
- Use `db.flush()` after mutations, NOT `db.commit()`
- Define custom exceptions: `PasswordChangeError`, `AccountDeletionError`

**Must NOT do**:
- Add functionality not in original routes
- Change validation logic - extract exactly as-is
- Add type hints beyond what mypy requires

**Recommended Agent Profile**:
- **Category**: `quick`
  - Reason: Single file creation following established patterns
- **Skills**: [`git-master`]
  - `git-master`: For atomic commit after task completion

**Parallelization**:
- **Can Run In Parallel**: NO
- **Parallel Group**: Sequential
- **Blocks**: Task 2
- **Blocked By**: None

**References** (CRITICAL):

**Pattern References** (existing code to follow):
- `backend/app/services/note_service.py:55-65` - Service class docstring and singleton pattern
- `backend/app/services/note_service.py:102-104` - `get_db()` usage pattern
- `backend/app/services/note_service.py:154-160` - `db.flush()` after mutation with try/except
- `backend/app/services/note_service.py:229-230` - Singleton instance export pattern
- `backend/app/services/auth_service.py:31-42` - Custom exception classes pattern

**Source References** (code to extract):
- `backend/app/routers/settings.py:54-55` - Note count query to extract
- `backend/app/routers/settings.py:91-114` - Password change validation logic to extract
- `backend/app/routers/settings.py:144-184` - `_collect_notes_for_export` function to move
- `backend/app/routers/settings.py:286-306` - Delete account logic to extract

**API References**:
- `backend/app/database/context.py:25-41` - `get_db()` function signature and usage

**Acceptance Criteria**:

- [ ] File created: `backend/app/services/settings_service.py`
- [ ] SettingsService class defined with singleton pattern
- [ ] All 4 methods implemented
- [ ] `rg 'get_db\(\)' backend/app/services/settings_service.py` returns matches
- [ ] `rg 'flush\(\)' backend/app/services/settings_service.py` returns matches
- [ ] `rg 'commit\(\)' backend/app/services/settings_service.py` returns NO matches

**Agent-Executed QA Scenarios**:

```
Scenario: Settings service file structure is correct
  Tool: Bash
  Steps:
    1. rg -c 'class SettingsService' backend/app/services/settings_service.py
    2. Assert: Returns "1"
    3. rg -c 'settings_service = SettingsService\(\)' backend/app/services/settings_service.py
    4. Assert: Returns "1"
  Expected Result: Service follows singleton pattern

Scenario: Service uses flush not commit
  Tool: Bash
  Steps:
    1. rg 'await db\.commit\(\)' backend/app/services/settings_service.py || echo "NO_COMMIT"
    2. Assert: Output is "NO_COMMIT"
  Expected Result: No commit calls

Scenario: Module imports successfully
  Tool: Bash
  Steps:
    1. cd backend && source .venv/bin/activate
    2. python -c "from app.services.settings_service import SettingsService, settings_service; print('OK')"
  Expected Result: Clean import
```

**Commit**: YES
- Message: `refactor(services): add SettingsService for user settings operations`
- Files: `backend/app/services/settings_service.py`

---

### - [ ] 2. Migrate settings.py Routes to SettingsService

**What to do**:
- Update `backend/app/routers/settings.py` to use SettingsService
- Remove `Depends(get_async_db)` from all 4 routes (lines 39, 70, 217, 261)
- Remove `db: AsyncSession` parameter from each route
- Remove `from app.database.database import get_async_db` import
- Remove `from sqlalchemy.ext.asyncio import AsyncSession` import
- Add `from app.services.settings_service import settings_service`
- Replace inline DB operations with SettingsService method calls
- Remove explicit `await db.commit()` calls (lines 114, 306)
- Delete helper function `_collect_notes_for_export` (lines 144-184)

**Must NOT do**:
- Change route paths, methods, or response models
- Change HTTPException status codes or details
- Modify `_sanitize_filename` or `_generate_zip_entries` (pure functions)

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: [`git-master`]

**Parallelization**:
- **Blocks**: Task 5
- **Blocked By**: Task 1

**References**:
- `backend/app/routers/notes.py:1-50` - Router using service pattern
- `backend/app/routers/settings.py` - File to modify

**Acceptance Criteria**:
- [ ] `rg 'Depends\(get_async_db\)' backend/app/routers/settings.py` returns NO matches
- [ ] `rg 'await db\.commit\(\)' backend/app/routers/settings.py` returns NO matches
- [ ] `pytest tests/test_settings.py -v` passes

**Commit**: YES
- Message: `refactor(routes): migrate settings routes to SettingsService`
- Files: `backend/app/routers/settings.py`

---

### - [ ] 3. Extend AuthService with OIDC User Creation

**What to do**:
- Extend `backend/app/services/auth_service.py` with OIDC methods
- Add methods:
  - `get_user_by_oidc_sub(oidc_sub: str) -> User | None`
  - `create_oidc_user(user_info: dict) -> User` - uses `db.flush()` + `db.refresh()`
- Use `get_db()` from context, `db.flush()` not `db.commit()`

**Must NOT do**:
- Change the IntegrityError rollback-retry semantics
- Modify existing AuthService methods

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: [`git-master`]

**Parallelization**:
- **Blocks**: Task 4
- **Blocked By**: None

**References**:
- `backend/app/services/auth_service.py:73-85` - Existing query pattern
- `backend/app/auth/dependencies.py:35-53` - Code to move

**Acceptance Criteria**:
- [ ] `rg 'async def get_user_by_oidc_sub' backend/app/services/auth_service.py` returns match
- [ ] `rg 'async def create_oidc_user' backend/app/services/auth_service.py` returns match
- [ ] `rg 'await db\.commit\(\)' backend/app/services/auth_service.py` returns NO matches
- [ ] `pytest tests/test_auth.py -v` passes

**Commit**: YES
- Message: `refactor(services): add OIDC user methods to AuthService`
- Files: `backend/app/services/auth_service.py`

---

### - [ ] 4. Migrate dependencies.py to Use AuthService

**What to do**:
- Update `backend/app/auth/dependencies.py` to use AuthService
- Remove `Depends(get_async_db)` from `get_current_user` (line 58)
- Remove `db: AsyncSession` parameter
- Remove `from app.database.database import get_async_db` import
- Add `from app.services.auth_service import auth_service`
- Add `from app.database.context import get_db`
- Replace helper calls with auth_service methods
- Delete private helper functions (lines 29-53)
- **PRESERVE IntegrityError handling**: Update rollback to `await get_db().rollback()`

**Must NOT do**:
- Change the IntegrityError retry logic flow
- Modify other helper functions in the file

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: [`git-master`]

**Parallelization**:
- **Blocks**: Task 5
- **Blocked By**: Task 3

**References**:
- `backend/app/services/auth_service.py` - Service to use
- `backend/app/auth/dependencies.py` - File to modify
- `backend/app/database/context.py:25-41` - get_db() for rollback

**Acceptance Criteria**:
- [ ] `rg 'Depends\(get_async_db\)' backend/app/auth/dependencies.py` returns NO matches
- [ ] `rg 'await get_db\(\)\.rollback\(\)' backend/app/auth/dependencies.py` returns match
- [ ] `rg 'def _query_user' backend/app/auth/dependencies.py` returns NO matches
- [ ] Full test suite passes: `pytest -x -q`

**Commit**: YES
- Message: `refactor(auth): migrate get_current_user to use AuthService`
- Files: `backend/app/auth/dependencies.py`

---

### - [ ] 5. Final Cleanup and Export Updates

**What to do**:
- Update `backend/app/services/__init__.py` to export SettingsService
- Add imports and update `__all__` list
- Run final verification of all acceptance criteria

**Recommended Agent Profile**:
- **Category**: `quick`
- **Skills**: [`git-master`]

**Parallelization**:
- **Blocked By**: Task 2, Task 4

**References**:
- `backend/app/services/__init__.py:15-51` - Current export pattern

**Acceptance Criteria**:
- [ ] `rg 'SettingsService' backend/app/services/__init__.py` in `__all__`
- [ ] `rg 'Depends\(get_async_db\)' backend/app/` returns ZERO matches
- [ ] `pytest` - 595 tests pass
- [ ] `mypy app/` passes
- [ ] `ruff check app/` passes
- [ ] `python -c "from app.main import app; print('OK')"` prints OK

**Commit**: YES
- Message: `refactor(services): complete service layer migration, update exports`
- Files: `backend/app/services/__init__.py`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `refactor(services): add SettingsService` | `settings_service.py` | mypy, ruff |
| 2 | `refactor(routes): migrate settings routes` | `settings.py` | test_settings.py |
| 3 | `refactor(services): add OIDC methods` | `auth_service.py` | test_auth.py |
| 4 | `refactor(auth): migrate get_current_user` | `dependencies.py` | full pytest |
| 5 | `refactor(services): complete migration` | `__init__.py` | all criteria |

---

## Success Criteria

### Verification Commands
```bash
cd backend && source .venv/bin/activate

# Zero legacy patterns
rg 'Depends\(get_async_db\)' app/
# Expected: No matches

# Tests pass
pytest
# Expected: 595 passed

# Type check
mypy app/
# Expected: Success

# Lint
ruff check app/
# Expected: No errors

# App starts
python -c "from app.main import app; print('OK')"
# Expected: OK
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All 595 tests pass
- [ ] mypy clean
- [ ] ruff clean
- [ ] App starts without import errors
