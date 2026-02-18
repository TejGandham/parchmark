import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { act } from 'react';
import { Note } from '../../../../types';
import { useUIStore } from '../../../../features/ui/store/ui';

const mockNavigate = vi.fn();
const mockFetcherSubmit = vi.fn();
const mockFetcherState = vi.fn().mockReturnValue('idle');
const mockFetcherData = vi.fn().mockReturnValue(undefined);
const mockRouteLoaderData = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useRouteLoaderData: (...args: unknown[]) => mockRouteLoaderData(...args),
    useFetcher: () => ({
      submit: mockFetcherSubmit,
      get state() {
        return mockFetcherState();
      },
      get data() {
        return mockFetcherData();
      },
    }),
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
    mockFetcherState.mockReturnValue('idle');
    mockFetcherData.mockReturnValue(undefined);
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

  it('shows Create button when search >= 4 chars and no results', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('zzzznonexistent');
    });
    await renderExplorer();
    expect(screen.getByTestId('create-from-search')).toBeInTheDocument();
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

  it('ArrowDown key increments active index', async () => {
    await renderExplorer();
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(mockNavigate).toHaveBeenCalled();
  });

  it('Enter key on active card navigates to note', async () => {
    await renderExplorer();
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringMatching(/^\/notes\//)
    );
  });

  it('Escape key clears search when searching', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('test');
    });
    await renderExplorer();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(useUIStore.getState().notesSearchQuery).toBe('');
  });

  it('Escape key navigates to /notes when not searching', async () => {
    await renderExplorer();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(mockNavigate).toHaveBeenCalledWith('/notes');
  });

  it('keyboard hints footer is visible', async () => {
    await renderExplorer();
    expect(screen.getByText(/↑↓ navigate/)).toBeInTheDocument();
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
    expect(screen.getByTestId('explorer-create-btn')).toBeInTheDocument();
  });

  it('create first note button works in empty state', async () => {
    await renderExplorer([]);
    const createBtn = screen.getByTestId('create-first-note-btn');
    fireEvent.click(createBtn);
    expect(mockFetcherSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'New Note' }),
      expect.objectContaining({ method: 'post', action: '/notes' })
    );
  });

  it('does not create from search when query < 4 chars', async () => {
    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('zz');
    });
    await renderExplorer();
    expect(screen.queryByTestId('create-from-search')).not.toBeInTheDocument();
  });
});
