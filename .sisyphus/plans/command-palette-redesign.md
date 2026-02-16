# ParchMark: Command Palette Redesign (Phase 1)

## TL;DR

> **Quick Summary**: Replace ParchMark's traditional sidebar+content layout with a Raycast-style floating command palette. The editor becomes full-width by default; `Cmd+K` summons a centered palette showing AI-curated "For You" notes + "Recent" notes + search. Palette auto-closes on selection. Backend adds access tracking for heuristic scoring.
>
> **Deliverables**:
> - New `CommandPalette` component (floating, keyboard-driven, Raycast-style)
> - Full-width editor layout (sidebar removed)
> - "For You" section with Tier 1 heuristic scoring (recency + frequency)
> - "Recent" section (last 5 by updatedAt)
> - "All Notes" expandable section with date grouping
> - Search with smooth section-to-results transition
> - Create-from-search (Cmd+Enter when no results)
> - Backend: `access_count` + `last_accessed_at` columns + tracking endpoint
> - Inline loading/delete indicators in editor
> - Updated/replaced tests (TDD, maintain 90% coverage)
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Task 1 + Task 2 (parallel) → Task 3 → Task 6 → Task 7
>
> **Target Project**: `/home/developer/source/parchmark`

---

## Context

### Original Request
> "The left panel for notes is becoming too cluttered. Explore ways to optimise it, explore ways to use AI to show only relevant notes."

### Interview Summary
**Key Discussions**:
- User has 200+ notes and the flat/grouped sidebar list is overwhelming
- Rejected manual pinning: "The app should be smart enough to do that for me"
- Rejected two-line card items and context menus that override browser defaults
- Rejected the sidebar+content two-panel layout entirely
- Chose Raycast-style floating command palette after exploring 7 layout alternatives
- Phased approach: Phase 1 = layout + palette + basic scoring, Phase 2 (future) = AI embeddings
- Backend changes acceptable
- TDD approach confirmed
- Existing theme (colors, fonts) stays exactly the same

**Research Findings**:
- 8 background agents analyzed: codebase architecture, API surface, UX patterns (Notion/Apple Notes/Bear/Obsidian), AI relevance techniques, sidebar best practices, note item display, sort controls, layout alternatives
- Raycast, Linear, VS Code all use command palette as primary navigation
- Single-line title + compact time badge is optimal for narrow palettes
- UX research: pre-search smart feed addresses cognitive effort of search-first patterns

### Metis Review
**Identified Gaps** (all addressed):
- "For You" scoring location → Frontend (uses existing `useRouteLoaderData` pattern)
- Access count increment → New `POST /notes/{id}/access` endpoint (explicit, not side-effect)
- "Related to current note" → Deferred to Phase 2 (no embeddings in Phase 1)
- Header hamburger → Replaced with palette trigger button showing `⌘K`
- Dark theme confusion → Mockups were conceptual; implementation uses existing light theme tokens
- Unsaved changes on note switch → Accept data loss (matches current behavior)
- localStorage migration → Add version field, spread persisted state under defaults
- Mobile trigger → Header palette button is mobile fallback
- Create validation → Disable for queries < 4 chars (backend min_length)
- Test churn → Sidebar tests replaced alongside each task (TDD), not deferred

### Design Comps (Approved)
High-fidelity HTML mockups approved by user at:
- `/tmp/parchmark-palette-mockup.png` — Full page, all 4 states
- `/tmp/parchmark-state1-editor.png` — Default full-width editor
- `/tmp/parchmark-state2-smartfeed.png` — Palette with "For You" + "Recent"
- `/tmp/parchmark-state3-search.png` — Search results with bold match highlighting
- `/tmp/parchmark-state4-create.png` — No results + create action

---

## Work Objectives

### Core Objective
Replace the permanent sidebar with an on-demand floating command palette, making the editor full-width and note navigation keyboard-driven and AI-assisted.

