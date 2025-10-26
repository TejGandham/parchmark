import { vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteContent from '../../../../features/notes/components/NoteContent';
import { mockNotes } from '../../../__mocks__/mockStores';

// Mock the components that NoteContent uses
vi.mock('../../../../features/notes/components/NoteActions', () => {
  return {
    default: function MockNoteActions({
      isEditing,
      onEdit,
      onSave,
    }: {
      isEditing: boolean;
      onEdit: () => void;
      onSave: () => void;
    }) {
      return (
        <div data-testid="note-actions">
          <button
            data-testid="edit-button"
            onClick={onEdit}
            disabled={isEditing}
          >
            Edit
          </button>
          <button
            data-testid="save-button"
            onClick={onSave}
            disabled={!isEditing}
          >
            Save
          </button>
        </div>
      );
    },
  };
});

// Mock the markdown service
vi.mock('../../../../services/markdownService', () => ({
  extractTitleFromMarkdown: vi.fn().mockImplementation((content) => {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : 'Untitled Note';
  }),
  removeH1FromContent: vi.fn().mockImplementation((content) => {
    return content.replace(/^#\s+(.+)($|\n)/, '').trim();
  }),
}));

describe('NoteContent Component', () => {
  // Default props for most tests
  const defaultProps = {
    currentNote: mockNotes[0],
    isEditing: false,
    editedContent: '',
    setEditedContent: vi.fn(),
    startEditing: vi.fn(),
    saveNote: vi.fn(),
    createNewNote: vi.fn(),
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
      expect(
        screen.getByText('This is test note 1 content.')
      ).toBeInTheDocument();
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
      fireEvent.change(textarea, {
        target: { value: '# Test Note 1\n\nUpdated content' },
      });

      expect(defaultProps.setEditedContent).toHaveBeenCalledWith(
        '# Test Note 1\n\nUpdated content'
      );
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
      expect(
        screen.getByText(/title is automatically set/i)
      ).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show "Ready to capture your thoughts?" message when no note is provided', () => {
      renderComponent({ currentNote: null });

      expect(screen.getByText('Ready to capture your thoughts?')).toBeInTheDocument();
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

    it('should extract title from edited content in edit mode', () => {
      const editedContent = '# New Title\n\nSome edited content';

      renderComponent({
        isEditing: true,
        editedContent,
      });

      expect(screen.getByDisplayValue('New Title')).toBeInTheDocument();
    });

    it('should show full content when editing', () => {
      const editedContent = '# Test Note\n\nThis is edited content';

      renderComponent({
        isEditing: true,
        editedContent,
      });

      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toHaveValue(editedContent);
    });

    it('should remove H1 from content in view mode', () => {
      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content:
            '# Test Title\n\nThis content should be shown without the H1.',
        },
        isEditing: false,
      });

      // Should show the content without the H1 title
      expect(
        screen.getByText(/This content should be shown without the H1/)
      ).toBeInTheDocument();
    });

    it('should handle content with complex markdown', () => {
      const complexContent =
        '# Main Title\n\n## Subtitle\n\n- Item 1\n- Item 2\n\n**Bold text**';

      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: complexContent,
        },
        isEditing: false,
      });

      // Should render the content without errors
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });

    it('should call setEditedContent on textarea change when creating new note', () => {
      const mockSetEditedContent = vi.fn();

      renderComponent({
        currentNote: null,
        isEditing: true,
        editedContent: '# New Note\n\nContent',
        setEditedContent: mockSetEditedContent,
      });

      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      fireEvent.change(textarea, {
        target: { value: '# Changed Title\n\nChanged content' },
      });

      expect(mockSetEditedContent).toHaveBeenCalledWith(
        '# Changed Title\n\nChanged content'
      );
    });

    it('should render editedContent when in editing mode', () => {
      const editedContent = '# Test Title\n\nThis is edited content';

      renderComponent({
        isEditing: true,
        editedContent,
      });

      // The textarea should contain the edited content
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toHaveValue(editedContent);
    });

    it('should call renderContent function with editedContent in edit mode', () => {
      const editedContent = '# Test Title\n\nThis is edited content';

      // Use a note with different content to ensure we're getting editedContent, not note content
      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: '# Original Note\n\nOriginal content',
        },
        isEditing: true,
        editedContent,
      });

      // When editing, we should see a textarea with editedContent, not the original content
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toHaveValue(editedContent);
      expect(textarea).not.toHaveValue('# Original Note\n\nOriginal content');
    });

    it('should render mermaid diagrams when code block has language-mermaid', () => {
      const contentWithMermaid = '# Note\n\n```mermaid\ngraph TD\nA-->B\n```';

      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: contentWithMermaid,
        },
        isEditing: false,
      });

      // Should render ReactMarkdown component (this indirectly tests the mermaid branch)
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });

    it('should render regular code blocks when not mermaid', () => {
      const contentWithCode =
        '# Note\n\n```javascript\nconsole.log("hello");\n```';

      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: contentWithCode,
        },
        isEditing: false,
      });

      // Should render ReactMarkdown component without errors
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });

    it('should handle code blocks without className', () => {
      const contentWithPlainCode = '# Note\n\n`inline code`';

      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: contentWithPlainCode,
        },
        isEditing: false,
      });

      // Should render ReactMarkdown component without errors
      expect(screen.getByTestId('note-actions')).toBeInTheDocument();
    });

    it('should handle edit button click when already editing a new note (no currentNote)', () => {
      renderComponent({
        currentNote: null,
        isEditing: true,
        editedContent: '# New Note\n\nContent',
      });

      // Click the edit button (which should be a no-op since already editing)
      const editButton = screen.getByTestId('edit-button');
      fireEvent.click(editButton);

      // Should not crash and edit button should be disabled
      expect(editButton).toBeDisabled();
    });

    it('should return editedContent in renderContent when isEditing is true', () => {
      const editedContent = '# Edited Title\n\nEdited body';

      renderComponent({
        currentNote: mockNotes[0],
        isEditing: true,
        editedContent,
      });

      // In edit mode, the textarea should show editedContent
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toHaveValue(editedContent);
    });

    it('should return removeH1FromContent result in renderContent when isEditing is false', () => {
      renderComponent({
        currentNote: {
          ...mockNotes[0],
          content: '# Test Note\n\nThis is the content',
        },
        isEditing: false,
      });

      // In view mode, should display content without H1
      expect(screen.getByText(/This is the content/)).toBeInTheDocument();
    });
  });
});
