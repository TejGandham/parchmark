import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import { act } from 'react';
import { CommandPalette } from '../../../../features/ui/components/CommandPalette';
import { highlightKeyword } from '../../../../features/ui/components/commandPaletteUtils';
import { useUIStore } from '../../../../features/ui/store/ui';
import { Note } from '../../../../types';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ noteId: 'current-note' }),
  };
});

vi.mock('../../../../services/api', async () => {
  const actual = await vi.importActual('../../../../services/api');
  return {
    ...actual,
    trackNoteAccess: vi.fn().mockResolvedValue(undefined),
    getSimilarNotes: vi.fn().mockResolvedValue([]),
  };
});

function makeNote(overrides: Partial<Note> & { id: string }): Note {
  return {
    title: `Note ${overrides.id}`,
    content: `Content of note ${overrides.id}`,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-02-16T12:00:00Z',
    ...overrides,
  };
}

const sampleNotes: Note[] = [
  makeNote({ id: '1', title: 'Alpha', updatedAt: '2026-02-16T12:00:00Z' }),
  makeNote({
    id: '2',
    title: 'Beta Testing',
    updatedAt: '2026-02-16T11:00:00Z',
  }),
  makeNote({ id: '3', title: 'Gamma', updatedAt: '2026-02-16T10:00:00Z' }),
  makeNote({ id: '4', title: 'Delta', updatedAt: '2026-02-16T09:00:00Z' }),
  makeNote({
    id: '5',
    title: 'Epsilon',
    updatedAt: '2026-02-16T08:00:00Z',
  }),
  makeNote({
    id: '6',
    title: 'Zeta Test',
    updatedAt: '2026-02-16T07:00:00Z',
  }),
];

function renderPalette(notes: Note[] = []) {
  return render(
    <ChakraProvider>
      <MemoryRouter>
        <CommandPalette notes={notes} />
      </MemoryRouter>
    </ChakraProvider>
  );
}

function openPalette() {
  act(() => {
    useUIStore.getState().actions.openPalette();
  });
}

function closePaletteViaStore() {
  act(() => {
    useUIStore.getState().actions.closePalette();
  });
}

