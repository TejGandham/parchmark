// ui/src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  render,
  screen,
  fireEvent,
  cleanup,
  within,
} from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import * as routerDom from 'react-router-dom';
import * as storeModule from '../../../../store';
import NoteContent from '../../../../features/notes/components/NoteContent';

// Mock router module
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
    useRouteLoaderData: vi.fn(),
    useSearchParams: vi.fn(),
    useNavigate: vi.fn(),
    useFetcher: vi.fn(),
  };
});

// Mock store
vi.mock('../../../../store', () => ({
  useNotesUIStore: vi.fn(),
}));

// Mock NoteActions
vi.mock('../../../../features/notes/components/NoteActions', () => ({
  default: ({
    isEditing,
    onEdit,
    onSave,
    onCancel,
    onDelete,
    isSaving,
    isDeleting,
  }: {
    isEditing: boolean;
    onEdit: () => void;
    onSave: () => void;
    onCancel?: () => void;
    onDelete?: () => void;
    isSaving?: boolean;
    isDeleting?: boolean;
  }) => (
    <div data-testid="note-actions">
      <button
        data-testid="edit-button"
        onClick={onEdit}
        disabled={isEditing || isDeleting}
      >
        Edit
      </button>
      {isEditing && (
        <button data-testid="cancel-button" onClick={onCancel}>
          Cancel
        </button>
      )}
      <button
        data-testid="save-button"
        onClick={onSave}
        disabled={!isEditing || isSaving}
      >
        {isSaving ? 'Saving...' : 'Save'}
      </button>
      {!isEditing && onDelete && (
        <button
          data-testid="delete-button"
          onClick={onDelete}
          disabled={isDeleting}
        >
          Delete
        </button>
      )}
    </div>
  ),
}));

vi.mock('../../../../features/notes/components/NoteMetadata', () => ({
  default: ({
    createdAt,
    updatedAt,
  }: {
    createdAt: string;
    updatedAt: string;
  }) => (
    <div
      data-testid="note-metadata"
      data-created={createdAt}
      data-updated={updatedAt}
    />
  ),
}));

// Mock markdown service
vi.mock('../../../../services/markdownService', () => ({
  extractTitleFromMarkdown: (content: string) => {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : 'Untitled Note';
  },
  removeH1FromContent: (content: string) => {
    return content.replace(/^#\s+(.+)($|\n)/, '').trim();
  },
}));

// Mock ReactMarkdown
vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => (
    <div data-testid="markdown-preview">{children}</div>
  ),
}));

vi.mock('remark-gfm', () => ({ default: () => {} }));
vi.mock('rehype-raw', () => ({ default: () => {} }));
vi.mock('../../../../components/Mermaid', () => ({
  default: () => <div data-testid="mermaid">Mermaid</div>,
}));

const mockNotes = [
  {
    id: 'note-1',
    title: 'First Note',
    content: '# First Note\n\nThis is the content.',
    createdAt: '2026-01-29T10:00:00Z',
    updatedAt: '2026-01-29T10:00:00Z',
  },
  {
    id: 'note-2',
    title: 'Second Note',
    content: '# Second Note\n\nMore content here.',
    createdAt: '2026-01-29T09:00:00Z',
    updatedAt: '2026-01-29T09:00:00Z',
  },
];

