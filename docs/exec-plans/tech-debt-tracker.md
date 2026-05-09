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
      retirement progresses (F12, F13, F14 landed; F15, F19, F20 to come),
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
