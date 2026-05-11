@AGENTS.md

## Migration history conventions

Alembic migration history is largely append-only, but a narrow exception
exists for dep-removal hygiene. The boundaries below were established by
F20 (dropping `openai` and `pgvector` from `pyproject.toml`) when removing
load-time imports of an absent package required patching two historical
migration bodies. The carve-out is documented here so future operators do
not mistake it for a general license to retouch migrations.

**Immutable across the project lifetime:**
- `revision`, `down_revision`, `branch_labels`, and `depends_on` identifiers.
- The file's revision filename.
- The *intent* and *direction* of each migration (which columns/tables/
  extensions it adds or removes, and in which direction).

**Patchable only for dep-removal hygiene:**
- Module-level imports and function bodies — provided the generated SQL on
  a *brownfield* database remains semantically equivalent (same columns
  added/dropped, same extension state). The change must be reviewable as
  "removing a load-time dependency on a now-absent package," not "fixing a
  logic bug" or "cosmetic cleanup."

**Required when patching:**
- The migration must be tested against (a) a fresh DB — verifies the body
  returns no-op early when `Base.metadata.create_all` has already produced
  the target schema; and (b) a brownfield DB stamped at the parent revision
  — verifies the body still produces the correct end state.

**Explicit non-goal:**
- This is NOT a green light to retroactively edit migrations for cosmetic
  refactors, `ruff` cleanups, type-hint modernisation, comment rewrites,
  or general tidiness. Dep-removal hygiene is the entire scope.
