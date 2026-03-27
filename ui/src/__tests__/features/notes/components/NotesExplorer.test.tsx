import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { act } from 'react';
import { Note } from '../../../../types';
import { useUIStore } from '../../../../features/ui/store/ui';

const mockNavigate = vi.fn();
const mockRouteLoaderData = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useRouteLoaderData: (...args: unknown[]) => mockRouteLoaderData(...args),
  };
});

vi.mock('../../../../services/api', () => ({
  trackNoteAccess: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../../../utils/compactTime', () => ({
  formatCompactTime: vi.fn(() => '2d'),
}));

function makeNote(overrides: Partial<Note> & { id: string }): Note {
  return {
    title: `Note ${overrides.id}`,
    content: `# Note ${overrides.id}\n\nContent of note ${overrides.id} with some words here.`,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-02-16T12:00:00Z',
    ...overrides,
  };
}

const sampleNotes: Note[] = [
  makeNote({ id: '1', title: 'Alpha Note', updatedAt: '2026-02-16T12:00:00Z' }),
  makeNote({
    id: '2',
    title: 'Beta Testing',
    updatedAt: '2026-02-16T11:00:00Z',
  }),
  makeNote({ id: '3', title: 'Gamma Ray', updatedAt: '2026-02-16T10:00:00Z' }),
  makeNote({
    id: '4',
    title: 'Delta Force',
    updatedAt: '2026-02-15T12:00:00Z',
  }),
  makeNote({
    id: '5',
    title: 'Epsilon Five',
    updatedAt: '2026-02-14T12:00:00Z',
  }),
];

async function renderExplorer(notes: Note[] = sampleNotes) {
  mockRouteLoaderData.mockReturnValue({ notes });

  const { default: NotesExplorer } = await import(
    '../../../../features/notes/components/NotesExplorer'
  );

  return render(
    <ChakraProvider>
      <MemoryRouter>
        <NotesExplorer />
      </MemoryRouter>
    </ChakraProvider>
  );
}

describe('NotesExplorer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    act(() => {
      useUIStore.setState({
        notesSortBy: 'lastModified',
        notesSortDirection: 'desc',
        notesSearchQuery: '',
        actions: useUIStore.getState().actions,
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('renders "FOR YOU" section header when notes exist and not searching', async () => {
    await renderExplorer();
    expect(screen.getByTestId('for-you-header')).toHaveTextContent('FOR YOU');
  });

  it('renders date group headers', async () => {
    await renderExplorer();
    const explorer = screen.getByTestId('notes-explorer');
    expect(explorer).toBeInTheDocument();
    const textElements = screen.getAllByText(
      /Today|Yesterday|This Week|This Month|Older/
    );
    expect(textElements.length).toBeGreaterThan(0);
  });

  it('renders all notes as ExplorerNoteCard elements', async () => {
    await renderExplorer();
    const cards = screen.getAllByTestId('explorer-note-card');
    expect(cards.length).toBeGreaterThanOrEqual(sampleNotes.length);
  });

  it('shows search result count when searching', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('Beta');
    });
    await renderExplorer();
    expect(screen.getByTestId('search-result-count')).toHaveTextContent(
      /1.*result/
    );
  });

  it('shows filtered notes when searching', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('Alpha');
    });
    await renderExplorer();
    const cards = screen.getAllByTestId('explorer-note-card');
    expect(cards.length).toBe(1);
  });

  it('shows "No notes found" when search has no results', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('zzzznonexistent');
    });
    await renderExplorer();
    expect(screen.getByTestId('no-notes-found')).toHaveTextContent(
      'No notes found'
    );
  });

  it('shows "No notes yet" empty state when notes array is empty', async () => {
    await renderExplorer([]);
    expect(screen.getByTestId('zero-notes-state')).toBeInTheDocument();
    expect(screen.getByText('No notes yet')).toBeInTheDocument();
  });

  it('clicking a note card calls navigate with correct path', async () => {
    await renderExplorer();
    const cards = screen.getAllByTestId('explorer-note-card');
    fireEvent.click(cards[0]);
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringMatching(/^\/notes\//)
    );
  });

  it('hides FOR YOU section when searching', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('Alpha');
    });
    await renderExplorer();
    expect(screen.queryByTestId('for-you-header')).not.toBeInTheDocument();
  });

  it('does not show FOR YOU when no notes', async () => {
    await renderExplorer([]);
    expect(screen.queryByTestId('for-you-header')).not.toBeInTheDocument();
  });

  it('renders explorer toolbar', async () => {
    await renderExplorer();
    expect(screen.getByTestId('explorer-search')).toBeInTheDocument();
  });

  it('typing in search input updates store and shows in input', async () => {
    await renderExplorer();
    const searchInput = screen.getByTestId('explorer-search');

    fireEvent.change(searchInput, { target: { value: 'Alpha' } });

    expect(useUIStore.getState().notesSearchQuery).toBe('Alpha');
    expect(searchInput).toHaveValue('Alpha');
  });

  it('typing filters notes in real-time', async () => {
    await renderExplorer();
    const searchInput = screen.getByTestId('explorer-search');

    fireEvent.change(searchInput, { target: { value: 'Beta' } });

    expect(screen.getByTestId('search-result-count')).toHaveTextContent(
      /1.*result/
    );
    const cards = screen.getAllByTestId('explorer-note-card');
    expect(cards.length).toBe(1);
  });
});
