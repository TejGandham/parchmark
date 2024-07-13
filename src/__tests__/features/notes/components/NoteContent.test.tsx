import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteContent from '../../../../features/notes/components/NoteContent';
import { mockNotes } from '../../../__mocks__/mockStores';

// Mock the components that NoteContent uses
jest.mock('../../../../features/notes/components/NoteActions', () => {
  return function MockNoteActions({ isEditing, onEdit, onSave }: any) {
    return (
      <div data-testid="note-actions">
        <button data-testid="edit-button" onClick={onEdit} disabled={isEditing}>
          Edit
        </button>
        <button data-testid="save-button" onClick={onSave} disabled={!isEditing}>
          Save
        </button>
      </div>
    );
  };
});

// Mock the markdown service
jest.mock('../../../../services/markdownService', () => ({
  extractTitleFromMarkdown: jest.fn().mockImplementation((content) => {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : 'Untitled Note';
  }),
  removeH1FromContent: jest.fn().mockImplementation((content) => {
    return content.replace(/^#\s+(.+)($|\n)/, '').trim();
  }),
}));

describe('NoteContent Component', () => {
  // Default props for most tests
  const defaultProps = {
    currentNote: mockNotes[0],
    isEditing: false,
    editedContent: '',
    setEditedContent: jest.fn(),
    startEditing: jest.fn(),
    saveNote: jest.fn(),
    createNewNote: jest.fn(),
  };

  const renderComponent = (props = {}) => {
    return render(
      <TestProvider>
        <NoteContent {...defaultProps} {...props} />
      </TestProvider>
    );
  };

  describe('View Mode', () => {
    it('should render the note title and content in view mode', () => {
      renderComponent();
      
      expect(screen.getByText('Test Note 1')).toBeInTheDocument();
      expect(screen.getByText('This is test note 1 content.')).toBeInTheDocument();
    });

    it('should show edit button in view mode', () => {
      renderComponent();
      
      const editButton = screen.getByTestId('edit-button');
      expect(editButton).toBeInTheDocument();
      expect(editButton).not.toBeDisabled();
    });

    it('should call startEditing when edit button is clicked', () => {
      renderComponent();
      
      fireEvent.click(screen.getByTestId('edit-button'));
      expect(defaultProps.startEditing).toHaveBeenCalled();
    });
  });

  describe('Edit Mode', () => {
    it('should render textarea in edit mode', () => {
      renderComponent({
        isEditing: true,
        editedContent: '# Test Note 1\n\nEdited content',
      });
      
      // Just get the textarea by its placeholder text
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('# Test Note 1\n\nEdited content');
    });

    it('should update edited content when textarea changes', () => {
      renderComponent({
        isEditing: true,
        editedContent: '# Test Note 1\n\nInitial content',
      });
      
      // Just get the textarea by its placeholder text
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      fireEvent.change(textarea, { target: { value: '# Test Note 1\n\nUpdated content' } });
      
      expect(defaultProps.setEditedContent).toHaveBeenCalledWith('# Test Note 1\n\nUpdated content');
    });

    it('should call saveNote when save button is clicked', () => {
      renderComponent({
        isEditing: true,
        editedContent: '# Test Note 1\n\nEdited content',
      });
      
      fireEvent.click(screen.getByTestId('save-button'));
      expect(defaultProps.saveNote).toHaveBeenCalled();
    });

    it('should show the title extracted from markdown in edit mode', () => {
      renderComponent({
        isEditing: true,
        editedContent: '# Changed Title\n\nContent',
      });
      
      // Look for an input that has the title value
      const titleInput = screen.getByDisplayValue('Changed Title');
      expect(titleInput).toBeInTheDocument();
      
      // There should be a help text about the title
      expect(screen.getByText(/title is automatically set/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show "No note selected" message when no note is provided', () => {
      renderComponent({ currentNote: null });
      
      expect(screen.getByText('No note selected.')).toBeInTheDocument();
      expect(screen.getByText('Create New Note')).toBeInTheDocument();
    });

    it('should call createNewNote when "Create New Note" button is clicked', () => {
      renderComponent({ currentNote: null });
      
      fireEvent.click(screen.getByText('Create New Note'));
      expect(defaultProps.createNewNote).toHaveBeenCalled();
    });

    it('should show editing interface when creating a new note', () => {
      renderComponent({
        currentNote: null,
        isEditing: true,
        editedContent: '# New Note\n\n',
      });
      
      // Should have an element with the title (could be readonly input with title value)
      const heading = screen.getByRole('heading');
      expect(heading).toBeInTheDocument();
      
      // Should have a textarea
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('# New Note\n\n');
    });
  });

  describe('Edge Cases', () => {
    it('should handle notes with missing title', () => {
      renderComponent({
        currentNote: {
          ...mockNotes[0],
          title: '',
          content: 'Content without title',
        },
      });
      
      // The component should still render without errors
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });

    it('should handle empty content in view mode', () => {
      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: '',
        },
      });
      
      // The component should still render without errors
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });
  });
});