describe('NoteContent with Data Router', () => {
  const mockSetSearchParams = vi.fn();
  const mockFetcherSubmit = vi.fn();
  const mockSetEditedContent = vi.fn();
  const mockNavigate = vi.fn();

  function setupMocks(
    options: {
      noteId?: string;
      isEditing?: boolean;
      editedContent?: string | null;
    } = {}
  ) {
    const {
      noteId = 'note-1',
      isEditing = false,
      editedContent = null,
    } = options;

    vi.mocked(routerDom.useParams).mockReturnValue({ noteId });
    vi.mocked(routerDom.useRouteLoaderData).mockReturnValue({
      notes: mockNotes,
    });
    vi.mocked(routerDom.useSearchParams).mockReturnValue([
      new URLSearchParams(isEditing ? 'editing=true' : ''),
      mockSetSearchParams,
    ] as unknown as ReturnType<typeof routerDom.useSearchParams>);
    vi.mocked(routerDom.useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(routerDom.useFetcher).mockReturnValue({
      submit: mockFetcherSubmit,
      state: 'idle',
      data: null,
    } as unknown as ReturnType<typeof routerDom.useFetcher>);

    vi.mocked(storeModule.useNotesUIStore).mockImplementation((selector) => {
      const state = {
        editedContent,
        setEditedContent: mockSetEditedContent,
      };
      return selector ? selector(state) : state;
    });
  }

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  function renderComponent() {
    return render(
      <ChakraProvider>
        <NoteContent />
      </ChakraProvider>
    );
  }

  describe('View Mode', () => {
    it('renders note title from params', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      expect(screen.getByText('First Note')).toBeInTheDocument();
    });

    it('renders note content in markdown preview', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      expect(screen.getByTestId('markdown-preview')).toBeInTheDocument();
      expect(screen.getByText('This is the content.')).toBeInTheDocument();
    });

    it('shows edit button in view mode', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      const editButton = screen.getByTestId('edit-button');
      expect(editButton).toBeInTheDocument();
      expect(editButton).not.toBeDisabled();
    });

    it('renders NoteMetadata in view mode with the selected note dates', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();

      const metadata = screen.getByTestId('note-metadata');
      expect(metadata).toBeInTheDocument();
      expect(metadata).toHaveAttribute('data-created', '2026-01-29T10:00:00Z');
      expect(metadata).toHaveAttribute('data-updated', '2026-01-29T10:00:00Z');
    });

    it('calls startEditing when edit button clicked', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      fireEvent.click(screen.getByTestId('edit-button'));
      expect(mockSetEditedContent).toHaveBeenCalledWith(
        '# First Note\n\nThis is the content.'
      );
      expect(mockSetSearchParams).toHaveBeenCalledWith({ editing: 'true' });
    });
  });

  describe('Edit Mode', () => {
    it('shows textarea in edit mode', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nThis is the content.',
      });
      renderComponent();
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('# First Note\n\nThis is the content.');
    });

    it('shows save button enabled in edit mode', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nContent',
      });
      renderComponent();
      const saveButton = screen.getByTestId('save-button');
      expect(saveButton).not.toBeDisabled();
    });

    it('does not render NoteMetadata in edit mode', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nThis is the content.',
      });
      renderComponent();

      expect(screen.queryByTestId('note-metadata')).not.toBeInTheDocument();
    });

    it('updates content when textarea changes', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nThis is the content.',
      });
      renderComponent();
      const textarea = screen.getByPlaceholderText(/# Your Title Here/i);
      fireEvent.change(textarea, {
        target: { value: '# Updated Title\n\nNew content' },
      });
      expect(mockSetEditedContent).toHaveBeenCalledWith(
        '# Updated Title\n\nNew content'
      );
    });

    it('submits form when save clicked', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nContent',
      });
      renderComponent();
      fireEvent.click(screen.getByTestId('save-button'));
      expect(mockFetcherSubmit).toHaveBeenCalledWith(
        { content: '# First Note\n\nContent' },
        { method: 'post', action: '/notes/note-1' }
      );
    });

    it('clears editing state only after save succeeds', () => {
      // Initial state: editing
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nContent',
      });
      const { rerender } = renderComponent();
      fireEvent.click(screen.getByTestId('save-button'));

      // State should NOT be cleared immediately
      expect(mockSetSearchParams).not.toHaveBeenCalled();

      // Simulate fetcher completing with success
      vi.mocked(routerDom.useFetcher).mockReturnValue({
        submit: mockFetcherSubmit,
        state: 'idle',
        data: { ok: true },
      } as unknown as ReturnType<typeof routerDom.useFetcher>);

      rerender(
        <ChakraProvider>
          <NoteContent />
        </ChakraProvider>
      );

      // Now state should be cleared
      expect(mockSetSearchParams).toHaveBeenCalledWith({});
      expect(mockSetEditedContent).toHaveBeenCalledWith(null);
    });
  });

  describe('Cancel Editing', () => {
    it('clears editing state when cancel is clicked', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nModified content',
      });
      renderComponent();

      fireEvent.click(screen.getByTestId('cancel-button'));

      expect(mockSetSearchParams).toHaveBeenCalledWith({});
      expect(mockSetEditedContent).toHaveBeenCalledWith(null);
    });

    it('clears editing state when Escape key is pressed', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nModified content',
      });
      renderComponent();

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockSetSearchParams).toHaveBeenCalledWith({});
      expect(mockSetEditedContent).toHaveBeenCalledWith(null);
    });

    it('does not respond to Escape key when not editing', () => {
      setupMocks({ noteId: 'note-1', isEditing: false });
      renderComponent();

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockSetSearchParams).not.toHaveBeenCalled();
      expect(mockSetEditedContent).not.toHaveBeenCalled();
    });
  });

  describe('Note Selection', () => {
    it('finds correct note from notes array', () => {
      setupMocks({ noteId: 'note-2' });
      renderComponent();
      expect(screen.getByText('Second Note')).toBeInTheDocument();
    });

    it('shows empty state when note not found', () => {
      setupMocks({ noteId: 'non-existent' });
      renderComponent();
      expect(
        screen.getByText('Ready to capture your thoughts?')
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Press Ctrl\+\. to search or create a new note/)
      ).toBeInTheDocument();
    });
  });

  describe('Create Note', () => {
    it('submits create action when Create New Note clicked', () => {
      setupMocks({ noteId: 'non-existent' });
      renderComponent();
      fireEvent.click(screen.getByText('Create New Note'));
      expect(mockFetcherSubmit).toHaveBeenCalledWith(null, {
        method: 'post',
        action: '/notes',
      });
    });
  });

  describe('Delete Note', () => {
    it('shows delete button in view mode', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      expect(screen.getByTestId('delete-button')).toBeInTheDocument();
    });

    it('opens confirmation dialog when delete clicked', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      fireEvent.click(screen.getByTestId('delete-button'));
      expect(screen.getByText('Delete Note')).toBeInTheDocument();
      expect(
        screen.getByText(/Are you sure you want to delete/)
      ).toBeInTheDocument();
    });

    it('submits delete action when confirmed', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      fireEvent.click(screen.getByTestId('delete-button'));
      const dialog = screen.getByRole('alertdialog');
      fireEvent.click(within(dialog).getByText('Delete'));
      expect(mockFetcherSubmit).toHaveBeenCalledWith(null, {
        method: 'post',
        action: '/notes/note-1/delete',
      });
    });

    it('closes dialog without deleting when cancel clicked', () => {
      setupMocks({ noteId: 'note-1' });
      renderComponent();
      fireEvent.click(screen.getByTestId('delete-button'));
      const dialog = screen.getByRole('alertdialog');
      fireEvent.click(within(dialog).getByText('Cancel'));
      expect(mockFetcherSubmit).not.toHaveBeenCalled();
    });

    it('does not show delete button in edit mode', () => {
      setupMocks({
        noteId: 'note-1',
        isEditing: true,
        editedContent: '# First Note\n\nContent',
      });
      renderComponent();
      expect(screen.queryByTestId('delete-button')).not.toBeInTheDocument();
    });
  });
});
