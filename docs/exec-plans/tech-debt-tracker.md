# Tech Debt Tracker

Known shortcuts, deferred improvements, and open questions.

<!-- Items get added as features land. Mark resolved items with [x].
     Review this file during garbage collection sweeps. -->

## Pre-Implementation

<!-- Spec drift, open questions discovered before coding starts -->

### Open Questions

- [ ] **Open product decisions (carried from the retired v2 TODO list).**
      Unresolved scope questions that block further wiring work until product
      decides: whether users may edit profile fields (account details are
      display-only today; settings already supports password change, notes
      export, and account deletion); whether workspace/preferences persistence
      (theme, default view,
      editor/sort defaults surviving across devices) becomes product scope —
      no backend preference contract exists; whether SSO provider management
      (connect / disconnect / provider switch / IdP links) is in scope;
      whether note deletion needs a confirmation step. Out of scope unless
      product scope changes: server-generated single-note export, server-side
      note search / tag query params, bulk tag management (colors, ordering,
      cross-note admin, saved views), Mermaid runtime rendering.

## During Implementation

<!-- Shortcuts taken, unexpected issues discovered during feature work -->

- [x] **RESOLVED — Root `AGENTS.md` now describes the v2 Vue stack.** The
      committed repo-root `AGENTS.md` previously named React 18 + Chakra UI
      v2 + Zustand + React Router + React Testing Library (plus a
      `ui/test-utils/render.tsx` helper and a `ui/src/__tests__/` tree).
      None of that existed in the `parchmark-v2` `ui/` — this is a
      ground-up **Vue 3 + Vite + TypeScript** rewrite using `<script setup>`
      SFCs, composable singletons for state (no Pinia/Vuex), a manual
      `App.vue` auth gate for view switching (no Vue Router), and
      `@vue/test-utils` + Vitest for tests (no React Testing Library, no
      provider-wrapping render helper). Test placement is **mixed**: 6
      co-located `*.test.ts` under `ui/src/` plus 11 under `__tests__/`
      directories (not uniformly co-located next to components/source).
      `AGENTS.md` has since been corrected to this Vue 3 reality — its
      stack table and testing table now read Vue 3 + `@vue/test-utils`.
      Remaining `docs/design-docs/` reconciliation, if any, is tracked
      separately.

- [x] **RESOLVED — `pytest.ini` `[tool:pytest]` header shadowed the real
      pytest config.** Surfaced during the drop-sync-session delivery
      (PR #134); fixed in PR #135. `backend/pytest.ini` used a
      `[tool:pytest]` section header — valid only in `setup.cfg`, not
      `pytest.ini` (which needs `[pytest]`) — so pytest selected
      `pytest.ini` as its config file, found no recognised section, ran
      with empty config, and silently shadowed the complete, identical
      `pyproject.toml [tool.pytest.ini_options]`. Effect: the
      `--cov-fail-under=90` gate, `-n auto` xdist, `--strict-markers` /
      `--strict-config`, and `asyncio_mode=auto` never applied (61
      unknown-mark warnings per run; the coverage gate was not enforced at
      all). Fixed by deleting `pytest.ini` so `pyproject.toml` — the
      project's single tool-config source (ruff, mypy, coverage, hatch all
      live there) — governs pytest.

- [x] **RESOLVED — coverage under-reported ~3 points (no thread/greenlet
      tracing).** Once the coverage gate was actually live (see the
      `pytest.ini` item above), the reported 90.89% was a measurement
      artifact: `[tool.coverage.run]` had no `concurrency` setting, so
      coverage.py did not trace async handlers running in FastAPI
      `TestClient`'s portal **thread** or DB code in SQLAlchemy's async
      **greenlets**. Those lines were exercised by passing tests all
      along — not a test gap. Fixed in PR #136 by adding
      `concurrency = ["thread", "greenlet"]`: TOTAL 90.89% → 96.22%,
      `app/routers/auth.py` 64% → 96%. pytest-cov already combines
      correctly under xdist, so no `parallel` / `sigterm` was needed.

