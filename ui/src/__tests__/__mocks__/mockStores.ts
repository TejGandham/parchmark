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

// Auth store mocks - includes all OIDC-related fields
export const mockAuthStore = {
  isAuthenticated: true,
  user: { username: 'user', password: '' },
  token: 'mock-token',
  refreshToken: 'mock-refresh-token',
  tokenSource: 'local' as const,
  error: null,
  oidcLogoutWarning: null,
  actions: {
    login: vi.fn().mockResolvedValue(true),
    loginWithOIDC: vi.fn().mockResolvedValue(undefined),
    handleOIDCCallbackFlow: vi.fn().mockResolvedValue(true),
    logout: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
    clearOidcLogoutWarning: vi.fn(),
    checkTokenExpiration: vi.fn(),
    refreshTokens: vi.fn().mockResolvedValue(true),
  },
};

export const mockUnauthenticatedStore = {
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  tokenSource: 'local' as const,
  error: null,
  oidcLogoutWarning: null,
  actions: {
    login: vi.fn().mockResolvedValue(false),
    loginWithOIDC: vi.fn().mockResolvedValue(undefined),
    handleOIDCCallbackFlow: vi.fn().mockResolvedValue(false),
    logout: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
    clearOidcLogoutWarning: vi.fn(),
    checkTokenExpiration: vi.fn(),
    refreshTokens: vi.fn().mockResolvedValue(false),
  },
};

export const mockAuthStoreWithError = {
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  tokenSource: 'local' as const,
  error: 'Invalid username or password',
  oidcLogoutWarning: null,
  actions: {
    login: vi.fn().mockResolvedValue(false),
    loginWithOIDC: vi.fn().mockResolvedValue(undefined),
    handleOIDCCallbackFlow: vi.fn().mockResolvedValue(false),
    logout: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
    clearOidcLogoutWarning: vi.fn(),
    checkTokenExpiration: vi.fn(),
    refreshTokens: vi.fn().mockResolvedValue(false),
  },
};
