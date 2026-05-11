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

### From `/keel-adopt` (Phase 4 roundtable)

- [ ] **Markdown parity as a shared test fixture.** The proposed Invariant
      #7 ("markdown utils FE/BE must match") was dropped from the grep
      safety-auditor set because cross-language regex equivalence can't be
      reliably grep-enforced. Follow-up: port the `markdownTestCases`
      fixture from `ui/src/utils/markdown.ts` into a JSON file that both
      test suites import, then write a Python test in
      `backend/tests/unit/` that loads it and asserts identical outputs.
      Until then, parity is enforced only by convention + the
      `parchmark-markdown-sync` skill.

- [ ] **Auth-provider consistency DB invariant** (surfaced by Codex in the
      hivemind pass). `User.auth_provider='local'` should imply
      `password_hash IS NOT NULL`; `auth_provider='oidc'` should imply
      `oidc_sub IS NOT NULL`. Currently only the Python-side logic
      enforces this; adding a CHECK constraint would make it DB-level.

- [ ] **CORS `ALLOWED_ORIGINS` sanity check** (Claude, hivemind). No
      invariant rule forbids `*` wildcards in production. Add a
      safety-auditor grep pattern once we've confirmed the deploy
      pipeline never sets a wildcard.

- [ ] **`Depends(get_async_db)` enforcement.** Add an invariant that
      prohibits module-level `AsyncSession` construction; every session
      must be request-scoped via `Depends`. Current code already honours
      this but it's un-gated.

## Post-MVP

<!-- Improvements to make after core features land -->

- [ ] **Automated doc-drift sweeps.** Today `doc-gardener` is invoked
      manually; schedule periodic sweeps once the repo grows past ~50
      docs or we catch our second stale cross-reference in review.
- [ ] **Alembic reversibility CI check.** Until we actually feel the pain
      of a broken downgrade, don't invest in this — but the invariant
      was proposed by Claude in roundtable and deferred for this reason.

- [ ] **Pre-existing doc drift surfaced by F14's post-commit doc-gardener.**
      Ad-hoc sweep after F14 commit found drift not caused by F14 but
      worth tracking for a future docs cleanup feature: (1) `AGENTS.md:17,140`
      points to non-existent `docs/north-star.md` — actual file is
      `NORTH-STAR.md` at repo root; (2) `ARCHITECTURE.md:174,269-281`
      still describes `routers/notes.py` doing "cosine similarity
      queries" and lists the deleted `GET /api/notes/{id}/similar`
      endpoint as active (F13 doc-drift miss); (3) `feature-backlog.md`
      F12 and F13 entries still carry `<!-- DRAFTED: -->` markers that
      should have been removed when those features landed; (4)
      `docs/ai-embeddings-design.md` carries multiple §P5 violations
      (`### Revision History` section, commit SHAs in metadata table
      and migration mermaid diagrams); (5)
      `docs/BACKEND_MIGRATION_RESEARCH.md:3` carries a "Document
      Created: January 2026" date annotation. Items (1) and (4)–(5) are
      pre-F14 drift; item (2) is F13's doc-drift miss; item (3) is
      F12/F13's marker-cleanup miss. Resolution: bundle into a single
      `chore: doc cleanup sweep` feature, or fold into F21's invariant-4
      cleanup since several touch the same retirement narrative.

- [ ] **`docs/deployment_upgrade/archive/` P5 timeline-artifact drift.**
      Doc-gardener flagged three §P5 violations during F14's pipeline:
      `DEPLOYMENT.md` carries a `## Changelog` section with version
      table; `PHASE4_GITHUB_SECRETS.md` and `DEPLOYMENT_VALIDATED.md`
      carry "as of January 2025" annotations in current-state assertions.
      These predate the §P5 invariant and are unrelated to F14's contract,
      so deferring rather than bundling into F14's PR. Sweep when
      touching deployment docs next, or as a dedicated docs cleanup
      feature.

- [ ] **Endpoint-removal test pattern accumulator.** As the `remove-for-you`
      retirement progresses (F12, F13, F14, F15, F19 landed; F20 to come),
      `backend/tests/integration/notes/test_endpoint_removal.py` is
      becoming an accumulator file holding multiple feature class-pairs
      (HTTP-tier + grep-tier + filesystem-tier per removed endpoint).
      Surfaced by roundtable landing review during F14. Tolerable
      through F20; consider parameterized fixtures or a dedicated
      `removed_endpoints/` subdirectory if the pattern continues past
      F20, or retire the grep-tier and filesystem-tier classes entirely
      across F12–F15 in a single follow-up sweep once the retirement is
      complete.

- [ ] **Automated browser E2E for live-updates (F07 graduation).** F07
      ships with a hybrid acceptance gate: F07a backend integration
      (pytest + httpx SSE client), F07b frontend unit (Vitest + mocked
      fetch-event-source), F07c manual Chrome DevTools MCP verification
      before merge. Parchmark has no browser E2E suite today. When F07c
      manual-run cost exceeds the tooling investment (likely signalled
      by recurring merge-gate pain or regressions that slipped past
      F07a+F07b), add Playwright and graduate F07c to an automated F07d.
      See `feature-backlog.md` F07 SPEC-NOTES.

