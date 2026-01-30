# React Router Data Router Migration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from React Router JSX routes to data router pattern for server state management.

**Architecture:** Replace Zustand's server state (notes fetching/mutations) with React Router loaders and actions. Keep Zustand for client-only state (auth tokens, UI preferences, edit buffer).

**Tech Stack:** React Router v7, Zustand, TypeScript, Chakra UI, Vitest

---

## Task 1: Create Route Error Boundary

**Files:**
- Create: `ui/src/features/ui/components/RouteError.tsx`
- Test: `ui/src/__tests__/features/ui/components/RouteError.test.tsx`

**Step 1: Write the test file**

```tsx
// ui/src/__tests__/features/ui/components/RouteError.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';

// We'll test RouteError by triggering actual route errors
describe('RouteError', () => {
  it('renders 401 error with login link', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Response('Unauthorized', { status: 401 });
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('Session Expired')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /log in/i })).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('renders generic HTTP error', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Response('Not Found', { status: 404, statusText: 'Not Found' });
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('404')).toBeInTheDocument();
    expect(screen.getByText('Not Found')).toBeInTheDocument();
  });

  it('renders thrown Error', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Error('Something broke');
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- ui/src/__tests__/features/ui/components/RouteError.test.tsx`

Expected: FAIL - module not found

**Step 3: Create RouteError component**

```tsx
// ui/src/features/ui/components/RouteError.tsx
import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { Box, Heading, Text, Button, Center, VStack } from '@chakra-ui/react';

export default function RouteError() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    if (error.status === 401) {
      return (
        <Center h="100vh" bg="bg.canvas">
          <VStack spacing={4}>
            <Heading size="lg" fontFamily="'Playfair Display', serif">
              Session Expired
            </Heading>
            <Text color="text.muted">Please log in again to continue.</Text>
            <Button as={Link} to="/login" colorScheme="primary">
              Log In
            </Button>
          </VStack>
        </Center>
      );
    }

    return (
      <Center h="100vh" bg="bg.canvas">
        <VStack spacing={4}>
          <Heading size="2xl" color="text.muted">
            {error.status}
          </Heading>
          <Text fontSize="lg" color="text.secondary">
            {error.statusText}
          </Text>
          <Button as={Link} to="/notes" colorScheme="primary" mt={4}>
            Back to Notes
          </Button>
        </VStack>
      </Center>
    );
  }

  return (
    <Center h="100vh" bg="bg.canvas">
      <VStack spacing={4}>
        <Heading size="lg" fontFamily="'Playfair Display', serif">
          Something went wrong
        </Heading>
        <Text color="text.muted">
          {error instanceof Error ? error.message : 'Unknown error'}
        </Text>
        <Button as={Link} to="/notes" colorScheme="primary" mt={4}>
          Back to Notes
        </Button>
      </VStack>
    </Center>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- ui/src/__tests__/features/ui/components/RouteError.test.tsx`

Expected: PASS

**Step 5: Commit**

```
git add ui/src/features/ui/components/RouteError.tsx ui/src/__tests__/features/ui/components/RouteError.test.tsx
git commit -m "feat: add RouteError boundary for data router"
```

---

## Task 2: Create Notes Actions

**Files:**
- Create: `ui/src/features/notes/actions.ts`
- Test: `ui/src/__tests__/features/notes/actions.test.ts`

**Step 1: Write the test file**