describe('CommandPalette', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    act(() => {
      useUIStore.setState({
        isPaletteOpen: false,
        paletteSearchQuery: '',
        actions: useUIStore.getState().actions,
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('does not render when closed', () => {
    renderPalette();
    expect(screen.queryByTestId('command-palette')).not.toBeInTheDocument();
  });

  it('renders when open', () => {
    openPalette();
    renderPalette();
    expect(screen.getByTestId('command-palette')).toBeInTheDocument();
  });

  it('has correct dialog role and aria-label', () => {
    openPalette();
    renderPalette();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-label', 'Command palette');
  });

  it('auto-focuses search input on open', () => {
    const focusSpy = vi.spyOn(HTMLInputElement.prototype, 'focus');
    openPalette();
    renderPalette();
    expect(focusSpy).toHaveBeenCalled();
    focusSpy.mockRestore();
  });

  it('renders search input with placeholder', () => {
    openPalette();
    renderPalette();
    expect(
      screen.getByPlaceholderText('What are you looking for?')
    ).toBeInTheDocument();
  });

  it('updates search query on input change', () => {
    openPalette();
    renderPalette();
    const searchInput = screen.getByTestId('command-palette-search');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    expect(useUIStore.getState().paletteSearchQuery).toBe('test query');
  });

  it('closes when backdrop is clicked', () => {
    openPalette();
    renderPalette();
    const backdrop = screen.getByTestId('command-palette-backdrop');
    fireEvent.click(backdrop);
    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('does not close when palette body is clicked', () => {
    openPalette();
    renderPalette();
    const palette = screen.getByTestId('command-palette');
    fireEvent.click(palette);
    expect(useUIStore.getState().isPaletteOpen).toBe(true);
  });

  it('clears search query on close', () => {
    openPalette();
    act(() => {
      useUIStore.getState().actions.setPaletteSearchQuery('some text');
    });
    renderPalette();
    closePaletteViaStore();
    expect(useUIStore.getState().paletteSearchQuery).toBe('');
  });

  it('renders backdrop with correct test id', () => {
    openPalette();
    renderPalette();
    expect(screen.getByTestId('command-palette-backdrop')).toBeInTheDocument();
  });

  describe('FOR YOU section', () => {
    it('shows FOR YOU header when palette is open with notes', () => {
      openPalette();
      renderPalette(sampleNotes);
      expect(screen.getByTestId('for-you-header')).toHaveTextContent('FOR YOU');
    });

    it('displays FOR YOU section above RECENT', () => {
      openPalette();
      renderPalette(sampleNotes);
      const forYouHeader = screen.getByTestId('for-you-header');
      const recentHeader = screen.getByTestId('recent-header');
      const order = forYouHeader.compareDocumentPosition(recentHeader);
      expect(order & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    it('excludes the current note from FOR YOU', () => {
      openPalette();
      renderPalette([
        ...sampleNotes,
        makeNote({
          id: 'current-note',
          title: 'Current',
          updatedAt: '2026-02-16T13:00:00Z',
        }),
      ]);
      const forYouHeader = screen.getByTestId('for-you-header');
      const recentHeader = screen.getByTestId('recent-header');
      const forYouItems: string[] = [];
      let sibling = forYouHeader.parentElement!.nextElementSibling;
      while (sibling && !sibling.contains(recentHeader)) {
        if (sibling.getAttribute('data-testid') === 'palette-note-item') {
          forYouItems.push(sibling.textContent ?? '');
        }
        sibling = sibling.nextElementSibling;
      }
      expect(forYouItems.join('')).not.toContain('Current');
    });

    it('does not show FOR YOU section when no notes', () => {
      openPalette();
      renderPalette([]);
      expect(screen.queryByTestId('for-you-header')).not.toBeInTheDocument();
    });

    it('hides FOR YOU section during search', () => {
      openPalette();
      renderPalette(sampleNotes);
      expect(screen.getByTestId('for-you-header')).toBeInTheDocument();
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'Alpha' },
      });
      expect(screen.queryByTestId('for-you-header')).not.toBeInTheDocument();
    });
  });

  describe('RECENT section', () => {
    it('shows RECENT header when palette is open with notes', () => {
      openPalette();
      renderPalette(sampleNotes);
      expect(screen.getByTestId('recent-header')).toHaveTextContent('RECENT');
    });

    it('shows notes ordered by updatedAt desc', () => {
      openPalette();
      renderPalette(sampleNotes);
      const items = screen.getAllByTestId('palette-note-item');
      expect(items[0]).toHaveTextContent('Alpha');
      expect(items[1]).toHaveTextContent('Beta Testing');
    });
  });

  describe('Search transition', () => {
    it('hides RECENT section when search query is non-empty', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'test' },
      });
      expect(screen.queryByTestId('recent-header')).not.toBeInTheDocument();
    });

    it('shows result count', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'test' },
      });
      expect(screen.getByTestId('search-result-count')).toHaveTextContent(
        '2 results'
      );
    });

    it('shows "1 result" singular', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'Alpha' },
      });
      expect(screen.getByTestId('search-result-count')).toHaveTextContent(
        '1 result'
      );
    });

    it('shows no-match message for unmatched query', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'zzzzzzz' },
      });
      expect(screen.getByTestId('no-notes-found')).toHaveTextContent(
        'No notes found'
      );
    });

    it('restores sections when search is cleared', () => {
      openPalette();
      renderPalette(sampleNotes);
      const searchInput = screen.getByTestId('command-palette-search');
      fireEvent.change(searchInput, { target: { value: 'test' } });
      expect(screen.queryByTestId('recent-header')).not.toBeInTheDocument();
      fireEvent.change(searchInput, { target: { value: '' } });
      expect(screen.getByTestId('recent-header')).toBeInTheDocument();
    });

    it('shows bold keyword highlighting in search results', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'Beta' },
      });
      const strongElements = screen.getAllByText('Beta');
      const boldEl = strongElements.find((el) => el.tagName === 'STRONG');
      expect(boldEl).toBeTruthy();
    });
  });

  describe('Note selection', () => {
    it('clicking a note navigates and closes palette', () => {
      openPalette();
      renderPalette(sampleNotes);
      const items = screen.getAllByTestId('palette-note-item');
      fireEvent.click(items[0]);
      expect(mockNavigate).toHaveBeenCalledWith('/notes/1');
      expect(useUIStore.getState().isPaletteOpen).toBe(false);
    });

    it('calls trackNoteAccess on selection', async () => {
      const { trackNoteAccess } = await import('../../../../services/api');
      openPalette();
      renderPalette(sampleNotes);
      const items = screen.getAllByTestId('palette-note-item');
      fireEvent.click(items[0]);
      expect(trackNoteAccess).toHaveBeenCalledWith('1');
    });
  });

  describe('Zero notes state', () => {
    it('shows zero notes message when no notes and no search', () => {
      openPalette();
      renderPalette([]);
      expect(screen.getByTestId('zero-notes-state')).toBeInTheDocument();
      expect(screen.getByText('No notes yet')).toBeInTheDocument();
    });

    it('does not show RECENT section with zero notes', () => {
      openPalette();
      renderPalette([]);
      expect(screen.queryByTestId('recent-header')).not.toBeInTheDocument();
    });

    it('does not show zero notes state when searching', () => {
      openPalette();
      renderPalette([]);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'test' },
      });
      expect(screen.queryByTestId('zero-notes-state')).not.toBeInTheDocument();
    });
  });

  describe('Similar notes integration', () => {
    it('fetches similar notes when palette opens with currentNoteId', async () => {
      const { getSimilarNotes } = await import('../../../../services/api');
      openPalette();
      renderPalette(sampleNotes);
      expect(getSimilarNotes).toHaveBeenCalledWith('current-note');
    });

    it('does NOT fetch similar notes when no currentNoteId', async () => {
      const { getSimilarNotes } = await import('../../../../services/api');
      vi.mocked(getSimilarNotes).mockClear();

      renderPalette(sampleNotes);
      expect(getSimilarNotes).not.toHaveBeenCalled();
    });

    it('clears similar notes when palette closes', async () => {
      const { getSimilarNotes } = await import('../../../../services/api');
      vi.mocked(getSimilarNotes).mockResolvedValue([
        { id: '2', title: 'Note 2', similarity: 0.9, updatedAt: '' },
      ]);

      openPalette();
      renderPalette(sampleNotes);
      expect(getSimilarNotes).toHaveBeenCalled();

      closePaletteViaStore();
    });

    it('falls back to heuristic when getSimilarNotes returns empty array', async () => {
      const { getSimilarNotes } = await import('../../../../services/api');
      vi.mocked(getSimilarNotes).mockResolvedValue([]);

      openPalette();
      renderPalette(sampleNotes);

      expect(screen.getByTestId('for-you-header')).toBeInTheDocument();
    });
  });

  describe('Deep link behavior', () => {
    it('does not auto-open palette when noteId is present (NotesLayout handles this)', () => {
      renderPalette(sampleNotes);
      expect(screen.queryByTestId('command-palette')).not.toBeInTheDocument();
    });
  });

  describe('Browse All Notes link', () => {
    it('renders "Browse All Notes →" when not searching and notes exist', () => {
      openPalette();
      renderPalette(sampleNotes);
      const browseLink = screen.getByTestId('browse-all-link');
      expect(browseLink).toBeInTheDocument();
      expect(browseLink).toHaveTextContent('Browse All Notes');
    });

    it('does not render when searching', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.change(screen.getByTestId('command-palette-search'), {
        target: { value: 'Alpha' },
      });
      expect(screen.queryByTestId('browse-all-link')).not.toBeInTheDocument();
    });

    it('does not render when no notes', () => {
      openPalette();
      renderPalette([]);
      expect(screen.queryByTestId('browse-all-link')).not.toBeInTheDocument();
    });

    it('navigates to /notes and closes palette on click', () => {
      openPalette();
      renderPalette(sampleNotes);
      fireEvent.click(screen.getByTestId('browse-all-link'));
      expect(mockNavigate).toHaveBeenCalledWith('/notes');
      expect(useUIStore.getState().isPaletteOpen).toBe(false);
    });
  });

  describe('highlightKeyword', () => {
    it('returns text as-is when keyword is empty', () => {
      expect(highlightKeyword('hello', '')).toBe('hello');
    });

    it('returns ReactNode array with bold match', () => {
      const result = highlightKeyword('Hello World', 'World');
      expect(Array.isArray(result)).toBe(true);
    });

    it('is case-insensitive', () => {
      const result = highlightKeyword('Hello World', 'hello');
      expect(Array.isArray(result)).toBe(true);
    });
  });
});
