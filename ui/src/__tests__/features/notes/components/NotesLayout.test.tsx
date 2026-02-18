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
    useParams: vi.fn(),
  };
});

const mockOpenPalette = vi.fn();

// Mock UI store
vi.mock('../../../../store', () => ({
  useUIStore: vi.fn((selector) => {
    const state = {
      notesSortBy: 'lastModified',
      notesSearchQuery: '',
      notesGroupByDate: true,
      isPaletteOpen: false,
      paletteSearchQuery: '',
      actions: {
        openPalette: mockOpenPalette,
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
  default: () => (
    <header data-testid="header">
      <span>Notes</span>
    </header>
  ),
}));

vi.mock('../../../../features/ui/components/CommandPalette', () => ({
  CommandPalette: () => <div data-testid="command-palette" />,
}));

const mockNotes = [
  {
    id: 'note-1',
    title: 'First Note',
    content: '# First Note\n\nContent',
    createdAt: '2026-01-29T10:00:00Z',
    updatedAt: '2026-01-29T10:00:00Z',
  },
  {
    id: 'note-2',
    title: 'Second Note',
    content: '# Second Note\n\nMore content',
    createdAt: '2026-01-29T09:00:00Z',
    updatedAt: '2026-01-29T09:00:00Z',
  },
];

describe('NotesLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(routerDom.useLoaderData).mockReturnValue({ notes: mockNotes });
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

  it('renders header', async () => {
    await renderComponent();
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('mounts command palette', async () => {
    await renderComponent();
    expect(screen.getByTestId('command-palette')).toBeInTheDocument();
  });

  it('shows empty state with palette hint when no noteId', async () => {
    await renderComponent();
    expect(
      screen.getByText('Press Ctrl+Shift+Space to search notes')
    ).toBeInTheDocument();
    expect(screen.getByText('2 notes available')).toBeInTheDocument();
  });

  it('auto-opens palette when no noteId selected', async () => {
    await renderComponent();
    expect(mockOpenPalette).toHaveBeenCalled();
  });

  it('does not auto-open palette when noteId is present', async () => {
    await renderComponent('note-1');
    expect(mockOpenPalette).not.toHaveBeenCalled();
  });

  it('renders Outlet for child routes when noteId present', async () => {
    await renderComponent('note-1');
    expect(
      screen.queryByText('Press Ctrl+Shift+Space to search notes')
    ).not.toBeInTheDocument();
  });

  it('renders full-width layout without sidebar', async () => {
    await renderComponent();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
  });
});