### Concrete Deliverables
- `ui/src/features/ui/components/CommandPalette.tsx` — New floating palette component
- `ui/src/features/ui/hooks/useCommandPalette.ts` — Keyboard shortcut + state hook
- Modified `ui/src/features/notes/components/NotesLayout.tsx` — Full-width, no sidebar
- Modified `ui/src/features/ui/components/Header.tsx` — Palette trigger, no hamburger
- Modified `ui/src/features/ui/store/ui.ts` — Palette state, remove sidebar state
- Modified `ui/src/features/notes/components/NoteContent.tsx` — Inline loading/delete indicators
- `ui/src/utils/noteScoring.ts` — Heuristic scoring utility
- Modified `backend/app/models/models.py` — New columns
- Modified `backend/app/routers/notes.py` — Access endpoint
- Modified `backend/app/schemas/schemas.py` — Extended NoteResponse
- New Alembic migration
- Updated/new test files for all changes

### Definition of Done
- [ ] `Cmd+K` / `Ctrl+K` opens floating command palette
- [ ] Palette shows "For You" (heuristic-ranked) + "Recent" (last 5) + "All Notes" (expandable)
- [ ] Typing transitions from sections to search results
- [ ] Selecting a note navigates and auto-closes palette
- [ ] `Escape` or `Cmd+K` again closes palette
- [ ] No sidebar exists anywhere in the app
- [ ] Editor is full-width when palette is closed
- [ ] Create-from-search works with `Cmd+Enter`
- [ ] Palette auto-opens on `/notes` when no note is selected
- [ ] Note access tracked via backend endpoint
- [ ] All tests pass, coverage >= 90%
- [ ] Existing theme unchanged

### Must Have
- Floating centered palette (~480-520px wide, max ~60vh tall, 14px border-radius)
- Keyboard navigation: arrows, Enter to select, Escape to close
- Search input auto-focused on open
- Dimmed/blurred backdrop overlay
- Palette trigger button in header with `⌘K` hint (mobile fallback)
- `esc to close` hint in palette header
- Footer keyboard hints (`↑↓ navigate`, `↵ open`)
- "All Notes (N) ▸" expandable row
- Bold keyword highlighting in search results
- Result count during search
- Inline loading skeleton in editor
- Inline fade indicator during note deletion

### Must NOT Have (Guardrails)
- **NO dark theme changes** — Use existing Chakra UI semantic tokens as-is
- **NO Chakra Modal** — Use Portal + positioned Box (Modal has wrong focus trap/centering)
- **NO new data fetching library** — No react-query, SWR, axios. Use existing `services/api.ts`
- **NO fuzzy search** — Phase 1 uses existing `filterNotes()` substring match
- **NO content-similarity scoring** — "For You" is strictly recency + frequency
- **NO command registry/plugin system** — Palette shows notes only
- **NO spring physics animations** — Fade in 150ms, fade out 100ms only
- **NO JSDoc bloat** — Follow existing minimal-comment convention
- **NO separate palette store** — Palette state in existing `useUIStore`, max 3 new fields
- **NO Redis/background jobs** — Backend: 2 columns + 1 endpoint only
- **NO sidebar deletion until Task 7** — Sidebar stays as fallback during development

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — All verification executed by agents.

### Test Decision
- **Infrastructure exists**: YES (Vitest + React Testing Library + pytest)
- **Automated tests**: TDD
- **Framework**: Vitest (frontend), pytest (backend)

### Verification Tools

| Type | Tool | Method |
|------|------|--------|
| Palette UI | Playwright | Navigate, press Cmd+K, interact, assert DOM, screenshot |
| Backend API | Bash (curl) | Send requests, parse JSON, assert fields |
| Tests | Bash | Run vitest/pytest, assert pass count and coverage |
| Cleanup | Bash (ast-grep) | Search for removed references, assert 0 matches |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: Backend — Migration + Access Endpoint [no deps]
└── Task 2: Frontend — Palette UI Shell [no deps]

Wave 2 (After Wave 1):
├── Task 3: Frontend — Layout Rewire [depends: 2]
├── Task 4: Frontend — Palette Features: sections + search [depends: 2]
└── Task 5: Frontend — "For You" Scoring + Access Integration [depends: 1, 2]

