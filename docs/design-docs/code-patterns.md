# Code Patterns

Concrete conventions for parchmark's frontend and backend. Consult when writing new code so it matches existing shape.

## Frontend (Vue 3 + TypeScript)

The v2 `ui/` is a ground-up Vue 3 rewrite. Components are `.vue` SFCs using
`<script setup lang="ts">`; logic helpers are plain `.ts`. There are **no
`.tsx` files**. Build tool is Vite; the `@` path alias maps to `ui/src`.
Feature-first layout under `ui/src`: `features/auth/`, `features/shell/`,
`features/notes/`, plus `design-system/` and `services/`. `App.vue` and
`main.ts` live at the `src/` root — there is no `src/config/`, `src/store/`,
or `src/router/`.

### HTTP Client & Error Handling

The shared client is an `ofetch` instance in `ui/src/services/http.ts`
(`ofetch.create({ retry: false })`). `request<T>()` owns the single
refresh-and-retry policy: on a `401` for any non-`/auth/refresh` call it
invokes the injected `onRefresh()` once and retries exactly once, otherwise
throws an `ApiError` (custom class carrying `status` + `detail` parsed from
the backend `{ detail }` body).

```typescript
import { request, ApiError } from '@/services/http';

try {
  const data = await request<T>('/some/path');
} catch (e) {
  if (e instanceof ApiError) { /* e.status, e.detail */ }
}
```

`http.ts` never imports the auth store. The auth layer wires itself in via
`setAuthHooks({ getToken, onRefresh })` (DI, avoids an import cycle). Base URL
is `import.meta.env.VITE_API_URL ?? "/api"`.

### Auth (composable singleton, no store library)

`ui/src/features/auth/useAuth.ts` is a composable singleton — module-level
`session`/`user`/`error`/`pending` refs at file scope; `useAuth()` returns the
same shared refs every call. The session is persisted as one JSON object via
`@vueuse/core` `useStorage<AuthSession>("pm_auth", …)` (shape
`{ accessToken, refreshToken, user }`).

```typescript
import { useAuth } from '@/features/auth/useAuth';

const { user, error, pending, isAuthenticated, login, logout, restoreSession } = useAuth();
```

`login()` posts to `/auth/login` then fetches `/auth/me` (the login response
carries no user). `refresh()` dedupes concurrent 401s with a shared
`refreshPromise` and clears the session on failure. The thin endpoint wrappers
(`login`, `refreshToken`, `getCurrentUser`, `logout`) live in
`ui/src/services/auth.ts`.

### State management — Vue refs/composables, NO Pinia/Vuex

There is no store library. Cross-cutting auth state is the `useAuth()`
composable singleton (above); per-view UI state is plain `ref`/`computed`
inside SFCs. For example `AppShell.vue` holds `notes`, `activeId`, `mode`,
`search`, `activeTags`, `navOpen`, `settingsActive`, `theme` as local refs.

### Routing — NO Vue Router; manual view switching

There is no router. The top-level switch is an **auth gate in `App.vue`**: a
`ready` ref gates first paint (set true after `restoreSession()` resolves in
`onMounted`), then `v-if="!ready"` loading → `v-else-if="!isAuthenticated"`
`<LoginView/>` → `v-else` `<AppShell/>`. Inside the app, "navigation" is ref
toggles in `AppShell.vue` (`mode` is `"read"|"edit"`, `activeId` selects a
note, `settingsActive` toggles a settings placeholder); views are
`v-if`/`v-else-if`/`v-else` `<section>`s.

### Markdown Processing

`ui/src/features/notes/markdownRender.ts` is the frontend renderer;
`backend/app/utils/markdown.py` is the backend counterpart — keep title/H1
handling in sync with the `parchmark-markdown-sync` skill after editing
either. `renderMarkdownBody()` strips the leading H1 via `stripTitle`, parses
with **`marked`** (`marked.parse(raw, { async: false })`, GFM enabled),
rewrites `language-mermaid` fences into `<div class="mermaid">` blocks, then
sanitizes with **`dompurify`** (allowing `input` + `checked`/`disabled`/`type`
for GFM task lists). `MarkdownProse.vue` wraps the renderer in a `computed` and
emits via `v-html` into a scoped `.prose` block. Note: mermaid markup is
produced but no mermaid runtime is wired in this worktree.

Pure note helpers (`extractTitle`, `stripTitle`, `plainPreview`, `wordCount`,
`readingTime`, `allTags`, `relTime`, `groupByTime`) live in
`ui/src/features/notes/noteMockHelpers.ts`.

### Notes data — backend API for list and mutations

The notes list is fetched from the backend via `GET /notes/`: the
`useNotes` composable (`features/notes/useNotes.ts`, a module-singleton
mirroring `useAuth`) calls `services/notes.ts` `listNotes()` on
`fetchNotes()` and maps each `NoteDTO` into `NoteMock` (ISO timestamps ->
epoch ms; backend-normalized `tags` copied from `NoteResponse`).
`AppShell.vue` calls `useNotes()` and `fetchNotes()` on mount and passes
`loading`/`error` to `SidebarDrawer.vue`, which emits `retry` to refetch.
Create, content update, delete, and tag add/remove use the `createNote()`,
`updateNote()`, and `deleteNote()` wrappers in `useNotes`; tag edits send the
full replacement tag set through `PUT /notes/{note_id}`. Selection,
search/tag filters, copy, and single-note export remain local browser state
or clipboard/Blob actions. The `features/notes/mockNotes.ts` module now only
provides the `NoteMock` type and an in-memory seed used outside the live list
path.

### Design system (DTCG tokens + Ds* components)

Design tokens are authored as W3C DTCG JSON under
`ui/src/design-system/tokens/` (`primitives.json`, `semantic.json` light,
`semantic.dark.json` dark overrides) and compiled to CSS via
`npm run build:tokens` (`node src/design-system/tokens/build.mjs`, using
**style-dictionary**). The build emits the generated
`design-system/tokens.css` (`:root` light + `[data-theme="dark"]` dark) — do
not edit that file by hand. `main.ts` imports `tokens.css` then `base.css`.

Reusable primitives are the `Ds*` SFCs (`DsMenu.vue`, `DsSegment.vue`,
`DsToolButton.vue`). Icons are hand-authored SVGs via a `createIcon()` factory
in `design-system/icons/index.ts` (`defineComponent` + render-function
`h("svg", …)`) — there is no icon library dependency.

## Backend (FastAPI + SQLAlchemy)

### Async Session

```python
from app.database.database import get_async_db

async def my_endpoint(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Model))
    return result.scalars().all()
```

## Code Style

### TypeScript / Vue
- Strong typing — avoid `any`
- SFCs with `<script setup lang="ts">`; composables for shared logic
- Style with design-system tokens / `Ds*` components and scoped SFC CSS
- Lint/format is `vue-tsc --noEmit` + Prettier (no ESLint); tests use Vitest + `@vue/test-utils` (no React Testing Library)

### Python
- Type hints where beneficial
- Ruff for lint + format
- 120-char line length
