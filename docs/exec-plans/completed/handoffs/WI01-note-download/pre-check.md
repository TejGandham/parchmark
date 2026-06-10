# Execution Brief: Read-view note download button (markdown export)

**Binder:** C:\Users\Developer\src\parchmark\.keel\worktrees\WI01-note-download\docs\exec-plans\binders\note-download.json
**Feature ID:** WI01
**Feature index:** 0
**Feature pointer base:** /work_items/0
**Layer:** ui
**Binder-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — `.dependencies.intra_binder[]` and `.dependencies.cross_binder[]` are both empty.
**Research needed:** NO
**Designer needed:** NO (trivial function — see Routing rationale)
**Implementer needed:** YES
**Safety auditor needed:** NO (no auth/credential/token surface; pure client-side UI; no domain-invariant path touched — note: the Karta lane runs safety-auditor regardless of this flag)
**Arch-advisor needed:** NO

**Intent:** mid-sized
**Complexity:** trivial

**What to build:**
A download IconButton in the read-view action toolbar (NoteActions, alongside Edit and Delete) that saves the currently-viewed note as a `.md` file, generated entirely in the browser: filename `slugify(note.title) + '.md'` falling back to `note-<id>.md` when the title slugifies to empty; body `removeH1FromContent(note.content)`; no network involved.

**New files:**
- `ui/src/features/notes/utils/noteDownload.ts` — `slugifyNoteTitle(title)`, `noteDownloadFilename(note)`, `downloadNoteAsMarkdown(note)` (Blob → object URL → anchor click → revoke). Pure client-side; the only place that touches the DOM download mechanism.
- `ui/src/__tests__/features/notes/components/NoteDownload.test.tsx` — composed read-view tests (real NoteActions inside NoteContent) covering all five oracle assertions.

**Modified files:**
- `ui/src/features/notes/components/NoteActions.tsx` — add optional `onDownload?: () => void` prop; render a Tooltip-wrapped download IconButton (FontAwesome `faDownload`) in view mode when `onDownload` is provided, mirroring the existing Delete IconButton pattern.
- `ui/src/features/notes/components/NoteContent.tsx` — add a `downloadNote` handler calling `downloadNoteAsMarkdown(currentNote)` and pass `onDownload` to the view-mode NoteActions.

**Existing patterns to follow:**
- `ui/src/features/notes/components/NoteActions.tsx` (Delete IconButton block, lines 52–65) — Tooltip + IconButton, `variant="ghost"`, `size="sm"`, `color="text.muted"`, conditional render on handler prop, view-mode only.
- `ui/src/services/markdownService.ts:removeH1FromContent` — the exact body source the contract names; do NOT reimplement title-stripping.
- `ui/src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx` — the mock harness for NoteContent (router hooks, store, react-markdown, Mermaid, NoteMetadata); reuse its `setupMocks` shape but render the REAL NoteActions so the composed toolbar is exercised.

**Assertion traceability:**
- `/work_items/0/oracle/assertions/0` → render NoteContent in read view (real NoteActions); assert a button named /download note/i exists alongside /edit/i and /delete note/i.
- `/work_items/0/oracle/assertions/1` → stub `URL.createObjectURL`; spy `HTMLAnchorElement.prototype.click` capturing `this`; note titled 'Meeting Notes 6/10' → clicked anchor's `download` attr === 'meeting-notes-6-10.md'.
- `/work_items/0/oracle/assertions/2` → capture the Blob passed to `URL.createObjectURL`; `await blob.text()` equals `removeH1FromContent(note.content)` (real markdownService, unmocked) and does not match /^#\s/m for the title line.
- `/work_items/0/oracle/assertions/3` → spy `globalThis.fetch` and the mocked `fetcher.submit`; assert neither called during download.
- `/work_items/0/oracle/assertions/4` → note with whitespace-only title and id 'note-3' → clicked anchor's `download` attr === 'note-note-3.md'.

**Edge cases:**
- Title slugifies to empty (whitespace-only, symbols-only) → `note-<id>.md` fallback (oracle assertion 4).
- Title with path-hostile characters (`/`, `:`, `*`) → slug replaces non-alphanumeric runs with single `-`, trims leading/trailing `-` (contract example: 'Meeting Notes 6/10' → 'meeting-notes-6-10.md').
- Download control must NOT render in edit mode (mirrors Delete's view-mode-only behavior).
- Object URL must be revoked after click (no leak per download).

**Risks:**
- happy-dom may not implement `URL.createObjectURL`/`revokeObjectURL` — tests must define/stub them rather than assume jsdom behavior.
- Coverage floor is 90% (branches/functions/lines/statements); the new util and new branches must be fully exercised by the new test file.

**Verify command:** UI gate per `makefiles/ui.mk` (`test-ui-all`): `cd ui && npm run lint` then `cd ui && npm run test:coverage`. Backend gate (`test-backend-all` static half): `cd backend && uv run ruff check app tests --no-fix && uv run ruff format --check app tests && uv run mypy app`; backend pytest requires Docker (testcontainers) and is N/A on a zero-backend-delta diff on this host.

**Path convention:** `ui/src/` — feature-first layout (`features/notes/{components,store,styles}`); shared utils in `ui/src/utils/`; tests mirror source under `ui/src/__tests__/`.

**Constraints for downstream:**
- MUST: reuse `removeH1FromContent` from `ui/src/services/markdownService.ts` for the file body — the contract names it explicitly.
- MUST: mirror the Delete IconButton pattern (Tooltip + IconButton, ghost/sm/text.muted, conditional on handler prop, view-mode only) for visual consistency.
- MUST: use FontAwesome `faDownload` from `@fortawesome/free-solid-svg-icons` (already a dependency) — no new icon package.
- MUST NOT: add any backend route, fetch, or server round-trip — generation is pure client-side per the contract.
- MUST NOT: include the H1 title in the file body — title lives in the filename only.
- MUST NOT: introduce a slugify/file-saver dependency — the slug rule is ~3 lines of regex; a library is scope inflation.
- MUST NOT: modify existing test files (`NoteActions.test.tsx`, `NoteContentDataRouter.test.tsx`) — inherited tests are prior contracts; new coverage goes in the new test file.
- MUST NOT: add HTML/PDF export, export menus, or configurability — excluded by the Binder scope.

### Routing rationale

`designer_needed` is NO despite `layer: ui` with a multi-file diff: the Binder's
`design_facts` already fix every design decision (control style, icon, placement,
filename rule, body source, format) and the control mirrors an existing sibling
(Delete IconButton) line-for-line — a static, stateless control with zero new
interface/state design. There is nothing left for frontend-designer to decide;
complexity is trivial in the designer-relevant sense (no state, no new component,
no layout change). `researcher_needed` is NO: `.pretriage_inputs.novel_dependency`
is corroborating-only and is a miss here — Blob + `URL.createObjectURL` + anchor
click are browser-native, and `faDownload` ships in the already-installed
`@fortawesome/free-solid-svg-icons`; no new third-party API, protocol, or library
enters the codebase.

**Ready:** YES
**Next hop:** implementer (Karta lean lane — no test-writer hop; spec-first)
