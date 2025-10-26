import { vi } from 'vitest';
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
  isDarkMode: false,
  notesSortBy: 'lastModified' as const,
  notesSearchQuery: '',
  notesGroupByDate: true,
  actions: {
    toggleSidebar: vi.fn(),
    toggleDarkMode: vi.fn(),
    setNotesSortBy: vi.fn(),
    setNotesSearchQuery: vi.fn(),
    setNotesGroupByDate: vi.fn(),
  },
};

export const mockNotesStore = {
  notes: mockNotes,
  currentNoteId: 'note-1',
  editedContent: null,
  actions: {
    fetchNotes: vi.fn(),
    createNote: vi.fn().mockReturnValue('note-3'),
    updateNote: vi.fn(),
    deleteNote: vi.fn(),
    setCurrentNote: vi.fn(),
    setEditedContent: vi.fn(),
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
    fetchNotes: vi.fn(),
    createNote: vi.fn().mockReturnValue('note-new'),
    updateNote: vi.fn(),
    deleteNote: vi.fn(),
    setCurrentNote: vi.fn(),
    setEditedContent: vi.fn(),
  },
};

// Auth store mocks
export const mockAuthStore = {
  isAuthenticated: true,
  user: { username: 'user', password: '' },
  token: 'mock-token',
  error: null,
  actions: {
    login: vi.fn().mockReturnValue(true),
    logout: vi.fn(),
    clearError: vi.fn(),
    checkTokenExpiration: vi.fn(),
  },
};

export const mockUnauthenticatedStore = {
  isAuthenticated: false,
  user: null,
  token: null,
  error: null,
  actions: {
    login: vi.fn().mockReturnValue(false),
    logout: vi.fn(),
    clearError: vi.fn(),
    checkTokenExpiration: vi.fn(),
  },
};

export const mockAuthStoreWithError = {
  isAuthenticated: false,
  user: null,
  token: null,
  error: 'Invalid username or password',
  actions: {
    login: vi.fn().mockReturnValue(false),
    logout: vi.fn(),
    clearError: vi.fn(),
    checkTokenExpiration: vi.fn(),
  },
};
