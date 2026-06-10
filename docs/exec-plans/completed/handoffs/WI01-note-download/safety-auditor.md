## Safety Audit: Read-view note download button (markdown export)

**Verdict:** PASS

**Binder:** C:\Users\Developer\src\parchmark\.keel\worktrees\WI01-note-download\docs\exec-plans\binders\note-download.json
**Feature ID:** WI01
**Files scanned:**
- ui/src/features/notes/utils/noteDownload.ts (new)
- ui/src/features/notes/components/NoteActions.tsx (modified)
- ui/src/features/notes/components/NoteContent.tsx (modified)
- ui/src/__tests__/features/notes/components/NoteDownload.test.tsx (new)
- git status/diff sweep of the full worktree to confirm scan scope is complete

**Invariant registry:** the seven configured domain invariants in
`docs/design-docs/core-beliefs.md` §"Domain Safety — The Seven Invariants"
(named by the project guide as the rules this gate enforces). Note: the
framework agent-master template's inline CUSTOMIZE block is not populated;
the project's invariants are configured in the core-beliefs registry, so the
audit ran against those seven — this is template/registry drift, not an
unconfigured-invariants condition, and is recorded for the tech-debt log.

**Per-invariant disposition:**
- #1 Tenant isolation (Note ORM in `backend/app/{routers,services}/**`) — NOT TOUCHED: diff contains zero backend files (`git diff --stat`: NoteActions.tsx, NoteContent.tsx; new files all under `ui/`). No ORM statement added or modified.
- #2 Auth on every non-public route (`backend/app/routers/**`) — NOT TOUCHED: no route added/changed; feature is pure client-side by contract and by diff (no fetch, no endpoint).
- #3 No raw SQL outside the whitelisted probe — NOT TOUCHED: no SQL anywhere in the diff.
- #4 Typed-or-bodyless mutations — NOT TOUCHED: no backend handler in the diff.
- #5 No secrets in logs (`backend/app/**`) — NOT TOUCHED: no backend logging; UI diff adds no logging and handles no secret material (grep across `ui/src/features/notes` for password/token/secret/credential: zero hits).
- #8 Passwords never stored raw — NOT TOUCHED: no `.password_hash` writes.
- #9 OIDC identity binding by `sub` — NOT TOUCHED: no auth/OIDC code in the diff.

**Supplementary UI-safety scan (diff scope):**
- No dynamic code execution: grep `eval(` / `new Function` — zero hits.
- No network egress added: grep `fetch(` / `axios` / `XMLHttpRequest` in `ui/src/features/notes` — zero hits; the download builds a Blob from loader data the authenticated user already holds (no IDOR surface, no new data exposure — the file content is exactly the note the read view renders).
- No storage writes: grep `localStorage` / `sessionStorage` — zero hits.
- Object URL lifecycle: `URL.revokeObjectURL` called after the anchor click — no leaked blob URLs.

**Violations (if any):**
- None.