- [ ] **`renderDateGroups` path lacks virtualization (TD-F17-1).** Surfaced
      by F17 roundtable landing review. The non-search render path in
      `NotesExplorer.tsx` (`renderDateGroups`) renders every note as a
      non-windowed React element. Pre-existing — search-only virtualization
      predates the `remove-for-you` PRD — but increasingly load-bearing
      post-F17 since the For You splice no longer sits on top. Threshold
      to act: re-evaluate when avg user note count exceeds ~200, or when
      a slow-render report comes in. Fix: virtualize `renderDateGroups`
      with the same `react-window` pattern used in `renderSearchResults`,
      or paginate. Out of scope for F17's contract.

- [ ] **Deletion-fence regex hardening (TD-F17-2).** Surfaced by F17
      roundtable landing review (Claude + Codex). Both
      `NotesExplorer.f17-deletion.test.tsx` and the F16 sibling
      `CommandPalette.f16-deletion.test.tsx` use raw substring regex
      against file contents (e.g. `/forYou/`). A future innocent
      identifier like `notForYou` would false-trip; comments would
      also match. Fix: tighten to word-boundary patterns
      (`\bforYou\b`) and exclude comments. Retire both fence files
      entirely once F18 lands and the symbols are gone repo-wide
      (the fence is a transient guard, not a durable test).

- [ ] **Search-virtualization branch untested at scale (TD-F17-3).**
      Surfaced by F17 roundtable landing review (Codex). The
      virtualization gate in `NotesExplorer.tsx` (`filteredNotes.length
      > 50`) is never exercised by the test suite — `sampleNotes`
      contains 5 items, threshold is 50. A future refactor could break
      virtualized search without CI catching. Fix: add a >50-notes
      search test asserting `virtual-notes-list` renders with the
      expected count. Optional polish; not a contract requirement.

- [ ] **`/keel-refine` consumer-path enumeration template for removal-features.**
      Four consecutive removal pipelines required mid-flight PRD amendments
      because the drafter under-enumerated consumer paths at refine time:
      F15 (PR #82, `test_backfill.py` import in deleted-target),
      F19 (PR #85, router/schema/test consumer paths to dropped columns),
      F20 (paused; migration-history pgvector imports + 4 compose files
      + conftest image swap),
      F16+F17 (PR #87, `SimilarNote` import + test-file scope + orphan
      `section.forYou` semantic token).
      Pattern: each removal feature's PRD lists the primary deletion target
      but misses transitive consumers (test files, type imports, style
      tokens, lockfile/dep ripples, infra image references).
      Roundtable across all four pipelines independently flagged the same
      diagnosis — recommendation: extend `/keel-refine` with a removal-
      feature checklist that walks the drafter through (a) render path,
      (b) service exports + dependency graph, (c) utility consumers,
      (d) type/config constants, (e) theme/style tokens, (f) test mocks
      + shared setup files, (g) infra (compose, dockerfile, lockfile),
      (h) doc surfaces. Per-removal one-time drafter cost; collapses
      multiple amendment-PR cycles into one refine pass. The KEEL
      framework is "a customization point, not a cage" (KEEL-CONTRACT)
      — this is the framework upgrade the data is asking for.

- [ ] **F19-residual: `backend/README.md` Note model fields drift.**
      Lines ~263-265 still describe `access_count`, `last_accessed_at`,
      and `embedding` Note model fields. F19's migration dropped these
      columns but the README cleanup wasn't bundled. Surfaced by F18
      roundtable landing review + doc-gardener Step 9 sweep
      (deferred from F18 scope as backend-side debt).

- [ ] **F19-residual: orphan `SimilarNoteResponse` Pydantic class.**
      `backend/app/schemas/schemas.py:88` still defines
      `SimilarNoteResponse` for the deleted `GET /api/notes/{id}/similar`
      endpoint (F13). The class has zero consumers post-F13.
      Surfaced by F18 roundtable landing review + doc-gardener Step 9
      sweep (deferred from F18 scope as backend-side debt).

- [ ] **Audit future migrations for brownfield-tolerance guards.** F20's
      arch-advisor consultation codified the pattern (inspect →
      `_table_exists` → return early on fresh DB) in CLAUDE.md
      "Migration history conventions". All six migrations in the current
      chain follow the pattern (`170dd30cebde` was retrofitted in F20's
      post-merge-fix-1 after CI surfaced the gap on fresh vanilla-postgres
      containers). Going forward: every new migration MUST include the
      `_table_exists` / column / index inspector guards before mutating
      DDL, so the chain remains replayable on a literally-empty DB
      regardless of the `create_all` vs `alembic-first` boot ordering.
      Optionally: tighten F20 oracle assertion 5's regex from
      `from pgvector|Vector\(` to `from pgvector\.|Vector\(` so
      historical prose mentioning "pgvector" doesn't force migration-body
      cosmetic edits to clear the grep (raised by arch-advisor VERIFY
      future-considerations).
