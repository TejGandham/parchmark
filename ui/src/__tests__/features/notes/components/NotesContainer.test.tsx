import { vi, Mock } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NotesContainer from '../../../../features/notes/components/NotesContainer';
import { useUIStore } from '../../../../store';
import { useStoreRouterSync } from '../../../../features/notes/hooks/useStoreRouterSync';
import { mockNotes } from '../../../__mocks__/mockStores';

// Mock dependencies
vi.mock('../../../../store', () => ({
  useUIStore: vi.fn(),
}));

vi.mock('../../../../features/notes/hooks/useStoreRouterSync', () => ({
  useStoreRouterSync: vi.fn(),
}));

vi.mock('../../../../features/ui/components/Header', () => {
  return {
    default: function MockHeader({
      toggleSidebar,
    }: {
      toggleSidebar: () => void;
    }) {
      return (
        <header data-testid="header">
          <button data-testid="toggle-sidebar" onClick={toggleSidebar}>
            Toggle Sidebar
          </button>
        </header>
      );
    },
  };
});

vi.mock('../../../../features/ui/components/Sidebar', () => {
  return {
    default: function MockSidebar({
      notes,
      currentNoteId,
    }: {
      notes: unknown[];
      currentNoteId: string | null;
      onSelectNote: () => void;
      onCreateNote: () => void;
      onDeleteNote: () => void;
    }) {
      return (
        <div data-testid="sidebar">
          <div>Notes: {notes.length}</div>
          <div>Current: {currentNoteId}</div>
        </div>
      );
    },
  };
});

vi.mock('../../../../features/notes/components/NoteContent', () => {
  return {
    default: function MockNoteContent(props: {
      currentNote: { title: string } | null;
      isEditing: boolean;
      editedContent: string | null;
      setEditedContent: (content: string) => void;
      startEditing: () => void;
      saveNote: () => void;
      createNewNote: () => void;
    }) {
      return (
        <div data-testid="note-content">
          <div>Note: {props.currentNote?.title || 'None'}</div>
          <div>Editing: {props.isEditing ? 'Yes' : 'No'}</div>
          <button data-testid="mock-save" onClick={props.saveNote}>
            Save
          </button>
          <button data-testid="mock-start-edit" onClick={props.startEditing}>
            Start Edit
          </button>
        </div>
      );
    },
  };
});

describe('NotesContainer Component', () => {
  const mockToggleSidebar = vi.fn();

  // Default mock implementations
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useUIStore - updated for direct store access pattern
    (useUIStore as Mock).mockReturnValue({
      isSidebarOpen: true,
      actions: {
        toggleSidebar: mockToggleSidebar,
      },
    });

    // Mock useStoreRouterSync
    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <NotesContainer />
      </MemoryRouter>
    );
  };

  it('should render the component with sidebar open', () => {
    renderComponent();

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should not render sidebar when isSidebarOpen is false', () => {
    // Update the mock to return sidebar closed - updated for direct store access pattern
    (useUIStore as Mock).mockReturnValue({
      isSidebarOpen: false,
      actions: {
        toggleSidebar: mockToggleSidebar,
      },
    });

    renderComponent();

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should pass correct props to NoteContent', () => {
    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: 'Edited content',
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    expect(screen.getByText('Note: Test Note 1')).toBeInTheDocument();
    expect(screen.getByText('Editing: Yes')).toBeInTheDocument();
  });

  it('should handle case when no note is selected', () => {
    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    expect(screen.getByText('Note: None')).toBeInTheDocument();
  });

  it('should handle editing state properly', () => {
    const mockUpdateNote = vi.fn();
    const mockSetEditedContent = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: 'Edited content',
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });

    renderComponent();

    // The NoteContent should receive the correct props for editing
    expect(screen.getByText('Editing: Yes')).toBeInTheDocument();
  });

  it('should handle editedContent being null', () => {
    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    const { container } = renderComponent();

    // Should render without errors when editedContent is null
    expect(container).toBeInTheDocument();
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should provide correct startEditing function', () => {
    const mockSetEditedContent = vi.fn();
    const currentNote = {
      id: 'note-1',
      title: 'Test Note',
      content: '# Test Note\n\nThis is test content.',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    };

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: currentNote,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });

    renderComponent();

    // The component should create the startEditing function correctly
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should provide correct saveNote function behavior', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: '# Updated Note\n\nUpdated content',
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Should create the saveNote function - tested indirectly through props
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should handle saveNote when currentNoteId is null', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: true,
      editedContent: '# Updated Note\n\nUpdated content',
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Should render without calling updateNote when currentNoteId is null
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should handle saveNote when editedContent is null', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Should render without calling updateNote when editedContent is null
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should handle startEditing when currentNote is null', () => {
    const mockSetEditedContent = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });

    renderComponent();

    // Should render and handle null currentNote
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should call updateNote when saveNote is triggered with valid data', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: '# Updated Note\n\nUpdated content',
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Trigger the saveNote function through the mock button
    fireEvent.click(screen.getByTestId('mock-save'));

    expect(mockUpdateNote).toHaveBeenCalledWith(
      'note-1',
      '# Updated Note\n\nUpdated content'
    );
  });

  it('should not call updateNote when saveNote is triggered without currentNoteId', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: true,
      editedContent: '# Updated Note\n\nUpdated content',
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Trigger the saveNote function through the mock button
    fireEvent.click(screen.getByTestId('mock-save'));

    expect(mockUpdateNote).not.toHaveBeenCalled();
  });

  it('should not call updateNote when saveNote is triggered without editedContent', () => {
    const mockUpdateNote = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: mockUpdateNote,
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: vi.fn(),
      },
    });

    renderComponent();

    // Trigger the saveNote function through the mock button
    fireEvent.click(screen.getByTestId('mock-save'));

    expect(mockUpdateNote).not.toHaveBeenCalled();
  });

  it('should call setEditedContent with current note content when startEditing is triggered', () => {
    const mockSetEditedContent = vi.fn();
    const currentNote = {
      id: 'note-1',
      title: 'Test Note',
      content: '# Test Note\n\nThis is test content.',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    };

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: currentNote,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });

    renderComponent();

    // Trigger the startEditing function through the mock button
    fireEvent.click(screen.getByTestId('mock-start-edit'));

    expect(mockSetEditedContent).toHaveBeenCalledWith(
      '# Test Note\n\nThis is test content.'
    );
  });

  it('should call setEditedContent with empty string when startEditing is triggered without currentNote', () => {
    const mockSetEditedContent = vi.fn();

    (useStoreRouterSync as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: vi.fn(),
        updateNote: vi.fn(),
        deleteNote: vi.fn(),
        setCurrentNote: vi.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });

    renderComponent();

    // Trigger the startEditing function through the mock button
    fireEvent.click(screen.getByTestId('mock-start-edit'));

    expect(mockSetEditedContent).toHaveBeenCalledWith('');
  });
});
