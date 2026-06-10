## Implementation Report: Read-view note download button (markdown export)

**Files created/modified:**
- `ui/src/features/notes/utils/noteDownload.ts` — NEW. `slugifyNoteTitle` (lowercase, non-alphanumeric runs → single `-`, trim edge hyphens), `noteDownloadFilename` (`slug.md`, fallback `note-<id>.md` on empty slug), `downloadNoteAsMarkdown` (body = `removeH1FromContent(note.content)` → Blob `text/markdown` → object URL → anchor click → revoke). Pure client-side; no fetch anywhere.
- `ui/src/features/notes/components/NoteActions.tsx` — added optional `onDownload?: () => void` prop; view-mode Tooltip-wrapped download IconButton (FontAwesome `faDownload`, `variant="ghost"`, `size="sm"`, `color="text.muted"`, `isDisabled={isDeleting}`), conditional on the prop exactly like the Delete IconButton it mirrors, placed before Delete in the toolbar.
- `ui/src/features/notes/components/NoteContent.tsx` — `downloadNote` handler (defined after the null-note early return, so `currentNote` is narrowed) calling `downloadNoteAsMarkdown(currentNote)`; passed `onDownload={downloadNote}` to the read-view NoteActions. The new-note editing branch passes no `onDownload` (button is edit-mode-hidden anyway).
- `ui/src/__tests__/features/notes/components/NoteDownload.test.tsx` — NEW. Composed read-view tests: real NoteActions inside NoteContent, real markdownService; router hooks/store/react-markdown/Mermaid/NoteMetadata mocked (same harness shape as `NoteContentDataRouter.test.tsx`). Download mechanism captured via stubbed `URL.createObjectURL`/`revokeObjectURL` and an `HTMLAnchorElement.prototype.click` spy recording `download`/`href` at click time.

**Change scope:** initial

**Changed paths:**
- ui/src/features/notes/utils/noteDownload.ts
- ui/src/features/notes/components/NoteActions.tsx
- ui/src/features/notes/components/NoteContent.tsx
- ui/src/__tests__/features/notes/components/NoteDownload.test.tsx

**Test status:** PASS
**Commands run:**
- `npx vitest run src/__tests__/features/notes/components/NoteDownload.test.tsx` — 6/6 passed (5 oracle assertions + edit-mode-hidden edge case).
- `npx tsc` — exit 0.
- `npm run lint` — exit 0 (after prettier formatting pass).

**Blockers (if any):**
- None.

### Decisions
- Slug rule implemented inline (~3 lines of regex) per the pre-check MUST NOT on new dependencies; matches the contract example `'Meeting Notes 6/10' → 'meeting-notes-6-10.md'` and `'Untitled Note' → 'untitled-note.md'`.
- Body source is the existing `removeH1FromContent` from `services/markdownService` — contract names it; no reimplementation, keeping FE/BE markdown parity untouched (`utils/markdown.ts` not edited).
- Download control renders only in view mode and only when `onDownload` is provided, mirroring the Delete IconButton contract exactly (Tooltip, ghost/sm/text.muted, conditional prop).
- Oracle assertion 2 ("triggers a browser file download") is execution-required and is test-covered by spying the anchor-click download mechanism — the standard RTL-testable boundary for browser downloads; no KARTA-DEFER needed.
- All five oracle assertions are covered by executing tests in the new file; no inherited test was modified.
