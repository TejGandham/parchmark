import { Note } from '../../../types';

export const mockNotes: Note[] = [
  {
    id: 'note-1',
    title: 'Test Note 1',
    content: '# Test Note 1\n\nThis is test note 1 content.',
    createdAt: '2023-01-01T00:00:00.000Z',
    updatedAt: '2023-01-01T00:00:00.000Z',
  },
  {
    id: 'note-2',
    title: 'Test Note 2',
    content: '# Test Note 2\n\nThis is test note 2 content.',
    createdAt: '2023-01-02T00:00:00.000Z',
    updatedAt: '2023-01-02T00:00:00.000Z',
  },
];

export const mockUIStore = {
  isSidebarOpen: true,
  actions: {
    toggleSidebar: jest.fn(),
  },
};

export const mockNotesStore = {
  notes: mockNotes,
  currentNoteId: 'note-1',
  editedContent: null,
  actions: {
    createNote: jest.fn().mockReturnValue('note-3'),
    updateNote: jest.fn(),
    deleteNote: jest.fn(),
    setCurrentNote: jest.fn(),
    setEditedContent: jest.fn(),
  },
};

// For custom hook testing
export const mockNotesStoreWithEditing = {
  ...mockNotesStore,
  editedContent: '# Edited Note\n\nThis is edited content.',
};

export const mockEmptyNotesStore = {
  notes: [],
  currentNoteId: null,
  editedContent: null,
  actions: {
    createNote: jest.fn().mockReturnValue('note-new'),
    updateNote: jest.fn(),
    deleteNote: jest.fn(),
    setCurrentNote: jest.fn(),
    setEditedContent: jest.fn(),
  },
};