```tsx
// ui/src/__tests__/features/notes/actions.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { redirect } from 'react-router-dom';

// Mock the API
vi.mock('../../services/api', () => ({
  createNote: vi.fn(),
  updateNote: vi.fn(),
  deleteNote: vi.fn(),
}));

// Mock react-router-dom redirect
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    redirect: vi.fn((path) => ({ type: 'redirect', path })),
  };
});

describe('notes actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createNoteAction', () => {
    it('creates note and redirects with editing flag', async () => {
      const { createNote } = await import('../../services/api');
      const { createNoteAction } = await import(
        '../../features/notes/actions'
      );

      (createNote as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'new-note-123',
        title: 'Untitled',
        content: '# Untitled\n\n',
      });

      const result = await createNoteAction();

      expect(createNote).toHaveBeenCalledWith({
        title: 'Untitled',
        content: '# Untitled\n\n',
      });
      expect(redirect).toHaveBeenCalledWith('/notes/new-note-123?editing=true');
    });
  });

  describe('updateNoteAction', () => {
    it('updates note and returns success', async () => {
      const { updateNote } = await import('../../services/api');
      const { updateNoteAction } = await import(
        '../../features/notes/actions'
      );

      (updateNote as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'note-123',
        title: 'Updated Title',
        content: '# Updated Title\n\nContent here',
      });

      const formData = new FormData();
      formData.append('content', '# Updated Title\n\nContent here');

      const request = new Request('http://localhost/notes/note-123', {
        method: 'POST',
        body: formData,
      });

      const result = await updateNoteAction({
        request,
        params: { noteId: 'note-123' },
      });

      expect(updateNote).toHaveBeenCalledWith('note-123', {
        content: '# Updated Title\n\nContent here',
      });
      expect(result).toEqual({ ok: true });
    });
  });

  describe('deleteNoteAction', () => {
    it('deletes note and redirects to /notes', async () => {
      const { deleteNote } = await import('../../services/api');
      const { deleteNoteAction } = await import(
        '../../features/notes/actions'
      );

      (deleteNote as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

      await deleteNoteAction({ params: { noteId: 'note-123' } });

      expect(deleteNote).toHaveBeenCalledWith('note-123');
      expect(redirect).toHaveBeenCalledWith('/notes');
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- ui/src/__tests__/features/notes/actions.test.ts`

Expected: FAIL - module not found

**Step 3: Create actions file**

```tsx
// ui/src/features/notes/actions.ts
import { redirect, ActionFunctionArgs } from 'react-router-dom';
import * as api from '../../services/api';
import {
  extractTitleFromMarkdown,
  formatNoteContent,
  createEmptyNoteContent,
} from '../../services/markdownService';

export async function createNoteAction() {
  const content = createEmptyNoteContent();
  const title = extractTitleFromMarkdown(content);
  const newNote = await api.createNote({ title, content });
  return redirect(`/notes/${newNote.id}?editing=true`);
}

export async function updateNoteAction({ request, params }: ActionFunctionArgs) {
  const formData = await request.formData();
  const content = formData.get('content') as string;
  const formattedContent = formatNoteContent(content);

  await api.updateNote(params.noteId!, { content: formattedContent });
  return { ok: true };
}

export async function deleteNoteAction({ params }: ActionFunctionArgs) {
  await api.deleteNote(params.noteId!);
  return redirect('/notes');
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- ui/src/__tests__/features/notes/actions.test.ts`

Expected: PASS

**Step 5: Commit**

```
git add ui/src/features/notes/actions.ts ui/src/__tests__/features/notes/actions.test.ts
git commit -m "feat: add notes actions for data router mutations"
```

---

## Task 3: Create Router Configuration

**Files:**
- Create: `ui/src/router.tsx`
- Test: `ui/src/__tests__/router.test.tsx`

**Step 1: Write the test file**

```tsx
// ui/src/__tests__/router.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';

// Mock auth store
vi.mock('../features/auth/store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ isAuthenticated: false })),
  },
}));

// Mock API
vi.mock('../services/api', () => ({
  getNotes: vi.fn().mockResolvedValue([]),
}));

describe('router', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects unauthenticated users from /notes to /login', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: false,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/notes'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });

  it('redirects root to /login when unauthenticated', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: false,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });

  it('redirects root to /notes when authenticated', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/notes');
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- ui/src/__tests__/router.test.tsx`

Expected: FAIL - module not found

**Step 3: Create router configuration**

