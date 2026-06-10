## Karta Structural Conformance: Read-view note download button (markdown export)

**Verdict:** CONFORMANT

**Binder:** C:\Users\Developer\src\parchmark\.keel\worktrees\WI01-note-download\docs\exec-plans\binders\note-download.json
**Feature ID:** WI01
**Feature index:** 0
**Feature pointer base:** /work_items/0
**Lane:** karta (from routing.json .pipeline)
**Code:** ui/src/features/notes/utils/noteDownload.ts; ui/src/features/notes/components/NoteActions.tsx; ui/src/features/notes/components/NoteContent.tsx; ui/src/__tests__/features/notes/components/NoteDownload.test.tsx

**Assertion disposition:**
- `/work_items/0/oracle/assertions/0` — "Read view of a note renders a download control (an icon button with a download icon) in the action toolbar alongside Edit and Delete." — execution-required (rendered axis; identity/wiring part inspection-verifiable and CONFORMS: NoteActions view-mode branch renders a faDownload IconButton in the same HStack as Delete and Edit) — covered by test [NoteDownload.test.tsx: "renders a download icon button in the read-view toolbar alongside Edit and Delete"] — composed render, real NoteActions, asserts icon svg + shared toolbar parent with Delete. Test lives under `src/__tests__/**` which the green-gate command (`npm run test:coverage`, vitest `include`) runs.
- `/work_items/0/oracle/assertions/1` — "Activating the download control triggers a browser file download whose filename is the slugified note title plus '.md' (e.g. a note titled 'Meeting Notes 6/10' downloads as 'meeting-notes-6-10.md')." — execution-required — covered by test [NoteDownload.test.tsx: "downloads the note as slugified-title.md via an object-URL anchor click"] — uses the Binder's own example title and asserts the clicked anchor's `download` is exactly `meeting-notes-6-10.md`.
- `/work_items/0/oracle/assertions/2` — "The downloaded file body equals removeH1FromContent(note.content) — the title-stripped markdown — and does NOT contain the H1 title line." — execution-required — covered by test [NoteDownload.test.tsx: "writes the title-stripped markdown (removeH1FromContent) as the file body"] — reads the Blob handed to URL.createObjectURL, compares to the REAL (unmocked) removeH1FromContent, asserts absence of the H1 line. Inspection corroborates: downloadNoteAsMarkdown calls removeH1FromContent(note.content) verbatim.
- `/work_items/0/oracle/assertions/3` — "Downloading performs no network request — the file is built from the note data already loaded into the read view." — execution-required — covered by test [NoteDownload.test.tsx: "performs no network request when downloading"] — fetch stub and router fetcher.submit both asserted uncalled. Inspection corroborates: noteDownload.ts contains no fetch/XHR/import of the API client; input is the loader-data note object.
- `/work_items/0/oracle/assertions/4` — "A note whose title slugifies to empty (e.g. whitespace-only) downloads as 'note-<id>.md' using the note's id." — execution-required — covered by test [NoteDownload.test.tsx: "falls back to note-<id>.md when the title slugifies to empty"] — whitespace-only title, id `note-3`, asserts `note-note-3.md`.

Contract fields (inspection-verifiable, all CONFORM):
- `file_format`/`file_extension`: Blob typed `text/markdown`, filename suffixed `.md` in both branches of `noteDownloadFilename`.
- `filename_rule`: `slugifyNoteTitle` lowercases, collapses non-alphanumeric runs to single hyphens, trims edge hyphens ('Meeting Notes 6/10' → 'meeting-notes-6-10'); empty slug falls back to `note-<id>`; 'Untitled Note' slugifies normally.
- `file_body_source`: `removeH1FromContent(note.content)` — the named function, not a reimplementation; full `note.content` is NOT used as the body.
- `control`: Tooltip-wrapped IconButton, `variant="ghost"`, `size="sm"`, `color="text.muted"`, conditional on the handler prop — the Delete IconButton pattern mirrored field-for-field.
- `placement`: rendered in the `!isEditing` branch of NoteActions inside the read-view toolbar HStack, alongside Delete and Edit; NoteContent passes `onDownload` only to the read-view NoteActions instance.
- `generation`: pure client-side (Blob → object URL → anchor click → revoke); no backend route, no fetch.

**Deviations (if any):**
- None.

**Spec-suspect (only when Verdict is SPEC-SUSPECT):**
- n/a

**Notes (CONFORMANT with minor items):**
- [MINOR] The oracle `tooling` names "render from test-utils/render"; no `test-utils/render` module exists in this codebase — the project's actual provider-wrapping helper is `TestProvider` from `src/__tests__/__mocks__/testUtils`, which the test uses. Vitest + RTL + browser-download-mechanism assertion are honored as specified. Not blocking.
- Verdict note: CONFORMANT is structural alignment by inspection plus test-coverage disposition — not a runtime-correctness guarantee; the green gate is the only runtime truth.