Wave 3 (After Wave 2):
├── Task 6: Frontend — Create-from-Search + Edge Cases [depends: 3, 4]
└── Task 7: Cleanup + Final QA [depends: 3, 4, 5, 6]
```

### Dependency Matrix

| Task | Depends On | Blocks | Parallelize With |
|------|------------|--------|-----------------|
| 1 | None | 5 | 2 |
| 2 | None | 3, 4, 5 | 1 |
| 3 | 2 | 6, 7 | 4, 5 |
| 4 | 2 | 6, 7 | 3, 5 |
| 5 | 1, 2 | 7 | 3, 4 |
| 6 | 3, 4 | 7 | 5 |
| 7 | 3, 4, 5, 6 | None | None (final) |

---

## TODOs

- [x] 1. Backend: Migration + Access Tracking Endpoint

  **What to do**:
  - Alembic migration adding to `notes` table:
    - `access_count`: Integer, server_default=0, nullable=False
    - `last_accessed_at`: DateTime(timezone=True), nullable=True
  - Use idempotent migration pattern (check column exists before adding)
  - Update `Note` model in `models.py` with new columns
  - Create `POST /api/notes/{note_id}/access` endpoint:
    - Increments `access_count` by 1, sets `last_accessed_at` to now(UTC)
    - Returns updated NoteResponse
    - Requires auth, validates note ownership
  - Extend `NoteResponse` with optional fields: `accessCount`, `lastAccessedAt`
  - TDD: migration tests, endpoint tests, schema tests

  **Must NOT do**: No Redis, no background jobs, no changes to existing CRUD endpoints

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`git-master`]

  **Parallelization**: Wave 1 (parallel with Task 2) | Blocks: 5 | Blocked By: None

  **References**:
  - `backend/app/models/models.py:24-45` — Note model column definitions
  - `backend/app/routers/notes.py:1-120` — Async endpoint pattern with auth deps
  - `backend/app/schemas/schemas.py:53-86` — Pydantic v2 NoteResponse schema
  - `backend/migrations/versions/3c1162fce719_*.py:27-43` — Idempotent migration helpers
  - `backend/app/auth/dependencies.py` — `get_current_user` dependency
  - `backend/app/database/database.py` — `get_async_db` session dependency

  **Acceptance Criteria**:
  - [ ] `alembic upgrade head` succeeds; `alembic downgrade -1` succeeds
  - [ ] `access_count` column exists with default 0; `last_accessed_at` nullable
  - [ ] `POST /api/notes/{id}/access` returns 200, increments count
  - [ ] 3 calls → accessCount equals 3, lastAccessedAt is recent timestamp
  - [ ] Non-existent note → 404; Unauthenticated → 401
  - [ ] Existing CRUD endpoints unchanged
  - [ ] `uv run pytest --cov=app` → all pass, >= 90% coverage

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: Access tracking increments correctly
    Tool: Bash (curl)
    Steps:
      1. GET /api/notes/{id} → capture initial accessCount (0 or null)
      2. POST /api/notes/{id}/access 3 times → Assert 200 each
      3. GET /api/notes/{id} → Assert accessCount=3, lastAccessedAt recent
    Evidence: Response bodies captured

  Scenario: Migration is reversible
    Tool: Bash
    Steps:
      1. alembic upgrade head → exit 0
      2. SELECT columns from notes → includes access_count, last_accessed_at
      3. alembic downgrade -1 → exit 0
      4. SELECT columns → access_count and last_accessed_at gone
      5. alembic upgrade head → exit 0 (re-apply)
    Evidence: Command outputs captured
  ```

  **Commit**: `feat(api): add note access tracking`

---