```tsx
// ui/src/router.tsx
import { createBrowserRouter, redirect, RouteObject } from 'react-router-dom';
import * as api from './services/api';
import { useAuthStore } from './features/auth/store';
import { createNoteAction, updateNoteAction, deleteNoteAction } from './features/notes/actions';
import RouteError from './features/ui/components/RouteError';

const requireAuth = async () => {
  const { isAuthenticated } = useAuthStore.getState();
  if (!isAuthenticated) {
    throw redirect('/login');
  }
  return null;
};

export const routes: RouteObject[] = [
  {
    path: '/',
    loader: () => {
      const { isAuthenticated } = useAuthStore.getState();
      return redirect(isAuthenticated ? '/notes' : '/login');
    },
  },
  {
    path: '/login',
    lazy: async () => {
      const { default: Component } = await import('./features/auth/components/LoginForm');
      return { Component };
    },
  },
  {
    path: '/oidc/callback',
    lazy: async () => {
      const { default: Component } = await import('./features/auth/components/OIDCCallback');
      return { Component };
    },
  },
  {
    id: 'notes-layout',
    path: '/notes',
    loader: async () => {
      await requireAuth();
      const notes = await api.getNotes();
      return { notes };
    },
    action: createNoteAction,
    lazy: async () => {
      const { default: Component } = await import('./features/notes/components/NotesLayout');
      return { Component };
    },
    errorElement: <RouteError />,
    children: [
      {
        index: true,
        element: null,
      },
      {
        path: ':noteId',
        action: updateNoteAction,
        lazy: async () => {
          const { default: Component } = await import('./features/notes/components/NoteContent');
          return { Component };
        },
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
    lazy: async () => {
      const { default: Component } = await import('./features/settings/components/Settings');
      return { Component };
    },
  },
  {
    path: '*',
    lazy: async () => {
      const { default: Component } = await import('./features/ui/components/NotFoundPage');
      return { Component };
    },
  },
];

export const router = createBrowserRouter(routes);
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- ui/src/__tests__/router.test.tsx`

Expected: PASS

**Step 5: Commit**

```
git add ui/src/router.tsx ui/src/__tests__/router.test.tsx
git commit -m "feat: add data router configuration with loaders and actions"
```

---

## Task 4: Create NotesLayout Component

**Files:**
- Create: `ui/src/features/notes/components/NotesLayout.tsx`
- Test: `ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`

**Step 1: Write the test file**

```tsx
// ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';

// Mock UI store
vi.mock('../../../store', () => ({
  useUIStore: vi.fn((selector) => {
    const state = {
      isSidebarOpen: true,
      actions: { toggleSidebar: vi.fn() },
    };
    return selector ? selector(state) : state;
  }),
}));

const mockNotes = [
  {
    id: 'note-1',
    title: 'First Note',
    content: '# First Note\n\nContent',
    created_at: '2026-01-29T10:00:00Z',
    updated_at: '2026-01-29T10:00:00Z',
  },
  {
    id: 'note-2',
    title: 'Second Note',
    content: '# Second Note\n\nMore content',
    created_at: '2026-01-29T09:00:00Z',
    updated_at: '2026-01-29T09:00:00Z',
  },
];

function renderWithRouter(initialEntries = ['/notes']) {
  return import('../../../features/notes/components/NotesLayout').then(
    ({ default: NotesLayout }) => {
      const router = createMemoryRouter(
        [
          {
            path: '/notes',
            element: <NotesLayout />,
            loader: () => ({ notes: mockNotes }),
            children: [
              { index: true, element: null },
              { path: ':noteId', element: <div data-testid="note-content">Note Content</div> },
            ],
          },
        ],
        { initialEntries }
      );

      return render(
        <ChakraProvider>
          <RouterProvider router={router} />
        </ChakraProvider>
      );
    }
  );
}

describe('NotesLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sidebar with notes from loader', async () => {
    await renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText('First Note')).toBeInTheDocument();
      expect(screen.getByText('Second Note')).toBeInTheDocument();
    });
  });

  it('renders header', async () => {
    await renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText('Notes')).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`

Expected: FAIL - module not found

**Step 3: Create NotesLayout component**

```tsx
// ui/src/features/notes/components/NotesLayout.tsx
import { useEffect } from 'react';
import { Outlet, useLoaderData, useNavigate, useParams, Link } from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';
import { useUIStore } from '../../../store';
import Header from '../../ui/components/Header';
import Sidebar from '../../ui/components/Sidebar';
import { Note } from '../../../types';
import '../../ui/styles/layout.css';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();
  const navigate = useNavigate();

  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const toggleSidebar = useUIStore((s) => s.actions.toggleSidebar);

  // Redirect to first note if none selected
  useEffect(() => {
    if (!noteId && notes.length > 0) {
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [noteId, notes, navigate]);

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      {/* Skip to main content link for screen readers */}
      <Link
        to="#main-content"
        style={{
          position: 'absolute',
          left: '-9999px',
          zIndex: 9999,
        }}
      >
        Skip to main content
      </Link>

      <Flex h="100vh" flexDirection="column">
        <Header toggleSidebar={toggleSidebar} />

        <Flex flex="1" overflow="hidden">
          {isSidebarOpen && (
            <Box as="nav" aria-label="Notes navigation">
              <Sidebar
                notes={notes}
                currentNoteId={noteId || ''}
                onSelectNote={(id) => navigate(`/notes/${id}`)}
                onCreateNote={() => {
                  // Handled by form action in Sidebar
                }}
                onDeleteNote={() => {
                  // Handled by form action in Sidebar
                }}
                isLoading={false}
              />
            </Box>
          )}

          <Box
            as="main"
            id="main-content"
            flex="1"
            p={6}
            overflowY="auto"
            className="note-transition"
            aria-label="Note content"
          >
            <Outlet />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`

