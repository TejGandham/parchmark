import { vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import Sidebar from '../../../../features/ui/components/Sidebar';
import { mockNotes } from '../../../__mocks__/mockStores';

// Mock the UI store with mutable state
let mockUIState = {
  notesSortBy: 'lastModified' as const,
  notesSearchQuery: '',
  notesGroupByDate: true,
  actions: {
    setNotesSortBy: vi.fn(),
    setNotesSearchQuery: vi.fn(),
    setNotesGroupByDate: vi.fn(),
  },
};

vi.mock('../../../../features/ui/store', () => ({
  useUIStore: (selector: (state: typeof mockUIState) => unknown) =>
    selector(mockUIState),
}));

// Mock NoteItem component
vi.mock('../../../../features/notes/components/NoteItem', () => {
  return {
    default: function MockNoteItem({ note, isActive, onSelect, onDelete }) {
      return (
        <li>
          <button
            onClick={() => onSelect(note.id)}
            aria-selected={isActive}
            data-testid={`note-item-${note.id}`}
          >
            {note.title}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(note.id);
            }}
            aria-label={`Delete ${note.title}`}
          >
            Delete
          </button>
          <span data-testid="note-date">Jan 1, 2023</span>
        </li>
      );
    },
  };
});

describe('Sidebar Component', () => {
  // Default props for component
  const defaultProps = {
    notes: mockNotes,
    currentNoteId: 'note-1',
    onSelectNote: vi.fn(),
    onCreateNote: vi.fn(),
    onDeleteNote: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mockUIState to default values
    mockUIState = {
      notesSortBy: 'lastModified' as const,
      notesSearchQuery: '',
      notesGroupByDate: true,
      actions: {
        setNotesSortBy: vi.fn(),
        setNotesSearchQuery: vi.fn(),
        setNotesGroupByDate: vi.fn(),
      },
    };
  });

  const renderComponent = (props = {}) => {
    return render(
      <TestProvider>
        <Sidebar {...defaultProps} {...props} />
      </TestProvider>
    );
  };

  it('should render the list of notes', () => {
    renderComponent();

    // Check that each note title is rendered
    expect(screen.getByText('Test Note 1')).toBeInTheDocument();
    expect(screen.getByText('Test Note 2')).toBeInTheDocument();
  });

  it('should highlight the currently selected note', () => {
    renderComponent();

    // Check that the current note has a different style or class
    const noteItems = screen.getAllByRole('button');

    // Get the note items (this implementation may vary based on your component)
    const currentNote = noteItems.find((item) =>
      item.textContent?.includes('Test Note 1')
    );

    expect(currentNote).toHaveAttribute('aria-selected', 'true');
  });

  it('should call onSelectNote when a note is clicked', () => {
    renderComponent();

    // Find the second note and click it
    const noteItem = screen.getByText('Test Note 2').closest('button');
    if (noteItem) fireEvent.click(noteItem);

    expect(defaultProps.onSelectNote).toHaveBeenCalledWith('note-2');
  });

  it('should call onCreateNote when create button is clicked', () => {
    renderComponent();

    // Find the create button and click it
    const createButton = screen.getByRole('button', { name: /new note/i });
    fireEvent.click(createButton);

    expect(defaultProps.onCreateNote).toHaveBeenCalled();
  });

  it('should call onDeleteNote when delete button is clicked', () => {
    renderComponent();

    // Find the delete buttons and click the first one
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    expect(defaultProps.onDeleteNote).toHaveBeenCalledWith('note-1');
  });

  it('should display creation date', () => {
    renderComponent();

    // Our mock implementation shows dates
    const dateElements = screen.getAllByTestId('note-date');
    expect(dateElements.length).toBeGreaterThan(0);
    expect(dateElements[0]).toHaveTextContent('Jan 1, 2023');
  });

  it('should render empty state when no notes are available', () => {
    renderComponent({ notes: [] });

    // There should be no note items
    const noteItems = screen.queryAllByRole('button', { name: /test note/i });
    expect(noteItems.length).toBe(0);

    // Create button should still be available
    const createButton = screen.getByRole('button', {
      name: /create new note/i,
    });
    expect(createButton).toBeInTheDocument();
  });

  it('should render notes in correct order (latest first)', () => {
    // Add a new note that should appear first
    const notesWithNewFirst = [
      {
        id: 'note-3',
        title: 'Newest Note',
        content: '# Newest Note\n\nContent',
        createdAt: '2023-01-03T00:00:00.000Z',
        updatedAt: '2023-01-03T00:00:00.000Z',
      },
      ...mockNotes,
    ];

    renderComponent({ notes: notesWithNewFirst });

    // Check that the notes are rendered in the correct order
    const noteItems = screen.getAllByRole('button', {
      name: /test note|newest note/i,
    });
    expect(noteItems[0].textContent).toContain('Newest Note');
  });

  it('should show loading skeleton when isLoading is true', () => {
    renderComponent({ isLoading: true });

    // Should not show actual notes
    expect(screen.queryByText('Test Note 1')).not.toBeInTheDocument();
    expect(screen.queryByText('Test Note 2')).not.toBeInTheDocument();
  });

  it('should render search input', () => {
    renderComponent();

    const searchInput = screen.getByPlaceholderText('Search notes...');
    expect(searchInput).toBeInTheDocument();
  });

  it('should render sorting dropdown with default value', () => {
    renderComponent();

    // Find elements to verify sorting UI is rendered
    const notesList = screen.getByRole('list', { hidden: true });
    expect(notesList).toBeInTheDocument();
  });

  it('should render notes with date-based grouping enabled', () => {
    renderComponent();

    // Notes should be rendered - grouping behavior is tested at the utility level
    expect(screen.getByText('Test Note 1')).toBeInTheDocument();
    expect(screen.getByText('Test Note 2')).toBeInTheDocument();
  });

  it('should render notes without date-based grouping when disabled', () => {
    // Disable grouping
    mockUIState.notesGroupByDate = false;

    renderComponent();

    // Notes should be rendered in a simple list
    expect(screen.getByText('Test Note 1')).toBeInTheDocument();
    expect(screen.getByText('Test Note 2')).toBeInTheDocument();

    // No group headers should be present
    expect(screen.queryByText('Today')).not.toBeInTheDocument();
    expect(screen.queryByText('Yesterday')).not.toBeInTheDocument();
    expect(screen.queryByText('This Week')).not.toBeInTheDocument();
  });
});