- [x] 2. Frontend: Command Palette UI Shell

  **What to do**:
  - Create `CommandPalette.tsx`: floating centered palette with Portal + positioned Box, dimmed backdrop, search input with auto-focus, section rendering slots (empty), footer keyboard hints, fade animation (AnimatePresence)
  - Create `useCommandPalette.ts`: global Cmd+K / Ctrl+K listener, toggle/open/close, Escape to close, prevent default browser Cmd+K
  - Add palette state to `ui.ts` store: `isPaletteOpen`, `paletteSearchQuery`, actions. Ephemeral (not persisted). Add `version: 2` to persist config.
  - Accessibility: `role="dialog"`, `aria-label="Command palette"`, keyboard trap
  - TDD: render/toggle/close/focus/escape tests

  **Must NOT do**: No Chakra Modal/Drawer/Popover, no real data wiring (Task 3/4), no complex animations, no separate store

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`, `playwright`]

  **Parallelization**: Wave 1 (parallel with Task 1) | Blocks: 3, 4, 5 | Blocked By: None

  **References**:
  - `ui/src/features/ui/store/ui.ts:1-91` — Zustand + Immer + persist pattern
  - `ui/src/features/notes/components/NoteContent.tsx:30-50` — Global keydown listener pattern
  - `ui/src/features/notes/components/NoteItem.tsx:15-114` — React.memo + keyboard handler pattern
  - `ui/src/__tests__/features/ui/components/SidebarDataRouter.test.tsx` — Data router test wrapper pattern
  - Design comp: `/tmp/parchmark-state2-smartfeed.png` — Visual reference

  **Acceptance Criteria**:
  - [ ] Cmd+K toggles palette; Escape closes; backdrop click closes
  - [ ] Search input auto-focused on open
  - [ ] Centered, ~480-520px wide, 14px border-radius, dimmed backdrop
  - [ ] `role="dialog"` and `aria-label` present
  - [ ] Footer keyboard hints visible
  - [ ] Fade in 150ms, out 100ms
  - [ ] Vitest: palette render/toggle/close/focus tests pass

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: Palette opens and closes with Cmd+K
    Tool: Playwright
    Steps:
      1. Navigate to /notes/{noteId}
      2. Assert: No [data-testid="command-palette"] visible
      3. Press Meta+k → Assert palette visible, search focused
      4. Press Meta+k → Assert palette NOT visible
      5. Screenshot: .sisyphus/evidence/task-2-toggle.png

  Scenario: Escape and backdrop close palette
    Tool: Playwright
    Steps:
      1. Meta+k → palette opens
      2. Escape → palette closes
      3. Meta+k → palette opens
      4. Click backdrop → palette closes
  ```

  **Commit**: `feat(ui): add command palette shell`

---

- [x] 3. Frontend: Layout Rewire — Full-Width Editor

  **What to do**:
  - Modify `NotesLayout.tsx`: remove Sidebar import/render, full-width editor, mount CommandPalette, pass notes via `useRouteLoaderData`
  - Modify `Header.tsx`: remove `toggleSidebar` prop/hamburger, add centered "Search notes... ⌘K" trigger button calling `openPalette()`
  - Modify `NotesLayout.tsx`: remove auto-redirect on `/notes` index (the redirect lives in NotesLayout, not router.tsx), render empty state that triggers palette open
  - Modify `NoteContent.tsx`: add inline loading skeleton, fade-out on deletion, remove "sidebar" text references
  - Modify `ui.ts`: remove `isSidebarOpen`/`toggleSidebar`. Keep sort/group state (used by palette "All Notes")
  - Use `lsp_find_references` on `isSidebarOpen`, `Sidebar`, `toggleSidebar` to find ALL consumers
  - Update tests: `NotesLayout.test.tsx`, `Header.test.tsx`, `NoteContentDataRouter.test.tsx`

  **Must NOT do**: Do NOT delete Sidebar.tsx yet (Task 7), do NOT implement palette sections (Task 4)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`, `playwright`]

  **Parallelization**: Wave 2 (parallel with Tasks 4, 5) | Blocks: 6, 7 | Blocked By: 2

  **References**:
  - `ui/src/features/notes/components/NotesLayout.tsx:1-75` — Current layout (THIS changes)
  - `ui/src/features/ui/components/Header.tsx:1-60` — Current header with hamburger (~line 30)
  - `ui/src/router.tsx:47-96` — Route structure, `notes-layout` loader ID
  - `ui/src/features/ui/components/Sidebar.tsx:1-30` — What's being replaced (understand props/data flow)
  - Design comp: `/tmp/parchmark-state1-editor.png` — Full-width editor target

  **Acceptance Criteria**:
  - [ ] No sidebar element renders on any `/notes` route
  - [ ] Editor spans full viewport width
  - [ ] Header shows "Search notes... ⌘K" button
  - [ ] Clicking header button opens palette
  - [ ] `/notes` with no noteId → palette opens automatically
  - [ ] Note loading shows inline skeleton
  - [ ] Note deletion shows fade-out
  - [ ] No reference to `toggleSidebar` in active code
  - [ ] Updated tests pass

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: Full-width editor, no sidebar
    Tool: Playwright
    Steps:
      1. Navigate to /notes/{noteId}
      2. Assert: No [data-testid="sidebar"] or [aria-label="Notes navigation"]
      3. Assert: Editor container width ~= viewport width
      4. Screenshot: .sisyphus/evidence/task-3-fullwidth.png

  Scenario: Palette auto-opens on /notes index
    Tool: Playwright
    Steps:
      1. Navigate to /notes (no noteId)
      2. Assert: [data-testid="command-palette"] visible within 3s
      3. Assert: Search input focused
  ```

  **Commit**: `refactor(ui): replace sidebar with full-width layout`