Expected: PASS

**Step 5: Commit**

```
git add ui/src/features/notes/components/NotesLayout.tsx ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
git commit -m "feat: add NotesLayout component for data router"
```

---

## Task 5: Simplify Notes Store

**Files:**
- Modify: `ui/src/features/notes/store/notes.ts`
- Modify: `ui/src/features/notes/store/index.ts`
- Modify: `ui/src/__tests__/features/notes/store/notes.test.ts`

**Step 1: Update test file**

```tsx
// ui/src/__tests__/features/notes/store/notes.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useNotesUIStore } from '../../../features/notes/store';

describe('useNotesUIStore', () => {
  beforeEach(() => {
    useNotesUIStore.setState({ editedContent: null });
  });

  it('should initialize with null editedContent', () => {
    const state = useNotesUIStore.getState();
    expect(state.editedContent).toBeNull();
  });

  it('should set editedContent', () => {
    const { setEditedContent } = useNotesUIStore.getState();
    setEditedContent('# New Content');
    expect(useNotesUIStore.getState().editedContent).toBe('# New Content');
  });

  it('should clear editedContent when set to null', () => {
    const { setEditedContent } = useNotesUIStore.getState();
    setEditedContent('# Some Content');
    setEditedContent(null);
    expect(useNotesUIStore.getState().editedContent).toBeNull();
  });
});
```

**Step 2: Simplify the notes store**

```tsx
// ui/src/features/notes/store/notes.ts
import { create } from 'zustand';

export type NotesUIState = {
  editedContent: string | null;
  setEditedContent: (content: string | null) => void;
};

export const useNotesUIStore = create<NotesUIState>((set) => ({
  editedContent: null,
  setEditedContent: (content) => set({ editedContent: content }),
}));

// Backward compatibility alias - remove after migration complete
export const useNotesStore = useNotesUIStore;
```

**Step 3: Update store barrel export**

```tsx
// ui/src/features/notes/store/index.ts
export { useNotesUIStore, useNotesStore } from './notes';
export type { NotesUIState } from './notes';
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- ui/src/__tests__/features/notes/store/notes.test.ts`

Expected: PASS

**Step 5: Commit**

```
git add ui/src/features/notes/store/notes.ts ui/src/features/notes/store/index.ts ui/src/__tests__/features/notes/store/notes.test.ts
git commit -m "refactor: simplify notes store to UI-only state"
```

---

## Task 6: Update App.tsx

**Files:**
- Modify: `ui/src/App.tsx`
- Modify: `ui/src/__tests__/App.test.tsx`

**Step 1: Update App.tsx**

```tsx
// ui/src/App.tsx
import { ChakraProvider } from '@chakra-ui/react';
import { RouterProvider } from 'react-router-dom';
import theme from './styles/theme';
import { router } from './router';
import { useTokenExpirationMonitor } from './features/auth/hooks/useTokenExpirationMonitor';

function App() {
  useTokenExpirationMonitor();

  return (
    <ChakraProvider theme={theme}>
      <RouterProvider router={router} />
    </ChakraProvider>
  );
}

export default App;
```

**Step 2: Update test file**

```tsx
// ui/src/__tests__/App.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('../router', () => ({
  router: {
    navigate: vi.fn(),
    state: { location: { pathname: '/login' } },
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    RouterProvider: () => <div data-testid="router-provider">Router Active</div>,
  };
});

vi.mock('../features/auth/hooks/useTokenExpirationMonitor', () => ({
  useTokenExpirationMonitor: vi.fn(),
}));

describe('App', () => {
  it('renders with RouterProvider', async () => {
    const { default: App } = await import('../App');
    render(<App />);
    expect(screen.getByTestId('router-provider')).toBeInTheDocument();
  });
});
```

