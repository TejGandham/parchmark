import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NotesContainer from '../../../../features/notes/components/NotesContainer';
import { useUIStore } from '../../../../store';
import { useStoreRouterSync } from '../../../../features/notes/hooks/useStoreRouterSync';
import { mockNotes } from '../../../__mocks__/mockStores';

// Mock dependencies
jest.mock('../../../../store', () => ({
  useUIStore: jest.fn(),
}));

jest.mock('../../../../features/notes/hooks/useStoreRouterSync', () => ({
  useStoreRouterSync: jest.fn(),
}));

jest.mock('../../../../features/ui/components/Header', () => {
  return function MockHeader({ toggleSidebar }: { toggleSidebar: () => void }) {
    return (
      <header data-testid="header">
        <button data-testid="toggle-sidebar" onClick={toggleSidebar}>
          Toggle Sidebar
        </button>
      </header>
    );
  };
});

jest.mock('../../../../features/ui/components/Sidebar', () => {
  return function MockSidebar({
    notes,
    currentNoteId,
    onSelectNote,
    onCreateNote,
    onDeleteNote,
  }: any) {
    return (
      <div data-testid="sidebar">
        <div>Notes: {notes.length}</div>
        <div>Current: {currentNoteId}</div>
      </div>
    );
  };
});

jest.mock('../../../../features/notes/components/NoteContent', () => {
  return function MockNoteContent(props: any) {
    return (
      <div data-testid="note-content">
        <div>Note: {props.currentNote?.title || 'None'}</div>
        <div>Editing: {props.isEditing ? 'Yes' : 'No'}</div>
      </div>
    );
  };
});

describe('NotesContainer Component', () => {
  const mockToggleSidebar = jest.fn();
  
  // Default mock implementations
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock useUIStore
    (useUIStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector({
          isSidebarOpen: true,
          actions: { toggleSidebar: mockToggleSidebar },
        });
      }
      return {
        isSidebarOpen: true,
        actions: { toggleSidebar: mockToggleSidebar },
      };
    });
    
    // Mock useStoreRouterSync
    (useStoreRouterSync as jest.Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: jest.fn(),
        updateNote: jest.fn(),
        deleteNote: jest.fn(),
        setCurrentNote: jest.fn(),
        setEditedContent: jest.fn(),
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
    // Update the mock to return sidebar closed
    (useUIStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector({
          isSidebarOpen: false,
          actions: { toggleSidebar: mockToggleSidebar },
        });
      }
      return {
        isSidebarOpen: false,
        actions: { toggleSidebar: mockToggleSidebar },
      };
    });
    
    renderComponent();
    
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.getByTestId('note-content')).toBeInTheDocument();
  });

  it('should pass correct props to NoteContent', () => {
    (useStoreRouterSync as jest.Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: 'Edited content',
      actions: {
        createNote: jest.fn(),
        updateNote: jest.fn(),
        deleteNote: jest.fn(),
        setCurrentNote: jest.fn(),
        setEditedContent: jest.fn(),
      },
    });
    
    renderComponent();
    
    expect(screen.getByText('Note: Test Note 1')).toBeInTheDocument();
    expect(screen.getByText('Editing: Yes')).toBeInTheDocument();
  });

  it('should handle case when no note is selected', () => {
    (useStoreRouterSync as jest.Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      currentNote: null,
      isEditing: false,
      editedContent: null,
      actions: {
        createNote: jest.fn(),
        updateNote: jest.fn(),
        deleteNote: jest.fn(),
        setCurrentNote: jest.fn(),
        setEditedContent: jest.fn(),
      },
    });
    
    renderComponent();
    
    expect(screen.getByText('Note: None')).toBeInTheDocument();
  });

  it('should handle editing state properly', () => {
    const mockUpdateNote = jest.fn();
    const mockSetEditedContent = jest.fn();
    
    (useStoreRouterSync as jest.Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      currentNote: mockNotes[0],
      isEditing: true,
      editedContent: 'Edited content',
      actions: {
        createNote: jest.fn(),
        updateNote: mockUpdateNote,
        deleteNote: jest.fn(),
        setCurrentNote: jest.fn(),
        setEditedContent: mockSetEditedContent,
      },
    });
    
    renderComponent();
    
    // The NoteContent should receive the correct props for editing
    expect(screen.getByText('Editing: Yes')).toBeInTheDocument();
  });
});