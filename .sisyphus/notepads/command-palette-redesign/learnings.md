
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
