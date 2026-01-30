// ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';

// Mock UI store
vi.mock('../../../../store', () => ({
  useUIStore: vi.fn((selector) => {
    const state = {
      isSidebarOpen: true,
      notesSortBy: 'lastModified',
      notesSearchQuery: '',
      notesGroupByDate: true,
      actions: {
        toggleSidebar: vi.fn(),
        setNotesSortBy: vi.fn(),
        setNotesSearchQuery: vi.fn(),
        setNotesGroupByDate: vi.fn(),
      },
    };
    return selector ? selector(state) : state;
  }),
}));

// Mock Header component
vi.mock('../../../../features/ui/components/Header', () => ({
  default: ({ toggleSidebar }: { toggleSidebar: () => void }) => (
    <header data-testid="header">
      <span>Notes</span>
      <button onClick={toggleSidebar}>Toggle</button>
    </header>
  ),
}));

// Mock Sidebar component
vi.mock('../../../../features/ui/components/Sidebar', () => ({
  default: ({
    notes,
    currentNoteId,
  }: {
    notes: Array<{ id: string; title: string }>;
    currentNoteId: string;
  }) => (
    <nav data-testid="sidebar">
      {notes.map((note) => (
        <div
          key={note.id}
          data-testid={`note-item-${note.id}`}
          data-selected={note.id === currentNoteId}
        >
          {note.title}
        </div>
      ))}
    </nav>
  ),
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
  return import('../../../../features/notes/components/NotesLayout').then(
    ({ default: NotesLayout }) => {
      const router = createMemoryRouter(
        [
          {
            path: '/notes',
            element: <NotesLayout />,
            loader: () => ({ notes: mockNotes }),
            children: [
              { index: true, element: null },
              {
                path: ':noteId',
                element: <div data-testid="note-content">Note Content</div>,
              },
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

  it('renders sidebar when isSidebarOpen is true', async () => {
    await renderWithRouter();

    await waitFor(() => {
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    });
  });

  it('renders child routes via Outlet', async () => {
    await renderWithRouter(['/notes/note-1']);

    await waitFor(() => {
      expect(screen.getByTestId('note-content')).toBeInTheDocument();
    });
  });
});
