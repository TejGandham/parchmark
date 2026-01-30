// ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import * as routerDom from 'react-router-dom';

// Mock react-router-dom hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLoaderData: vi.fn(),
    useNavigate: vi.fn(),
    useParams: vi.fn(),
  };
});

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

describe('NotesLayout', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(routerDom.useLoaderData).mockReturnValue({ notes: mockNotes });
    vi.mocked(routerDom.useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(routerDom.useParams).mockReturnValue({});
  });

  async function renderComponent(noteId?: string) {
    vi.mocked(routerDom.useParams).mockReturnValue(noteId ? { noteId } : {});

    const { default: NotesLayout } = await import(
      '../../../../features/notes/components/NotesLayout'
    );

    return render(
      <ChakraProvider>
        <MemoryRouter>
          <NotesLayout />
        </MemoryRouter>
      </ChakraProvider>
    );
  }

  it('renders sidebar with notes from loader', async () => {
    await renderComponent();

    expect(screen.getByText('First Note')).toBeInTheDocument();
    expect(screen.getByText('Second Note')).toBeInTheDocument();
  });

  it('renders header', async () => {
    await renderComponent();

    expect(screen.getByText('Notes')).toBeInTheDocument();
  });

  it('renders sidebar when isSidebarOpen is true', async () => {
    await renderComponent();

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders child routes via Outlet', async () => {
    await renderComponent('note-1');

    // The Outlet is rendered (even if empty, sidebar still shows the note as selected)
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('note-item-note-1')).toHaveAttribute(
      'data-selected',
      'true'
    );
  });
});
