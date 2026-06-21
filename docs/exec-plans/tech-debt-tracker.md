# Tech Debt Tracker

Known shortcuts, deferred improvements, and open questions.

<!-- Items get added as features land. Mark resolved items with [x].
     Review this file during garbage collection sweeps. -->

## Pre-Implementation

<!-- Spec drift, open questions discovered before coding starts -->

### Open Questions

<!-- None currently tracked. Add as they surface during feature pre-checks. -->

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

- [ ] **Auth-provider consistency DB invariant.**
      `User.auth_provider='local'` should imply `password_hash IS NOT NULL`;
      `auth_provider='oidc'` should imply `oidc_sub IS NOT NULL`. Currently
      only the Python-side logic enforces this; adding a CHECK constraint
      would make it DB-level.

- [ ] **CORS `ALLOWED_ORIGINS` sanity check.** Nothing forbids `*`
      wildcards in production. Add a check once we've confirmed the deploy
      pipeline never sets a wildcard.

- [ ] **`Depends(get_async_db)` enforcement.** Prohibit module-level
      `AsyncSession` construction; every session must be request-scoped via
      `Depends`. Current code already honours this but it's un-enforced.

## Post-MVP

<!-- Improvements to make after core features land -->

- [ ] **Automated doc-drift sweeps.** Doc-drift checks are run manually
      today; schedule periodic sweeps once the repo grows past ~50
      docs or we catch our second stale cross-reference in review.
- [ ] **Alembic reversibility CI check.** Until we actually feel the pain
      of a broken downgrade, don't invest in this — deferred for this
      reason.

- [ ] **Pre-existing doc drift surfaced by an F14 post-commit doc sweep.**
      Ad-hoc sweep after F14 commit found drift not caused by F14 but
      worth tracking for a future docs cleanup feature:
      `docs/BACKEND_MIGRATION_RESEARCH.md:3` carries a "Document Created:
      January 2026" date annotation. (The earlier `AGENTS.md` north-star
      cross-reference flagged here is now moot: `AGENTS.md` no longer
      references north-star, and neither `docs/north-star.md` nor a
      repo-root `NORTH-STAR.md` exists anywhere in the tree.) Items
      previously tracked here that are now resolved: (a) ARCHITECTURE.md
      cosine-similarity / `/similar` endpoint references (swept by F20+F21);
      (b) F12/F13 DRAFTED markers (cleaned during retirement); (c)
      `docs/ai-embeddings-design.md` §P5 violations (file archived by F21
      to `docs/design-docs/archive/`; archived content is historical
      by contract).

- [ ] **`docs/deployment_upgrade/archive/` P5 timeline-artifact drift.**
      A doc sweep flagged three §P5 violations during F14:
      `DEPLOYMENT.md` carries a `## Changelog` section with version
      table; `PHASE4_GITHUB_SECRETS.md` and `DEPLOYMENT_VALIDATED.md`
      carry "as of January 2025" annotations in current-state assertions.
      These predate the §P5 invariant and are unrelated to F14's contract,
      so deferring rather than bundling into F14's PR. Sweep when
      touching deployment docs next, or as a dedicated docs cleanup
      feature.

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
      automated browser E2E suite. The notes list is now fetched from the
      backend (`useNotes`/`GET /notes/`), but note mutations remain
      local-only and the SSE stream is unconsumed. Add Playwright coverage
      once manual browser verification of the live list becomes recurring
      merge-gate work.

- [ ] **v2 note mutations are local-only; SSE stream unconsumed.**
      The v2 `ui/src/services/` layer covers auth + the notes list
      (`http.ts`, `auth.ts`, `notes.ts`); `useNotes` fetches `GET /notes/`
      on mount and `AppShell.vue` renders the result with backend-provided
      tags plus `loading`/`error` states. But note mutations
      (create/delete/edit/tag/copy/export) are still local `ref` mutations —
      they do not POST/PUT/DELETE to the backend and do not persist — and the
      backend `GET /api/notes/events` SSE stream is unconsumed. Wiring the
      remaining CRUD/tag mutations and the SSE live-update channel is the
      outstanding integration work.

- [ ] **No virtualization for the rendered notes list (Vue rewrite).**
      The legacy React `NotesExplorer` used `react-window` to virtualize
      large lists; the v2 Vue shell renders notes directly in `AppShell.vue`
      with no windowing. With the list now sourced from the backend this is
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
      fresh DB) in CLAUDE.md "Migration history conventions". All seven
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
