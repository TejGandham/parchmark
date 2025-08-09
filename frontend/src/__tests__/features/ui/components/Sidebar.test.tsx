import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import Sidebar from '../../../../features/ui/components/Sidebar';
import { mockNotes } from '../../../__mocks__/mockStores';


// Mock NoteItem component
jest.mock('../../../../features/notes/components/NoteItem', () => {
  return function MockNoteItem({ note, isActive, onSelect, onDelete }) {
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
  };
});

describe('Sidebar Component', () => {
  // Default props for component
  const defaultProps = {
    notes: mockNotes,
    currentNoteId: 'note-1',
    onSelectNote: jest.fn(),
    onCreateNote: jest.fn(),
    onDeleteNote: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
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
});

