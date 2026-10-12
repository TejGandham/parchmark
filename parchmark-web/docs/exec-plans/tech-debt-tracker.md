# Tech Debt Tracker

Known shortcuts, deferred improvements, and open questions.

<!-- Items get added as features land. Mark resolved items with [x].
     Review this file during garbage collection sweeps. -->

## Pre-Implementation

<!-- Spec drift, open questions discovered before coding starts -->

### Open Questions

- [ ] **Open product decisions (carried from the retired v2 TODO list).**
      These block further wiring work until product decides:

      - Can users edit profile fields? Account details are display-only
        today; settings already covers password change, notes export, and
        account deletion.
      - Does workspace/preference persistence (theme, default view,
        editor/sort defaults surviving across devices) become product
        scope? No backend preference contract exists yet.
      - Is SSO provider management (connect, disconnect, provider switch,
        IdP links) in scope?
      - Does note deletion need a confirmation step?

      Out of scope unless product scope changes: server-generated
      single-note export, server-side note search/tag query params, bulk
      tag management (colors, ordering, cross-note admin, saved views),
      and Mermaid runtime rendering.

## During Implementation

<!-- Shortcuts taken, unexpected issues discovered during feature work -->

- [x] **Re-audit `auth_service.py` coverage after the auth-service
      extraction.** The extraction (`[karta:item-auth-service-extraction]`,
      merged 2026-07-02) moved `refresh_access_token()`'s error branches
      out of `routers/auth.py` into `services/auth_service.py`. Their
      coverage hasn't been re-checked since — needs Docker, since the
      exercising tests are integration-level.

### Cross-cutting

- [ ] **CORS `ALLOWED_ORIGINS` sanity check.** Nothing forbids `*`
      wildcards in production. Add a check once we've confirmed the deploy
      pipeline never sets a wildcard.

## Post-MVP

<!-- Improvements to make after core features land -->

- [ ] **Automated doc-drift sweeps.** Doc-drift checks are run manually
      today; schedule periodic sweeps once the repo grows past ~50
      docs or we catch our second stale cross-reference in review.
- [ ] **Alembic reversibility CI check.** Until we actually feel the pain
      of a broken downgrade, don't invest in this — deferred for this
      reason.

- **DECISION (January 2026): the backend stays Python/FastAPI.** The
  migration research that produced `docs/BACKEND_MIGRATION_RESEARCH.md`
  concluded against a rewrite; the doc is deleted. Revisit only under real
  performance or reliability pressure, not speculation.

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
      live-update flow has integration coverage and Forgejo-gated
      cross-user SSE isolation coverage, but nothing exercises the Vue
      frontend in a real browser — not the notes list, not persisted note
      mutations, not the live note-events stream, even though all three
      now flow through the backend notes API. Add Playwright coverage once
      manual browser verification of the live notes flow becomes
      recurring merge-gate work.

- [ ] **No virtualization for the rendered notes list (Vue rewrite).**
      The legacy React `NotesExplorer` used `react-window` to virtualize
      large lists; the v2 Vue shell renders the notes list in
      `SidebarDrawer.vue` (a plain `v-for` over `NoteCard`s) with no
      windowing. Harmless while per-user note counts stay low, but the
      list is now sourced from the backend and this needs revisiting
      before the app carries real note volumes. Threshold to act:
      re-evaluate past ~200 notes per user, or on the first slow-render
      report.

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
      fresh DB) in CLAUDE.md "Migration history conventions". All nine
      migrations in the current chain follow the pattern (`170dd30cebde`
      had its guard added mid-PR, before merge — commit `4979715` fixed a
      CI failure ("relation notes does not exist" on a fresh vanilla
      `postgres:17` testcontainer) on the F20 branch itself, landing on
      `main` already guarded as part of the same merge; `be7aafff4947` was
      written guarded from the start). Going forward: every new migration MUST
      include the `_table_exists` / column / index inspector guards before
      mutating DDL, so the chain remains replayable on a literally-empty DB
      regardless of the `create_all` vs `alembic-first` boot ordering.