**Step 3: Run test**

Run: `npm run test -- ui/src/__tests__/App.test.tsx`

Expected: PASS

**Step 4: Commit**

```
git add ui/src/App.tsx ui/src/__tests__/App.test.tsx
git commit -m "refactor: replace Routes with RouterProvider in App.tsx"
```

---

## Task 7: Update NoteContent for Data Router

**Files:**
- Modify: `ui/src/features/notes/components/NoteContent.tsx`
- Modify: `ui/src/features/notes/components/NoteActions.tsx` (add isSaving prop)

This is the most complex task. NoteContent needs to:
- Use `useRouteLoaderData('notes-layout')` to get notes
- Use `useParams()` to get noteId
- Use `useFetcher` for save/create operations
- Use URL search params for `?editing=true`

See design document for full implementation.

**Step 1: Implement changes per design document**

**Step 2: Run tests and fix failures**

Run: `npm run test`

**Step 3: Commit**

```
git add ui/src/features/notes/components/NoteContent.tsx ui/src/features/notes/components/NoteActions.tsx
git commit -m "refactor: update NoteContent to use data router hooks"
```

---

## Task 8: Update Sidebar for Data Router Actions

**Files:**
- Modify: `ui/src/features/ui/components/Sidebar.tsx`

Update Sidebar to use `useFetcher` for create/delete operations.

**Step 1: Import useFetcher and update create/delete handlers**

**Step 2: Run tests**

Run: `npm run test -- ui/src/__tests__/features/ui/components/Sidebar.test.tsx`

**Step 3: Commit**

```
git add ui/src/features/ui/components/Sidebar.tsx
git commit -m "refactor: update Sidebar to use data router actions"
```

---

## Task 9: Delete Obsolete Files

**Files to delete:**
- `ui/src/features/notes/hooks/useStoreRouterSync.ts`
- `ui/src/features/auth/components/ProtectedRoute.tsx`
- `ui/src/__tests__/features/notes/hooks/useStoreRouterSync.test.tsx`
- `ui/src/__tests__/features/auth/components/ProtectedRoute.test.tsx`

**Step 1: Remove files**

```
rm ui/src/features/notes/hooks/useStoreRouterSync.ts
rm ui/src/features/auth/components/ProtectedRoute.tsx
rm -rf ui/src/__tests__/features/notes/hooks/
rm ui/src/__tests__/features/auth/components/ProtectedRoute.test.tsx
```

**Step 2: Remove any remaining imports**

Search and remove imports referencing deleted files.

**Step 3: Run tests**

Run: `npm run test`

**Step 4: Commit**

```
git add -A
git commit -m "chore: remove obsolete files replaced by data router"
```

---

## Task 10: Fix Remaining Test Failures

**Step 1: Run full test suite**

Run: `make test-ui-all`

**Step 2: Fix failures**

Common issues:
- Tests mocking old store structure
- Tests expecting old component props
- Tests using old router setup

**Step 3: Commit fixes**

```
git add -A
git commit -m "test: fix tests for data router migration"
```

---

## Task 11: Manual Testing

**Step 1: Start dev server**

Run: `make dev`

**Step 2: Test flows**

1. Visit http://localhost:5173 - should redirect to /login
2. Log in - should redirect to /notes
3. Create note - should create and enter edit mode
4. Edit and save - should persist
5. Delete note - should remove and redirect
6. Navigate between notes
7. Refresh page on /notes/:id

**Step 3: Create issues for bugs found**

```
bd create --title="Bug: [description]" --type=bug --priority=2
```

---

## Task 12: Final Cleanup and Push

**Step 1: Run final tests**

Run: `make test`

**Step 2: Push branch**

```
git push -u origin feature/react-router-data-router
```

---

## Summary

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Create RouteError boundary | Low |
| 2 | Create notes actions | Low |
| 3 | Create router configuration | Medium |
| 4 | Create NotesLayout | Medium |
| 5 | Simplify notes store | Low |
| 6 | Update App.tsx | Low |
| 7 | Update NoteContent | High |
| 8 | Update Sidebar | Medium |
| 9 | Delete obsolete files | Low |
| 10 | Fix test failures | Medium |
| 11 | Manual testing | Medium |
| 12 | Final cleanup | Low |
