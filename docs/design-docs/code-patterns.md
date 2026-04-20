# Code Patterns

Concrete conventions for parchmark's frontend and backend. Consult when writing new code so it matches existing shape.

## Frontend (React + TypeScript)

### Error Handling

```typescript
import { handleError } from '../utils/errorHandler';
const appError = handleError(error);  // normalizes all error types
```

### Type-Safe Constants

```typescript
import { API_ENDPOINTS } from '../config/api';
import { STORAGE_KEYS } from '../config/storage';
```

Never hard-code endpoints or storage keys.

### Markdown Processing

`ui/src/utils/markdown.ts` (frontend) and `backend/app/utils/markdown.py` (backend) must stay in sync — use the `parchmark-markdown-sync` skill after editing either.

```typescript
markdownService.extractTitle(content)   // get H1 title
markdownService.removeH1(content)       // remove FIRST H1 only (not all)
```

### Zustand Stores

```typescript
useAuthStore      // auth state, login/logout
useNotesUIStore   // editor draft content (ephemeral)
useUIStore        // command palette state, preferences
```

### React Router v7 (Data Router)

Loaders fetch before render; actions handle mutations via `useFetcher().submit()`.

```typescript
// ui/src/router.tsx
loader: async () => {
  const notes = await api.getNotes();
  return { notes };
}

// ui/src/features/notes/actions.ts
action: createNoteAction

// In components
const { notes } = useRouteLoaderData('notes-layout');
```

Route protection uses `requireAuth()` loader in `router.tsx` — there is no `ProtectedRoute` component.

## Backend (FastAPI + SQLAlchemy)

### Async Session

```python
from app.database.database import get_async_db

async def my_endpoint(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Model))
    return result.scalars().all()
```

## Code Style

### TypeScript
- Strong typing — avoid `any`
- Functional components with hooks
- Chakra UI components; avoid inline styles

### Python
- Type hints where beneficial
- Ruff for lint + format
- 120-char line length
