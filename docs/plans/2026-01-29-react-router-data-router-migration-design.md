# React Router Data Router Migration Design

**Date:** 2026-01-29
**Status:** Draft
**Related Issue:** [#47 - TanStack Query for Server State Management](https://github.com/TejGandham/parchmark/issues/47)

## Context

Issue #47 proposed adopting TanStack Query to replace manual server state management in Zustand. During design exploration, we discovered that React Router v7 (already installed) provides similar benefits through its data router pattern with loaders and actions.

The current codebase uses React Router's legacy JSX pattern (`<Routes>`/`<Route>`), but v7 recommends the data router pattern (`createBrowserRouter`). Migrating to data router:

1. Modernizes the router to the v7 recommended approach
2. Provides data fetching/caching via loaders (no new dependency)
3. Auto-revalidates after mutations via actions
4. Future-proofs for React 19 and React Router's direction

## Decision

Migrate from JSX routes to React Router data router instead of adding TanStack Query.

**Rationale:**
- Zero new dependencies (vs 12KB gzip for TanStack Query)
- Aligns with idiomatic React Router v7 patterns
- Solves the same problems: loading states, caching, mutation handling
- Simpler mental model: router owns server state, Zustand owns client state

## Architecture

### Final State

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Router Data Router                    │
├─────────────────────────────────────────────────────────────────┤
│  Loaders (fetch before render)    Actions (mutations)           │
│  ├─ /notes → getNotes()           ├─ POST /notes → create       │
│  ├─ /settings → getUserInfo()     ├─ POST /notes/:id → update   │
│                                   ├─ POST /notes/:id/delete     │
├─────────────────────────────────────────────────────────────────┤
│                        Zustand (client state only)              │
│  ├─ useAuthStore: tokens, isAuthenticated, login/logout         │
│  ├─ useUIStore: sidebar, sort, search, groupByDate              │
│  └─ useNotesUIStore: editedContent (unsaved changes)            │
└─────────────────────────────────────────────────────────────────┘
```

### Why Auth Stays in Zustand

Auth tokens require synchronous access via `getState()` for the API client's request interceptor. TanStack Query and React Router loaders are async/hook-based. The existing auth store handles:
- Token persistence via Zustand persist middleware
- OIDC redirects and silent refresh
- Promise deduplication for token refresh
- 401 retry logic in `api.ts`

These imperative flows are better suited for a Zustand store than declarative loaders/actions.

## Route Structure

```tsx
// ui/src/router.tsx
import { createBrowserRouter, redirect } from 'react-router';
import * as api from './services/api';
import { useAuthStore } from './features/auth/store';

const requireAuth = async () => {
  const { isAuthenticated } = useAuthStore.getState();
  if (!isAuthenticated) {
    throw redirect('/login');
  }
  return null;
};

export const router = createBrowserRouter([
  {
    path: '/',
    loader: () => {
      const { isAuthenticated } = useAuthStore.getState();
      return redirect(isAuthenticated ? '/notes' : '/login');
    },
  },
  {
    path: '/login',
    lazy: () => import('./features/auth/components/LoginForm'),
  },
  {
    path: '/oidc/callback',
    lazy: () => import('./features/auth/components/OIDCCallback'),
  },
  {
    path: '/notes',
    loader: async () => {
      await requireAuth();
      const notes = await api.getNotes();
      return { notes };
    },
    action: createNoteAction,
    lazy: () => import('./features/notes/components/NotesLayout'),
    errorElement: <RouteError />,
    children: [
      {
        index: true,
        element: null,
      },
      {
        path: ':noteId',
        action: updateNoteAction,
        lazy: () => import('./features/notes/components/NoteContent'),
        errorElement: <RouteError />,
        children: [
          {
            path: 'delete',
            action: deleteNoteAction,
          },
        ],
      },
    ],
  },
  {
    path: '/settings',
    loader: requireAuth,
    lazy: () => import('./features/settings/components/Settings'),
  },
  {
    path: '*',
    lazy: () => import('./features/ui/components/NotFoundPage'),
  },
]);
```

## Actions (Mutations)

```tsx
// ui/src/features/notes/actions.ts
import { redirect } from 'react-router';
import * as api from '../../../services/api';
import {
  extractTitleFromMarkdown,
  formatNoteContent,
  createEmptyNoteContent,
} from '../../../services/markdownService';

export async function createNoteAction() {
  const content = createEmptyNoteContent();
  const title = extractTitleFromMarkdown(content);
  const newNote = await api.createNote({ title, content });
  return redirect(`/notes/${newNote.id}?editing=true`);
}

export async function updateNoteAction({ request, params }) {
  const formData = await request.formData();
  const content = formData.get('content') as string;
  const formattedContent = formatNoteContent(content);

  await api.updateNote(params.noteId, { content: formattedContent });
  return { ok: true };  // Triggers revalidation of parent loader
}

export async function deleteNoteAction({ params }) {
  await api.deleteNote(params.noteId);
  return redirect('/notes');
}
```

## Component Changes

### NotesLayout (New)

Replaces `NotesContainer`. Handles sidebar + content layout:

```tsx
// ui/src/features/notes/components/NotesLayout.tsx
import { Outlet, useLoaderData, useNavigate, useParams } from 'react-router';
import { useEffect } from 'react';
import { Box, Flex } from '@chakra-ui/react';
import { useUIStore } from '../../../store';
import Header from '../../ui/components/Header';
import Sidebar from '../../ui/components/Sidebar';
import { Note } from '../../../types';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();
  const navigate = useNavigate();

  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const toggleSidebar = useUIStore((s) => s.actions.toggleSidebar);

  useEffect(() => {
    if (!noteId && notes.length > 0) {
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [noteId, notes, navigate]);

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      <Flex h="100vh" flexDirection="column">
        <Header toggleSidebar={toggleSidebar} />
        <Flex flex="1" overflow="hidden">
          {isSidebarOpen && (
            <Sidebar
              notes={notes}
              currentNoteId={noteId || ''}
              onSelectNote={(id) => navigate(`/notes/${id}`)}
              onCreateNote={() => {/* handled by action */}}
              onDeleteNote={(id) => {/* handled by action */}}
              isLoading={false}
            />
          )}
          <Box as="main" flex="1" p={6} overflowY="auto">
            <Outlet />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
}
```

### Sidebar Mutations

```tsx
// Create button using useFetcher
import { useFetcher } from 'react-router';

function CreateButton() {
  const fetcher = useFetcher();
  return (
    <fetcher.Form method="post" action="/notes">
      <Button type="submit" isLoading={fetcher.state !== 'idle'}>
        New Note
      </Button>
    </fetcher.Form>
  );
}

// Delete button
function DeleteButton({ noteId }) {
  const fetcher = useFetcher();
  return (
    <fetcher.Form method="post" action={`/notes/${noteId}/delete`}>
      <Button type="submit">Delete</Button>
    </fetcher.Form>
  );
}
```

## Zustand Store Changes

### useNotesStore → useNotesUIStore

Only client UI state remains:

```tsx
// ui/src/features/notes/store/notes.ts
import { create } from 'zustand';

type NotesUIState = {
  editedContent: string | null;
  setEditedContent: (content: string | null) => void;
};

export const useNotesUIStore = create<NotesUIState>((set) => ({
  editedContent: null,
  setEditedContent: (content) => set({ editedContent: content }),
}));
```

**Deleted from notes store:**
- `notes: Note[]` → `useLoaderData()`
- `currentNoteId` → `useParams().noteId`
- `isLoading` → loader resolves before render
- `error` → route `errorElement`
- All actions (fetchNotes, createNote, updateNote, deleteNote)

## Error Handling

```tsx
// ui/src/features/ui/components/RouteError.tsx
import { useRouteError, isRouteErrorResponse, Link } from 'react-router';
import { Box, Heading, Text, Button, Center } from '@chakra-ui/react';

export default function RouteError() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    if (error.status === 401) {
      return (
        <Center h="100vh">
          <Box textAlign="center">
            <Heading>Session Expired</Heading>
            <Button as={Link} to="/login" mt={4}>Log In</Button>
          </Box>
        </Center>
      );
    }

    return (
      <Center h="100vh">
        <Box textAlign="center">
          <Heading>{error.status}</Heading>
          <Text>{error.statusText}</Text>
        </Box>
      </Center>
    );
  }

  return (
    <Center h="100vh">
      <Box textAlign="center">
        <Heading>Something went wrong</Heading>
        <Text>{error instanceof Error ? error.message : 'Unknown error'}</Text>
        <Button as={Link} to="/notes" mt={4}>Back to Notes</Button>
      </Box>
    </Center>
  );
}
```

## Testing Strategy

Use `createMemoryRouter` with mock loaders:

```tsx
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import NotesLayout from '../NotesLayout';

