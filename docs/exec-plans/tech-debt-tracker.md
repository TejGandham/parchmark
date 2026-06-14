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

- [ ] **`test-utils/render` references point to a non-existent module.**
      AGENTS.md (Testing table) and `docs/design-docs/core-beliefs.md`
      (Layer 4, Testing Infrastructure) reference `ui/test-utils/render.tsx`;
      no such file exists. The actual provider-wrapping helpers are
      `TestProvider` / `renderWithProviders` in
      `ui/src/__tests__/__mocks__/testUtils.tsx`. Either create the
      documented helper or fix both doc references.

### Cross-cutting

- [ ] **Markdown parity as a shared test fixture.** Frontend/backend
      markdown utils must produce identical output, but cross-language
      regex equivalence can't be reliably enforced by a static check.
      Follow-up: port the `markdownTestCases` fixture from
      `ui/src/utils/markdown.ts` into a JSON file that both test suites
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
      worth tracking for a future docs cleanup feature: (1) `AGENTS.md:17,140`
      points to non-existent `docs/north-star.md` — actual file is
      `NORTH-STAR.md` at repo root; (2) `docs/BACKEND_MIGRATION_RESEARCH.md:3`
      carries a "Document Created: January 2026" date annotation. Items
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

- [ ] **Automated browser E2E for realtime note updates.** The live-update
      flow now has backend integration coverage, frontend stream-client
      unit coverage, and Forgejo-gated cross-user SSE isolation coverage,
      but ParchMark still has no automated browser E2E suite for the rendered
      notes list. Add Playwright coverage when manual browser verification
      becomes recurring merge-gate work or when rendered-list regressions slip
      past the backend and unit gates.

- [ ] **`renderDateGroups` path lacks virtualization (TD-F17-1).** Surfaced
      by F17 landing review. The non-search render path in
      `NotesExplorer.tsx` (`renderDateGroups`) renders every note as a
      non-windowed React element. Pre-existing — search-only virtualization
      predates the `remove-for-you` PRD — but increasingly load-bearing
      post-F17 since the For You splice no longer sits on top. Threshold
      to act: re-evaluate when avg user note count exceeds ~200, or when
      a slow-render report comes in. Fix: virtualize `renderDateGroups`
      with the same `react-window` pattern used in `renderSearchResults`,
      or paginate. Out of scope for F17's contract.

- [ ] **Deletion-fence regex hardening (TD-F17-2).** Surfaced by F17
      landing review. Both
      `NotesExplorer.f17-deletion.test.tsx` and the F16 sibling
      `CommandPalette.f16-deletion.test.tsx` use raw substring regex
      against file contents (e.g. `/forYou/`). A future innocent
      identifier like `notForYou` would false-trip; comments would
      also match. Fix: tighten to word-boundary patterns
      (`\bforYou\b`) and exclude comments. Retire both fence files
      entirely once F18 lands and the symbols are gone repo-wide
      (the fence is a transient guard, not a durable test).

- [ ] **Search-virtualization branch untested at scale (TD-F17-3).**
      Surfaced by F17 landing review. The
      virtualization gate in `NotesExplorer.tsx` (`filteredNotes.length
      > 50`) is never exercised by the test suite — `sampleNotes`
      contains 5 items, threshold is 50. A future refactor could break
      virtualized search without CI catching. Fix: add a >50-notes
      search test asserting `virtual-notes-list` renders with the
      expected count. Optional polish; not a contract requirement.

- [ ] **Audit future migrations for brownfield-tolerance guards.** F20
      codified the pattern (inspect → `_table_exists` → return early on
      fresh DB) in CLAUDE.md "Migration history conventions". All six
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
