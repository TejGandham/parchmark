// ui/src/__tests__/features/ui/components/SidebarDataRouter.test.tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import * as routerDom from 'react-router-dom';
import Sidebar from '../../../../features/ui/components/Sidebar';

// Mock router module
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
    useFetcher: vi.fn(),
  };
});

// Mock UI store
vi.mock('../../../../features/ui/store', () => ({
  useUIStore: vi.fn((selector) => {
    const state = {
      notesSortBy: 'lastModified' as const,
      notesSearchQuery: '',
      notesGroupByDate: false,
      actions: {
        setNotesSortBy: vi.fn(),
        setNotesSearchQuery: vi.fn(),
        setNotesGroupByDate: vi.fn(),
      },
    };
    return selector(state);
  }),
}));

// Mock NoteItem component
vi.mock('../../../../features/notes/components/NoteItem', () => ({
  default: ({
    note,
    isActive,
    onSelect,
    onDelete,
  }: {
    note: { id: string; title: string };
    isActive: boolean;
    onSelect: (id: string) => void;
    onDelete: (id: string) => void;
  }) => (
    <li data-testid={`note-item-${note.id}`}>
      <button
        onClick={() => onSelect(note.id)}
        aria-selected={isActive}
        data-testid={`select-${note.id}`}
      >
        {note.title}
      </button>
      <button
        onClick={() => onDelete(note.id)}
        data-testid={`delete-${note.id}`}
      >
        Delete
      </button>
    </li>
  ),
}));

// Mock NoteListSkeleton
vi.mock('../../../../components/NoteCardSkeleton', () => ({
  NoteListSkeleton: () => <div data-testid="note-skeleton">Loading...</div>,
}));

// Mock VirtualizedNotesList
vi.mock('../../../../components/VirtualizedNotesList', () => ({
  default: () => <div data-testid="virtualized-list">Virtualized</div>,
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

describe('Sidebar with Data Router', () => {
  const mockNavigate = vi.fn();
  const mockFetcherSubmit = vi.fn();

  function setupMocks() {
    vi.mocked(routerDom.useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(routerDom.useFetcher).mockReturnValue({
      submit: mockFetcherSubmit,
      state: 'idle',
      data: null,
    } as unknown as ReturnType<typeof routerDom.useFetcher>);
  }

  beforeEach(() => {
    vi.clearAllMocks();
    setupMocks();
  });

  afterEach(() => {
    cleanup();
  });

  function renderComponent(
    props: Partial<{ notes: typeof mockNotes; currentNoteId: string }> = {}
  ) {
    return render(
      <ChakraProvider>
        <Sidebar
          notes={props.notes ?? mockNotes}
          currentNoteId={props.currentNoteId ?? 'note-1'}
        />
      </ChakraProvider>
    );
  }

  describe('Note Selection', () => {
    it('renders notes from props', () => {
      renderComponent();
      expect(screen.getByText('First Note')).toBeInTheDocument();
      expect(screen.getByText('Second Note')).toBeInTheDocument();
    });

    it('navigates to note when selected', () => {
      renderComponent();
      fireEvent.click(screen.getByTestId('select-note-2'));
      expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
    });

    it('highlights current note', () => {
      renderComponent({ currentNoteId: 'note-1' });
      const selectButton = screen.getByTestId('select-note-1');
      expect(selectButton).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('Create Note', () => {
    it('submits create action when create button clicked', () => {
      renderComponent();
      const createButton = screen.getByRole('button', { name: /new note/i });
      fireEvent.click(createButton);
      expect(mockFetcherSubmit).toHaveBeenCalledWith(null, {
        method: 'post',
        action: '/notes',
      });
    });
  });

  describe('Delete Note', () => {
    it('submits delete action when delete button clicked', () => {
      renderComponent();
      fireEvent.click(screen.getByTestId('delete-note-1'));
      expect(mockFetcherSubmit).toHaveBeenCalledWith(null, {
        method: 'delete',
        action: '/notes/note-1',
      });
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no notes', () => {
      renderComponent({ notes: [] });
      expect(screen.getByText('No notes yet')).toBeInTheDocument();
    });

    it('create button in empty state submits action', () => {
      renderComponent({ notes: [] });
      const createButton = screen.getByRole('button', { name: /create note/i });
      fireEvent.click(createButton);
      expect(mockFetcherSubmit).toHaveBeenCalledWith(null, {
        method: 'post',
        action: '/notes',
      });
    });
  });

  describe('Loading State', () => {
    it('shows skeleton when loading', () => {
      render(
        <ChakraProvider>
          <Sidebar notes={[]} currentNoteId="" isLoading={true} />
        </ChakraProvider>
      );
      expect(screen.getByTestId('note-skeleton')).toBeInTheDocument();
    });
  });
});