---

- [x] 4. Frontend: Palette Features — Sections + Search

  **What to do**:
  - "Recent" section: last 5 by `updatedAt` desc. Header "RECENT", single-line items (title left, compact time right)
  - "All Notes" expandable: "All Notes (N) ▸" row → expands with date-grouped notes + sort controls (icon buttons). Reuse `sortNotes()`, `groupNotesByDate()` from `dateGrouping.ts`. Virtual scroll for 50+ notes.
  - Search transition: non-empty query → hide sections, show filtered results with bold keyword highlighting + result count. Empty query → restore sections. Use existing `filterNotes()`.
  - Keyboard navigation: arrow keys move active highlight, Enter selects + navigates + closes palette
  - Note selection: `useNavigate(/notes/{id})` + `closePalette()`
  - Compact time format: 5m, 2h, 1d, 2w, Jan 15
  - Wire to `useRouteLoaderData` notes data

  **Must NOT do**: No "For You" (Task 5), no fuzzy search, no stagger animations

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`, `playwright`]

  **Parallelization**: Wave 2 (parallel with Tasks 3, 5) | Blocks: 6, 7 | Blocked By: 2

  **References**:
  - `ui/src/utils/dateGrouping.ts:1-144` — `filterNotes()`, `sortNotes()`, `groupNotesByDate()` — REUSE
  - `ui/src/features/ui/components/Sidebar.tsx:150-300` — Current grouped rendering with section headers/counts
  - `ui/src/features/notes/components/NoteItem.tsx:15-114` — Memoized item (adapt: simpler, just title+time)
  - `ui/src/components/VirtualizedNotesList.tsx:1-89` — react-window pattern for "All Notes"
  - Design comp: `/tmp/parchmark-state2-smartfeed.png` — Section layout
  - Design comp: `/tmp/parchmark-state3-search.png` — Search results

  **Acceptance Criteria**:
  - [ ] "RECENT" shows last 5 by updatedAt
  - [ ] Compact time format works (5m, 2h, 1d, 2w, Jan 15)
  - [ ] Arrow keys navigate, Enter selects and closes
  - [ ] "All Notes (N) ▸" shows correct count; click expands with date groups
  - [ ] Typing → sections disappear, results appear with bold matches + count
  - [ ] Clearing search → sections reappear
  - [ ] Palette height adjusts to content
  - [ ] Tests pass >= 90% coverage

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: Search transitions from sections to results
    Tool: Playwright
    Steps:
      1. Meta+k → Assert "RECENT" visible
      2. Type "product" → Assert "RECENT" NOT visible, results shown
      3. Assert bold "product" in result titles, result count visible
      4. Clear input → Assert "RECENT" visible again

  Scenario: Keyboard navigation and selection
    Tool: Playwright
    Steps:
      1. Open palette, search for term with 3+ results
      2. Assert first result highlighted
      3. ArrowDown → second highlighted
      4. Enter → URL changed to /notes/{id}, palette closed
  ```

  **Commit**: `feat(ui): add palette sections search and navigation`

---

