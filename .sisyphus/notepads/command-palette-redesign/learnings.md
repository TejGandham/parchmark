
## [2026-02-16T20:53:23Z] Task 2: Command Palette Shell

- framer-motion AnimatePresence: wrap in conditional, use initial/animate/exit for fade
- Chakra Portal: renders outside DOM hierarchy, useful for modals/overlays
- Keyboard trap: useEffect with addEventListener on window, cleanup in return
- Auto-focus: callback ref pattern (node => node.focus()) more reliable than useEffect + ref.current.focus() in happy-dom
- happy-dom limitation: HTMLElement.focus() doesn't change document.activeElement - use vi.spyOn(HTMLInputElement.prototype, 'focus') in tests
- Backdrop blur: backdropFilter CSS property (Chakra prop)
- Zustand ephemeral state: exclude from persist via partialize (return state minus ephemeral fields)
- Version migration: handle old localStorage gracefully with default spreading in migrate callback
- Store pattern: createActions factory with stable references, immer mutations via set()
- Test pattern: use act() + useUIStore.setState() in beforeEach, ChakraProvider wrapper for component tests
- Existing tests use happy-dom environment (vitest.config.ts), not jsdom


## [2026-02-16] Task 1: Backend Access Tracking
- Migration pattern: idempotent column checks via `sa.inspect(conn)` + `_get_existing_columns()` prevent duplicate column errors
- Migration chain: `3c1162fce719` → `170dd30cebde` → `fad201191d3b` (new)
- Alembic `func.now()` for server-side timestamp vs Python `datetime.now()` — use `from sqlalchemy.sql import func`
- SQLAlchemy `text('0')` needed for `server_default` on Integer columns (not just `'0'`)
- SQLAlchemy async session: must `await db.commit()` AND `await db.refresh(note)` for updated values after server-side operations
- Pydantic v2: Use `int | None = None` not `Optional[int]` for optional fields — consistent with existing codebase style
- NoteResponse uses camelCase for frontend compatibility: `accessCount`, `lastAccessedAt` (matches `createdAt`/`updatedAt` pattern)
- All existing endpoints updated to return access fields — avoids inconsistent API responses
- Dev DB had stale alembic_version — needed `alembic stamp` before upgrade when tables already exist
- Test pattern: `TestClient` fixtures from conftest work with testcontainers, each worker gets own PostgreSQL

## [2026-02-16T21:12:52Z] Task 5: For You Scoring

- Heuristic scoring: 60% recency (1/(1+hours)), 40% frequency (min(count/20, 1.0))
- Fallback pattern: lastAccessedAt || updatedAt for recency
- Fire-and-forget API: try/catch with empty catch, no throw — swallows network errors silently
- Type extension: optional fields accessCount?, lastAccessedAt? on Note interface
- Score sorting: map to {note, score}, sort desc, slice, map back to Note[]
- Current note exclusion: filter before scoring via getForYouNotes(notes, currentNoteId, count)
- useParams() provides currentNoteId from route — no extra prop needed
- API_ENDPOINTS.NOTES.ACCESS added for /notes/{id}/access endpoint
- FOR YOU section conditionally rendered: only when forYouNotes.length > 0 && !isSearching
- Test gotcha: const arrays evaluated at describe-scope (before beforeEach) — use fixed ISO strings, not Date.now()
- Test gotcha: DOM traversal needed to check FOR YOU vs RECENT items (same data-testid)
- All test files need MemoryRouter + mockNavigate + mockUseParams since component uses router hooks
- noteScoring.ts: 100% coverage across statements/branches/functions/lines (20 tests)
- CommandPalette.test.tsx: 41 tests covering FOR YOU + RECENT + search + keyboard nav + trackNoteAccess


## [2026-02-16T21:14:12Z] Task 4: Palette Features

- Notes passed as prop from NotesLayout (useLoaderData in parent), NOT via useRouteLoaderData in palette
- filterNotes, sortNotes, groupNotesByDate reused from dateGrouping.ts
- Keyboard navigation: useEffect with window.addEventListener, activeIndex state, cleanup on unmount
- Conditional rendering: searchQuery.length > 0 toggles sections ↔ results
- Bold highlighting: regex split via escapeRegex + map with <Text as='strong'> (Chakra, not raw <strong>)
- Compact time format: formatCompactTime in compactTime.ts — diffMs-based thresholds (now/m/h/d/w/short date)
- Virtual scroll: react-window v2 List + RowComponentProps pattern for 50+ notes in All Notes expanded
- Note selection: useNavigate + closePalette pattern
- Expandable section: local useState toggle + chevron indicator (▸/▾)
- Sort controls: cycleSortOption cycles lastModified→alphabetical→createdDate, toggleSortDir flips desc/asc
- All Notes grouping: groupNotesByDate from dateGrouping.ts, renders group headers with count
- Tests mock useNavigate via vi.mock, use MemoryRouter wrapper
- Portal cleanup issue: cleanup() in both beforeEach AND afterEach needed to prevent stale DOM elements
- Task 5 ran in parallel, merged FOR YOU section + trackNoteAccess into CommandPalette and tests
- MutableRefObject cast needed for searchInputRef.current assignment (TS readonly ref fix)

