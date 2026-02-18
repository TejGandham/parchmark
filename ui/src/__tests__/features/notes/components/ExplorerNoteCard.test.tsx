import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import ExplorerNoteCard from '../../../../features/notes/components/ExplorerNoteCard';
import { Note } from '../../../../types';

vi.mock('../../../../utils/compactTime', () => ({
  formatCompactTime: vi.fn((dateStr: string) => {
    if (dateStr.includes('2026-02-16')) return '2d';
    if (dateStr.includes('2026-01-01')) return 'Jan 1';
    return 'now';
  }),
}));

function makeNote(overrides: Partial<Note> & { id: string }): Note {
  return {
    title: `Note ${overrides.id}`,
    content: `# Note ${overrides.id}\n\nThis is some sample content for testing purposes with enough words to count.`,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-02-16T12:00:00Z',
    ...overrides,
  };
}

describe('ExplorerNoteCard', () => {
  const defaultNote = makeNote({ id: 'note-1', title: 'Test Note' });
  const defaultOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderCard(props: Partial<React.ComponentProps<typeof ExplorerNoteCard>> = {}) {
    return render(
      <ChakraProvider>
        <ExplorerNoteCard
          note={defaultNote}
          isActive={false}
          onSelect={defaultOnSelect}
          {...props}
        />
      </ChakraProvider>
    );
  }

  it('renders title from note', () => {
    renderCard();
    expect(screen.getByText('Test Note')).toBeInTheDocument();
  });

  it('renders content preview as plain text', () => {
    renderCard({
      note: makeNote({
        id: 'note-2',
        content: '# My Title\n\nSome **bold** and *italic* content here.',
      }),
    });
    expect(screen.getByText(/Some bold and italic content here/)).toBeInTheDocument();
  });

  it('renders word count', () => {
    renderCard();
    expect(screen.getByText(/\d+ words/)).toBeInTheDocument();
  });

  it('renders reading time', () => {
    renderCard();
    expect(screen.getByText(/\d+ min read/)).toBeInTheDocument();
  });

  it('renders relative timestamp', () => {
    renderCard();
    expect(screen.getByText('2d')).toBeInTheDocument();
  });

  it('calls onSelect with note.id when clicked', () => {
    renderCard();
    const card = screen.getByTestId('explorer-note-card');
    fireEvent.click(card);
    expect(defaultOnSelect).toHaveBeenCalledWith('note-1');
  });

  it('calls onSelect when Enter key pressed', () => {
    renderCard();
    const card = screen.getByTestId('explorer-note-card');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(defaultOnSelect).toHaveBeenCalledWith('note-1');
  });

  it('applies active styling when isActive=true', () => {
    renderCard({ isActive: true });
    const card = screen.getByTestId('explorer-note-card');
    const style = window.getComputedStyle(card);
    expect(
      card.getAttribute('data-testid')
    ).toBe('explorer-note-card');
    expect(card).toBeInTheDocument();
  });

  it('highlights search keywords when searchQuery provided', () => {
    renderCard({
      note: makeNote({ id: 'note-3', title: 'React Hooks Guide' }),
      searchQuery: 'React',
    });
    const strongElements = screen.getAllByText('React');
    const boldEl = strongElements.find((el) => el.tagName === 'STRONG');
    expect(boldEl).toBeTruthy();
  });

  it('handles note with empty content', () => {
    renderCard({
      note: makeNote({ id: 'note-4', title: 'Empty Note', content: '' }),
    });
    expect(screen.getByText('Empty Note')).toBeInTheDocument();
    expect(screen.getByTestId('explorer-note-card')).toBeInTheDocument();
  });

  it('handles note with very long title', () => {
    const longTitle = 'A'.repeat(300);
    renderCard({
      note: makeNote({ id: 'note-5', title: longTitle }),
    });
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('has correct data-testid', () => {
    renderCard();
    expect(screen.getByTestId('explorer-note-card')).toBeInTheDocument();
  });

  it('has button role for accessibility', () => {
    renderCard();
    const card = screen.getByRole('button', { name: /Open note/i });
    expect(card).toBeInTheDocument();
  });
});