- [x] **RESOLVED — OIDC dependency branches untested.** After the
      concurrency fix, `app/auth/dependencies.py` was the one genuine
      coverage gap (~71%). Added `TestOIDCBranchCoverage` (PR #136)
      covering missing-`sub` → 401, the userinfo-endpoint fallback
      (success / fetch-raises / empty), OIDC user auto-creation,
      race-condition `IntegrityError` rollback + re-fetch recovery, and the
      validation exception handlers → 97.65%. Residual uncovered lines are
      intentional and minor: `app/auth/dependencies.py:155-159` (a
      defensive "should not happen" `else`, unreachable) and
      `app/routers/auth.py:107,112` (refresh-token error branches) — left
      as-is rather than contorted to hit.

### Cross-cutting

- [ ] **Markdown parity as a shared test fixture.** Frontend and backend
      markdown handling must stay aligned (title extraction / leading-H1
      stripping), but cross-language equivalence can't be reliably enforced
      by a static check. The v2 frontend renderer lives in
      `ui/src/features/notes/markdownRender.ts` (`marked` + `dompurify`),
      with title/H1 helpers in
      `ui/src/features/notes/noteMockHelpers.ts`; the backend counterpart
      is `backend/app/utils/markdown.py`. Follow-up: extract a shared
      fixture of title/strip cases into a JSON file that both test suites
      import, then write a Python test in `backend/tests/unit/` that loads
      it and asserts identical outputs. Until then, parity is enforced only
      by convention + the `parchmark-markdown-sync` skill.

- [ ] **Auth-provider consistency DB invariant — migration missing for
      brownfield DBs.** `User.auth_provider='local'` should imply
      `password_hash IS NOT NULL`; `auth_provider='oidc'` should imply
      `oidc_sub IS NOT NULL`. A `valid_auth_credentials` CHECK constraint
      already exists on the model (`backend/app/models/models.py`), so any
      `create_all`-built DB enforces it DB-level. What's missing is an
      Alembic migration backfilling the constraint onto brownfield databases
      migrated before it existed — no file under
      `backend/migrations/versions/` references it.

- [ ] **CORS `ALLOWED_ORIGINS` sanity check.** Nothing forbids `*`
      wildcards in production. Add a check once we've confirmed the deploy
      pipeline never sets a wildcard.

- [ ] **`Depends(get_async_db)` enforcement.** Prohibit module-level
      `AsyncSession` construction; every session must be request-scoped via
      `Depends`. Current code already honours this but it's un-enforced.

- [ ] **`make test-ui-oidc` is broken.** `makefiles/ui.mk` still targets
      React-era `src/__tests__/**/*.tsx` files that were deleted in the Vue
      rewrite, so the target can never pass. Remove or repoint it.

- [x] **RESOLVED — DeprecationWarnings triaged and the filter narrowed
      (PR #138).** The blanket `filterwarnings = ["ignore::UserWarning",
      "ignore::DeprecationWarning"]` became live only when the pytest
      config actually started applying (the `pytest.ini` shadowing fix,
      PR #135) and could have masked upcoming deprecations. Triage (the
      suite re-run with the ignores overridden) found only **one
      actionable** DeprecationWarning — our own `test_login_invalid_json`
      posting httpx `data=<str>` (deprecated in favour of `content=`) —
      plus two transitive uvicorn/`websockets` ones (`websockets.legacy` /
      `WebSocketServerProtocol`, deprecated in websockets 14.0; not our
      code, the app uses SSE). Fixed the httpx call and replaced the
      blanket ignore with `default::DeprecationWarning` (so future in-code
      deprecations surface in the test summary) plus targeted `ignore:`
      filters for only the two transitive websockets messages.
      `ignore::UserWarning` stays — its lone case is PyJWT's
      `InsecureKeyLengthWarning` from tests that deliberately sign with
      short HMAC keys.

## Post-MVP

<!-- Improvements to make after core features land -->

- [ ] **Automated doc-drift sweeps.** Doc-drift checks are run manually
      today; schedule periodic sweeps once the repo grows past ~50
      docs or we catch our second stale cross-reference in review.
- [ ] **Alembic reversibility CI check.** Until we actually feel the pain
      of a broken downgrade, don't invest in this — deferred for this
      reason.

- [x] **RESOLVED — pre-existing doc drift surfaced by an F14 post-commit
      doc sweep.** The last outstanding sub-item — the "Document Created:
      January 2026" annotation in `docs/BACKEND_MIGRATION_RESEARCH.md` —
      was closed by the docs-accuracy overhaul deleting that file outright.
      Earlier sub-items were already resolved: ARCHITECTURE.md
      cosine-similarity / `/similar` references (swept by F20+F21), F12/F13
      DRAFTED markers (cleaned during retirement),
      `docs/ai-embeddings-design.md` §P5 violations (archived by F21, then
      the archive itself deleted by the docs overhaul), and the moot
      north-star cross-reference.

- **DECISION (January 2026): the backend stays Python/FastAPI.** The
  migration research that produced `docs/BACKEND_MIGRATION_RESEARCH.md`
  concluded against a rewrite; the doc is deleted. Revisit only under real
  performance or reliability pressure, not speculation.

- [x] **RESOLVED — `docs/deployment_upgrade/archive/` P5 timeline-artifact
      drift.** The flagged files (`DEPLOYMENT.md`'s changelog table,
      `PHASE4_GITHUB_SECRETS.md` / `DEPLOYMENT_VALIDATED.md` "as of January
      2025" annotations) were deleted wholesale by the docs-accuracy
      overhaul along with the rest of `docs/deployment_upgrade/`; nothing
      left to sweep.

- [ ] **Endpoint-removal test pattern accumulator.** With the
      `remove-for-you` retirement complete (F12-F22 landed),
      `backend/tests/integration/notes/test_endpoint_removal.py` is an
      accumulator file holding multiple feature class-pairs (HTTP-tier
      + grep-tier + filesystem-tier per removed endpoint). Surfaced by
      landing review during F14. Consider parameterized
      fixtures or a dedicated `removed_endpoints/` subdirectory if the
      pattern recurs in future retirements, or retire the grep-tier and
      filesystem-tier classes entirely across F12–F15 in a single
      follow-up sweep now that the retirement is complete.

- [ ] **Automated browser E2E for the Vue frontend.** The backend
      live-update flow still has integration coverage and Forgejo-gated
      cross-user SSE isolation coverage, but the v2 Vue frontend has no
      automated browser E2E suite. The notes list, persisted note
      mutations, and the live note-events stream now flow through the backend
      notes API, but none of that flow is exercised by an automated browser
      suite. Add Playwright coverage once manual browser verification of the
      live notes flow becomes recurring merge-gate work.

- [x] **RESOLVED — SSE stream now consumed for live refresh.**
      The v2 `ui/src/services/` layer covers auth and notes CRUD
      (`http.ts`, `auth.ts`, `notes.ts`); `useNotes` fetches `GET /notes/`
      on mount and wraps `POST`, `PUT`, and `DELETE` mutations with
      `creating`/`updating`/`deletingId`/`mutationError` state. `AppShell.vue`
      persists create, edit, delete, and tag add/remove. The backend
      `GET /api/notes/events` SSE stream is now consumed: `services/noteEvents.ts`
      and `features/notes/useNoteEvents.ts` open the authenticated stream over
      `http.ts`'s `requestStream`, and `AppShell.vue` debounces a
      `useNotes().scheduleRefetch()` on each change event to reconcile the list.

- [ ] **No virtualization for the rendered notes list (Vue rewrite).**
      The legacy React `NotesExplorer` used `react-window` to virtualize
      large lists; the v2 Vue shell renders the notes list in
      `SidebarDrawer.vue` (a plain `v-for` over `NoteCard`s) with no
      windowing. With the list now sourced from the backend this is
      only harmless at low per-user note counts; it must be revisited before
      the app is wired to real per-user note volumes. Threshold to act:
      re-evaluate when avg user note count exceeds ~200, or when a
      slow-render report comes in.

- [ ] **Superseded React frontend tech debt (`remove-for-you` / F16–F17).**
      The earlier `NotesExplorer.tsx` / `CommandPalette` deletion-fence
      items (TD-F17-1/2/3, the `forYou` substring fences, and the
      search-virtualization-at-scale gap) were all tied to the retired
      React app and the `remove-for-you` PRD. None of those files or
      symbols exist in the Vue rewrite (verified: no `forYou`,
      `NotesExplorer`, `CommandPalette`, `react-window`, or `*.test.tsx`
      under `ui/`). Recorded here only so the historical references aren't
      mistaken for live debt — nothing to action against the v2 tree.

- [ ] **Audit future migrations for brownfield-tolerance guards.** F20
      codified the pattern (inspect → `_table_exists` → return early on
      fresh DB) in CLAUDE.md "Migration history conventions". All eight
      migrations in the current chain follow the pattern (`170dd30cebde`
      was retrofitted in F20's post-merge-fix-1 after CI surfaced the gap
      on fresh vanilla-postgres containers). Going forward: every new
      migration MUST include the `_table_exists` / column / index inspector
      guards before mutating DDL, so the chain remains replayable on a
      literally-empty DB regardless of the `create_all` vs `alembic-first`
      boot ordering. Optionally: tighten F20's pgvector grep assertion from
      `from pgvector|Vector\(` to `from pgvector\.|Vector\(` so historical
      prose mentioning "pgvector" doesn't force migration-body cosmetic
      edits to clear the grep.