const mockNotes = [
  { id: '1', title: 'Note 1', content: '# Note 1', created_at: '...', updated_at: '...' },
];

function renderWithRouter(initialEntries = ['/notes']) {
  const router = createMemoryRouter(
    [
      {
        path: '/notes',
        element: <NotesLayout />,
        loader: () => ({ notes: mockNotes }),
        children: [
          { path: ':noteId', element: <div>Note Content</div> },
        ],
      },
    ],
    { initialEntries }
  );

  return render(<RouterProvider router={router} />);
}

test('renders notes list from loader', async () => {
  renderWithRouter();
  expect(await screen.findByText('Note 1')).toBeInTheDocument();
});
```

## File Changes

### Files to Create

| File | Purpose |
|------|---------|
| `ui/src/router.tsx` | Route config with loaders/actions |
| `ui/src/features/notes/components/NotesLayout.tsx` | Layout with sidebar |
| `ui/src/features/notes/actions.ts` | Create/update/delete actions |
| `ui/src/features/ui/components/RouteError.tsx` | Error boundary |

### Files to Modify

| File | Change |
|------|--------|
| `ui/src/App.tsx` | Replace `<Routes>` with `<RouterProvider>` |
| `ui/src/main.tsx` | May need adjustment for router setup |
| `ui/src/features/notes/store/notes.ts` | Keep only `editedContent` |
| `ui/src/features/notes/components/NoteContent.tsx` | Use `useLoaderData`, `useFetcher` |
| `ui/src/features/ui/components/Sidebar.tsx` | Use `useFetcher` for create/delete |
| `ui/src/store/index.ts` | Export renamed store |

### Files to Delete

| File | Reason |
|------|--------|
| `ui/src/features/notes/hooks/useStoreRouterSync.ts` | Router is source of truth |
| `ui/src/features/auth/components/ProtectedRoute.tsx` | Auth check moved to loaders |
| `ui/src/__tests__/features/notes/hooks/useStoreRouterSync.test.tsx` | Hook deleted |
| `ui/src/__tests__/features/auth/components/ProtectedRoute.test.tsx` | Component deleted |

## Impact Summary

| Metric | Change |
|--------|--------|
| Lines deleted | ~220 (store actions, sync hook, ProtectedRoute) |
| Lines added | ~150 (router config, actions, error boundary, layout) |
| New dependencies | 0 |
| Bundle size | Neutral (same React Router, less Zustand usage) |

## Implementation Order

1. Create `router.tsx` with basic route config (no loaders yet)
2. Update `App.tsx` to use `RouterProvider`
3. Add loaders for `/notes` route
4. Create `NotesLayout.tsx` consuming loader data
5. Add actions for create/update/delete
6. Update `Sidebar.tsx` and `NoteContent.tsx` to use `useFetcher`
7. Simplify `useNotesStore` to `useNotesUIStore`
8. Delete `useStoreRouterSync.ts` and `ProtectedRoute.tsx`
9. Update tests
10. Delete old test files

## Open Questions

1. **Settings page:** Should `/settings` also use loaders for `getUserInfo()`? (Yes, recommended)
2. **Optimistic updates:** Do we need optimistic UI for note updates, or is revalidation fast enough?
3. **Pending UI:** Should we show loading indicators during navigation/mutations using `useNavigation()`?

## References

- [React Router v7 Data Router docs](https://reactrouter.com/en/main/routers/create-browser-router)
- [Original issue #47](https://github.com/TejGandham/parchmark/issues/47)
- Consultation with Gemini and Codex via zen workflow
