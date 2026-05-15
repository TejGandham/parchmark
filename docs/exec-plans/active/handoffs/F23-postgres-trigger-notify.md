# Postgres trigger emits NOTIFY on note title/content/delete

---
status: IN-PROGRESS
pipeline: backend
spec_ref:
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F23
parent_sha:

intent: build
complexity: standard
designer_needed: YES
researcher_needed: NO
safety_auditor_needed: YES
arch_advisor_needed: NO
implementer_needed: YES

spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict: PASS
safety_attempt: 1
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict:

arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

remote_name: origin
roundtable_enabled: false
roundtable_precheck_skipped: true
roundtable_precheck_skip_reason: Roundtable MCP tools are unavailable in this Codex session.
pr_url:

roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped: true
roundtable_skip_reason: Roundtable MCP tools are unavailable in this Codex session.

roundtable_landing_attempt: 0
roundtable_landing_verdict:

roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0
---

## pre-check

### Execution brief

**Feature:** F23 — Postgres trigger emits NOTIFY on note title/content/delete

**PRD:** docs/exec-plans/prds/realtime-notes-list-revalidation.json#F23

**Pipeline:** backend

**Intent:** build

**Complexity:** standard

**Routing:**
- Designer needed: YES
- Researcher needed: NO
- Safety auditor needed: YES
- Arch-advisor needed: NO
- Implementer needed: YES

**Contract:**
- Trigger table: `notes`
- Trigger events: `INSERT`, `UPDATE`, `DELETE`
- Update columns: `title`, `content`
- Excluded update columns: retired vector-storage fields
- Notify channel: `notes_events`
- Payload fields: `user_id`, `kind`, `note_id`
- Transactional delivery: true
- Migration required: true

**Oracle pointers:**
- `/features/0/oracle/assertions/0` — committed note insert, title/content update, and delete each produce exactly one event on the intended Postgres notification channel.
- `/features/0/oracle/assertions/1` — transaction rollback produces no delivered note-change event.
- `/features/0/oracle/assertions/2` — update outside the declared note-list semantics does not produce client-visible notification noise.

### Constraints for downstream

- MUST implement this through an Alembic migration, not application-layer note router hooks.
- MUST use PostgreSQL `NOTIFY` channel `notes_events` with JSON payload fields `user_id`, `kind`, and `note_id`.
- MUST scope update notifications to `title` and `content` changes only.
- MUST preserve transactional delivery semantics: rolled-back writes must not emit delivered notifications.
- MUST avoid introducing raw SQL outside sanctioned migration/test contexts.

## researcher

### Decisions

- Researcher skipped: the PRD and local Alembic/PostgreSQL patterns are sufficient.

## arch-advisor-consultation

### Constraints for downstream

- Arch-advisor skipped: standard migration-backed backend feature, no architecture-tier decision required.

## backend-designer / frontend-designer

### Decisions

- Implement a new Alembic revision that creates a small `plpgsql` trigger function and attaches it to `notes`.
- Use `pg_notify('notes_events', json_build_object(... )::text)` so future listeners can parse a stable JSON payload.
- Represent event `kind` as `created`, `updated`, and `deleted` for insert, update, and delete respectively.
- Use `OLD` values for delete payloads and `NEW` values for insert/update payloads.
- Use a trigger `WHEN (OLD.title IS DISTINCT FROM NEW.title OR OLD.content IS DISTINCT FROM NEW.content)` for update filtering.

### Constraints for downstream

- MUST make the migration idempotent enough for Alembic upgrade/downgrade in tests.
- MUST drop the trigger and trigger function on downgrade.
- MUST add focused backend migration tests for insert/update/delete, rollback, and ignored updates.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this Codex session.

## test-writer

Added focused integration coverage in `backend/tests/integration/migrations/test_f23_notes_notify_trigger.py`.

Coverage:
- Insert, title update, and delete each emit exactly one `notes_events` payload.
- Rolled-back insert emits no payload.
- `updated_at`-only updates emit no payload.
- `title = title` no-op updates emit no payload.

### Decisions

- Use a dedicated PostgreSQL testcontainer seeded at parent revision `7f1c343772e8`.
- Stamp Alembic at the parent revision and run `upgrade head` so the test exercises only the F23 migration.
- Use a dedicated LISTEN connection and parse notification payloads as JSON.

## implementer

Added Alembic revision `8f4d2b1c9a7e_add_notes_events_notify_trigger.py`.

### Decisions

- Created trigger function `notify_notes_events()` that emits JSON payloads on `notes_events`.
- Created separate triggers for insert/delete and title/content updates.
- Used `AFTER UPDATE OF title, content` plus `IS DISTINCT FROM` to avoid notifications for unrelated or no-op updates.
- Downgrade drops both triggers before dropping the trigger function.

## code-reviewer

**Verdict:** APPROVED

No blocking findings.

Review notes:
- Trigger names and function name are stable and scoped.
- Trigger function uses static migration SQL only; no interpolated user input.
- Tests assert transactional behavior and quiet updates.
- Migration is reversible via downgrade.

## spec-reviewer

**Verdict:** CONFORMANT

Contract conformance:
- `trigger_table: notes` — migration checks and attaches to `notes`.
- `trigger_events: INSERT, UPDATE, DELETE` — insert/delete trigger plus update trigger cover all three.
- `update_columns: title, content` — update trigger is scoped to those columns.
- `notify_channel: notes_events` — trigger function uses `pg_notify('notes_events', ...)`.
- `payload_fields: user_id, kind, note_id` — trigger function emits exactly those fields.
- `transactional_delivery: true` — PostgreSQL NOTIFY is emitted inside the row transaction and tested by rollback coverage.
- `migration_required: true` — implementation is an Alembic revision.

## safety-auditor

**Verdict:** PASS

Safety notes:
- No router or service Note ORM operation changed, so tenant-isolation invariant is not weakened.
- No route/auth surface changed.
- Raw SQL is confined to an Alembic migration and integration tests, matching the pre-check constraint and existing migration-test precedent.
- No secrets, tokens, credentials, or request bodies are logged.

## arch-advisor-verification

Skipped: not architecture-tier.

## landing-verifier

**Verdict:** BLOCKED locally, CI required

Passed locally:
- `cd backend && uv run ruff check .`
- `cd backend && uv run ruff format --check .`
- `cd backend && uv run mypy app`
- `cd backend && uv run alembic heads`
- `cd backend && uv run alembic history -r 7f1c343772e8:head`
- `python3 scripts/validate-prds.py --repo .`
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json`

Blocked locally:
- `cd backend && uv run pytest tests/integration/migrations/test_f23_notes_notify_trigger.py -q`
- `cd backend && uv run pytest tests/unit -q`

Both pytest commands failed at setup because Docker is not available at `/var/run/docker.sock` on this machine. The unit command reached `341 passed` before Docker-backed fixtures errored. Forgejo CI should run these in the supported Docker environment.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this Codex session.