- [x] 5. Frontend: "For You" Scoring + Access Integration

  **What to do**:
  - Create `noteScoring.ts`:
    - `computeForYouScore(note)`: `score = (0.6 * recencyScore) + (0.4 * frequencyScore)` where `recencyScore = 1/(1+hoursSinceLastAccess)`, `frequencyScore = min(accessCount/20, 1.0)`. Fallback to `updatedAt` if no access data.
    - `getForYouNotes(notes, currentNoteId, count=3)`: scores all, excludes current, returns top N
  - "For You" section in palette: above "Recent", header "FOR YOU", top 3 scored notes
  - Access tracking: on note selection, fire-and-forget `POST /api/notes/{id}/access`
  - Add `trackNoteAccess(noteId)` to `services/api.ts`
  - Extend `types/index.ts`: `accessCount?: number; lastAccessedAt?: string;` (optional)
  - TDD: scoring formula tests, exclusion tests, fallback tests

  **Must NOT do**: No embeddings, no blocking on access call, no ML scoring

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**: Wave 2 (parallel with Tasks 3, 4) | Blocks: 7 | Blocked By: 1, 2

  **References**:
  - `ui/src/utils/dateGrouping.ts:1-50` — Utility pattern
  - `ui/src/services/api.ts:125-149` — API function pattern
  - `ui/src/types/index.ts:1-13` — Note type extension
  - `ui/src/__tests__/utils/dateGrouping.test.ts` — Utility test pattern

  **Acceptance Criteria**:
  - [ ] `computeForYouScore()` returns 0-1, matches formula exactly
  - [ ] `getForYouNotes()` excludes current note
  - [ ] "FOR YOU" section above "RECENT" in palette with 3 items
  - [ ] Note selection fires `POST /notes/{id}/access` (fire-and-forget)
  - [ ] Note type extended with optional fields
  - [ ] Scoring unit tests pass with 100% branch coverage

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: "For You" shows scored notes excluding current
    Tool: Playwright
    Steps:
      1. Navigate to /notes/{someId}
      2. Meta+k → Assert "FOR YOU" above "RECENT"
      3. Assert 3 items in "FOR YOU"
      4. Assert current note title NOT in "FOR YOU"
  ```

  **Commit**: `feat(ui): add For You scoring and access tracking`

---

- [x] 6. Frontend: Create-from-Search + Edge Cases

  **What to do**:
  - Create-from-search: 0 results → "No notes found" + "Create '{query}'" row (burgundy accent). Cmd+Enter creates via `useFetcher.submit()`, closes palette, navigates to new note with `?editing=true`. Disable for queries < 4 chars with hint.
  - Zero notes: palette shows "No notes yet" + create CTA
  - Deep link: `/notes/{id}` directly → palette stays closed
  - Loading: palette skeleton items (3 per section) while route loads
  - Unsaved changes: accept data loss on note switch (document, matches current behavior)
  - TDD all edge cases

  **Must NOT do**: No unsaved changes dialog, no offline support

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`frontend-ui-ux`, `playwright`]

  **Parallelization**: Wave 3 | Blocks: 7 | Blocked By: 3, 4

  **References**:
  - `ui/src/features/notes/actions.ts` — `createNoteAction` existing pattern
  - `ui/src/features/ui/components/Sidebar.tsx:280-320` — Current create flow
  - `ui/src/components/NoteCardSkeleton.tsx:1-31` — Skeleton pattern
  - `ui/src/features/notes/store/notesUI.ts` — `editedContent` for unsaved detection
  - Design comp: `/tmp/parchmark-state4-create.png` — Create-from-search visual

  **Acceptance Criteria**:
  - [ ] 0 results → "No notes found" + "Create '{query}'" visible
  - [ ] Query < 4 chars → create disabled with hint
  - [ ] Cmd+Enter creates note, navigates, closes palette, edit mode
  - [ ] Zero-notes state shows create CTA
  - [ ] Deep link → palette stays closed
  - [ ] Loading: skeleton items while route loads
  - [ ] All edge case tests pass

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: Create note from search
    Tool: Playwright
    Steps:
      1. Meta+k → type "My Unique New Topic" (no match)
      2. Assert "No notes found" + "Create 'My Unique New Topic'" visible
      3. Meta+Enter → URL changes, palette closed, editor in edit mode
      4. Assert note title = "My Unique New Topic"

  Scenario: Short query blocks creation
    Tool: Playwright
    Steps:
      1. Meta+k → type "ab" (< 4 chars)
      2. Assert create row absent or disabled
      3. Assert minimum length hint visible
  ```

  **Commit**: `feat(ui): add create-from-search and edge cases`

