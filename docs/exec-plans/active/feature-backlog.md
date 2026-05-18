# Feature Backlog

<!-- KEEL-INVARIANT-7: legacy-through=F00 -->

Smallest independently testable features. Execute top-to-bottom.
Each feature: read spec → write test → write code → verify.

**Specs:** `docs/product-specs/<spec>.md` (one per feature; authored before `/keel-pipeline`)
**PRDs:** `docs/exec-plans/prds/<slug>.md` (one per cohesive feature set; authored via `/keel-refine`)
**Principles:** `docs/design-docs/core-beliefs.md`
**Architecture:** `ARCHITECTURE.md`

<!-- KEEL-BOOTSTRAP: not-applicable -->

---

## Foundation (backend pipeline starts here)

- [x] **F19 Alembic migration drops embedding columns + pgvector extension and updates Note model**
  Needs: F12, F13, F14, F15
  PRD: remove-for-you
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F20 Drop openai and pgvector dependencies from pyproject.toml**
  Needs: F15, F19
  PRD: remove-for-you
  <!-- DRAFTED: 2026-05-09 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

## Service

- [x] **F12 Strip embedding generation from routers/notes.py**
  PRD: remove-for-you
  <!-- DRAFTED: 2026-05-09 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F13 Delete GET /api/notes/{id}/similar endpoint**
  PRD: remove-for-you
  <!-- DRAFTED: 2026-05-09 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F14 Delete POST /api/notes/{id}/access endpoint**
  PRD: remove-for-you

- [x] **F15 Delete embeddings + backfill services and OpenAI lifespan wiring**
  Needs: F12, F13
  PRD: remove-for-you
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F23 Postgres trigger emits NOTIFY on note title/content/delete**
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F24 Per-worker LISTEN consumer plus per-user broker fanout**
  Needs: F23
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F25 Authenticated SSE endpoint /notes/events**
  Needs: F24
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F26 SSE lifecycle heartbeat and disconnect cleanup**
  Needs: F25
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F22 Retire F19 residuals — backend/README.md note-model fields + orphan SimilarNoteResponse schema**
  Needs: F19, F20
  PRD-exempt: trivial
  <!-- DRAFTED: 2026-05-11 by /keel-refine (PRD-exempt); 0 markers remain -->
  <!-- SOURCE: prose:f19-residual-cleanup -->

## UI

- [x] **F16 Strip For You section from CommandPalette.tsx**
  PRD: remove-for-you
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F17 Strip forYouNotes block from NotesExplorer.tsx**
  PRD: remove-for-you
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F18 Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types**
  Needs: F16, F17
  PRD: remove-for-you
  <!-- DRAFTED: 2026-05-09 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F27 Frontend SSE client with bearer auth**
  Needs: F25
  PRD: realtime-notes-list-revalidation
  <!-- DRAFTED: 2026-05-15 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F28 Notes loader revalidation on received events**
  Needs: F27
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F29 Initial-connect and reconnect reconciliation**
  Needs: F27
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F30 SSE auto-reconnect with exponential backoff**
  Needs: F27
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F31 SSE auth-failure refresh and logout handling**
  Needs: F27
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

- [x] **F32 Event stream teardown on logout**
  Needs: F27
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->

## Cross-cutting

- [x] **F21 Documentation sweep: remove embedding / access-tracking references and retire invariants 6 + 7**
  Needs: F19, F20
  PRD: remove-for-you
  <!-- SOURCE: prose:c4f1d9a2e7b8a3f5 -->

- [x] **F33 End-to-end cross-user isolation safety test**
  Needs: F23, F24, F25, F28
  PRD: realtime-notes-list-revalidation
  <!-- SOURCE: prose:1dd071ec29355a67 -->
