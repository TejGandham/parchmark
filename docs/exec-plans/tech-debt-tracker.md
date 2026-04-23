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

- [ ] **Automated browser E2E for live-updates (F07 graduation).** F07
      ships with a hybrid acceptance gate: F07a backend integration
      (pytest + httpx SSE client), F07b frontend unit (Vitest + mocked
      fetch-event-source), F07c manual Chrome DevTools MCP verification
      before merge. Parchmark has no browser E2E suite today. When F07c
      manual-run cost exceeds the tooling investment (likely signalled
      by recurring merge-gate pain or regressions that slipped past
      F07a+F07b), add Playwright and graduate F07c to an automated F07d.
      See `feature-backlog.md` F07 SPEC-NOTES.