---

- [x] 7. Cleanup: Remove Sidebar + Dead Code + Final QA

  **What to do**:
  - Delete: `Sidebar.tsx`, `SidebarDataRouter.test.tsx`, `VirtualizedNotesList.tsx` (verify not used elsewhere via `lsp_find_references`)
  - Remove dead state: `isSidebarOpen`, `toggleSidebar` (if not already done in Task 3)
  - Remove `.sidebar-shadow` from CSS
  - Remove all dead imports via `ast_grep_search`
  - Run full suites: `npm test`, `uv run pytest --cov=app`, `npm run lint`, `uv run ruff check`
  - Final Playwright smoke test: all 4 palette states

  **Must NOT do**: Do NOT delete `dateGrouping.ts` (used by palette), `NoteCardSkeleton.tsx` (reused)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**: Sequential (final) | Blocks: None | Blocked By: 3, 4, 5, 6

  **Acceptance Criteria**:
  - [ ] `Sidebar.tsx` does not exist
  - [ ] Zero references to `Sidebar`, `isSidebarOpen`, `toggleSidebar` in active code
  - [ ] `npm test` → all pass, >= 90% coverage
  - [ ] `npm run lint` → 0 errors
  - [ ] `uv run pytest --cov=app` → all pass, >= 90%
  - [ ] `uv run ruff check` → 0 errors

  **Agent-Executed QA Scenarios:**
  ```
  Scenario: No dead references remain
    Tool: Bash (ast-grep)
    Steps:
      1. Search "Sidebar" in TSX → 0 matches
      2. Search "isSidebarOpen" in TS/TSX → 0 matches
      3. Search "toggleSidebar" in TS/TSX → 0 matches
      4. Search "sidebar" in CSS → 0 matches

  Scenario: Full smoke test
    Tool: Playwright
    Steps:
      1. /notes → palette opens, "FOR YOU" + "RECENT" visible
      2. Click note → closes, full-width editor loads
      3. Meta+k → palette opens, type search → results appear
      4. Escape → closes
      5. Meta+k → type nonexistent → "Create" row → Meta+Enter → note created
      6. Screenshot: .sisyphus/evidence/task-7-smoke.png
  ```

  **Commit**: `chore(ui): remove sidebar and dead code`

---

## Commit Strategy

| After Task | Message | Verification |
|------------|---------|-------------|
| 1 | `feat(api): add note access tracking` | `uv run pytest` |
| 2 | `feat(ui): add command palette shell` | `npm test` |
| 3 | `refactor(ui): replace sidebar with full-width layout` | `npm test` |
| 4 | `feat(ui): add palette sections search and navigation` | `npm test` |
| 5 | `feat(ui): add For You scoring and access tracking` | `npm test` |
| 6 | `feat(ui): add create-from-search and edge cases` | `npm test` |
| 7 | `chore(ui): remove sidebar and dead code` | `npm test && npm run lint` |

---

## Success Criteria

### Verification Commands
```bash
cd /home/developer/source/parchmark/ui && npm test
cd /home/developer/source/parchmark/backend && uv run pytest --cov=app
cd /home/developer/source/parchmark/ui && npm run lint
cd /home/developer/source/parchmark/backend && uv run ruff check
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] Sidebar fully removed (no file, no references, no CSS)
- [ ] Editor full-width when palette closed
- [ ] Cmd+K / Ctrl+K opens palette on all platforms
- [ ] "For You" shows heuristic-scored notes
- [ ] "Recent" shows last 5 by updatedAt
- [ ] Search filters with bold keyword highlighting
- [ ] Create-from-search with Cmd+Enter
- [ ] Palette auto-opens on launch
- [ ] All tests pass, >= 90% coverage
- [ ] Theme unchanged (existing light mode)
- [ ] Access tracking endpoint functional
