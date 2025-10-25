import { vi, Mock } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  MemoryRouter,
  useNavigate,
  useParams,
  useLocation,
} from 'react-router-dom';
import { useStoreRouterSync } from '../../../../features/notes/hooks/useStoreRouterSync';
import { useNotesStore } from '../../../../store';
import { useAuthStore } from '../../../../features/auth/store';
import {
  mockNotes,
  mockNotesStore,
  mockAuthStore,
} from '../../../__mocks__/mockStores';

// Mock the modules
vi.mock('react-router-dom', async () => ({
  ...(await import('react-router-dom')),
  useParams: vi.fn(),
  useNavigate: vi.fn(),
  useLocation: vi.fn(),
}));

vi.mock('../../../../features/notes/store');
vi.mock('../../../../features/auth/store');

describe('useStoreRouterSync', () => {
  // Mock react-router hooks
  const mockNavigate = vi.fn();
  const mockParams = { noteId: undefined };
  const mockLocation = { pathname: '/notes' };

  // Setup test harness
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/notes']}>{children}</MemoryRouter>
  );

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mocks
    (useNavigate as Mock).mockReturnValue(mockNavigate);
    (useParams as Mock).mockReturnValue(mockParams);
    (useLocation as Mock).mockReturnValue(mockLocation);

    // Mock the stores
    (useNotesStore as Mock).mockReturnValue(mockNotesStore);
    (useAuthStore as Mock).mockReturnValue(mockAuthStore);
  });

  it('should return the correct state with route params', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    expect(result.current.notes).toEqual(mockNotes);
    expect(result.current.currentNoteId).toBe('note-1');
    expect(result.current.currentNote).toEqual(mockNotes[0]);
    expect(result.current.isEditing).toBe(false);
    expect(result.current.editedContent).toBe(null);
    expect(typeof result.current.actions.createNote).toBe('function');
    expect(typeof result.current.actions.updateNote).toBe('function');
    expect(typeof result.current.actions.deleteNote).toBe('function');
    expect(typeof result.current.actions.setCurrentNote).toBe('function');
    expect(typeof result.current.actions.setEditedContent).toBe('function');
  });

  it('should navigate to first note when at /notes route with notes available', () => {
    // Mock location to trigger the navigation effect
    (useLocation as Mock).mockReturnValue({
      pathname: '/notes',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-1', {
      replace: true,
    });
  });

  it('should navigate to first available note if noteId in URL doesnt exist', () => {
    // Mock params with non-existent note ID but with notes available
    (useParams as Mock).mockReturnValue({
      noteId: 'non-existent',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    // Since the noteId doesn't exist but notes are available, it should navigate to first note
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-1', {
      replace: true,
    });
  });

  it('should handle createNote action correctly', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // Clear any navigation calls from initial render, but reset the mock return value
    mockNavigate.mockClear();
    mockNotesStore.actions.createNote.mockClear();
    mockNotesStore.actions.createNote.mockReturnValue('note-3');

    await act(async () => {
      await result.current.actions.createNote();
    });

    expect(mockNotesStore.actions.createNote).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-3');
  });

  it('should handle deleteNote action with correct navigation', async () => {
    // Setup the findNextNoteId functionality test
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // Clear any navigation calls from initial render
    mockNavigate.mockClear();
    mockNotesStore.actions.deleteNote.mockClear();

    await act(async () => {
      // Delete current note
      await result.current.actions.deleteNote('note-1');
    });

    expect(mockNotesStore.actions.deleteNote).toHaveBeenCalledWith('note-1');
    // Should navigate to the next note
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
  });

  it('should handle empty notes array correctly when noteId is non-existent', () => {
    // Mock empty notes store
    (useNotesStore as Mock).mockReturnValue({
      notes: [],
      currentNoteId: null,
      editedContent: null,
      actions: mockNotesStore.actions,
    });

    // Mock params with a non-existent ID to trigger path for non-existent note
    (useParams as Mock).mockReturnValue({
      noteId: 'non-existent',
    });

    // Mock location to trigger the navigation effect
    (useLocation as Mock).mockReturnValue({
      pathname: '/notes/non-existent',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    // When no notes are available and noteId doesn't exist, no navigation should happen
    // The component should handle the empty state gracefully
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle case when storeActions is undefined during initial load', () => {
    // Mock the useNotesStore to simulate initial load with undefined actions
    (useNotesStore as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      editedContent: null,
      actions: undefined,
    });

    // Mock params with existing note ID
    (useParams as Mock).mockReturnValue({
      noteId: 'note-1',
    });

    // This should not throw an error despite actions being undefined
    renderHook(() => useStoreRouterSync(), { wrapper });

    // We're not expecting any specific behavior here, just that it doesn't crash
    // The component should handle the undefined actions gracefully
    expect(true).toBe(true);
  });

  it('should handle createNote when no new ID is returned', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // Mock createNote to return null (no ID)
    mockNotesStore.actions.createNote.mockReturnValue(null);
    mockNavigate.mockClear();

    await act(async () => {
      const newId = await result.current.actions.createNote();
      expect(newId).toBeNull();
    });

    expect(mockNotesStore.actions.createNote).toHaveBeenCalled();
    // Should not navigate when no ID is returned
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle deleteNote when not current note', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    mockNavigate.mockClear();
    mockNotesStore.actions.deleteNote.mockClear();

    await act(async () => {
      // Delete a note that is not the current note
      await result.current.actions.deleteNote('note-2');
    });

    expect(mockNotesStore.actions.deleteNote).toHaveBeenCalledWith('note-2');
    // Should not navigate when deleting non-current note
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle actions when storeActions is null', async () => {
    (useNotesStore as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      editedContent: null,
      actions: null,
    });

    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // All actions should handle null storeActions gracefully
    const createResult = await result.current.actions.createNote();
    expect(createResult).toBeNull();

    await result.current.actions.deleteNote('note-1');
    await result.current.actions.updateNote('note-1', 'content');
    result.current.actions.setEditedContent('content');

    // Should not throw errors
    expect(true).toBe(true);
  });

  it('should handle setCurrentNote when storeActions is available', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    mockNavigate.mockClear();
    mockNotesStore.actions.setCurrentNote.mockClear();

    act(() => {
      result.current.actions.setCurrentNote('note-2');
    });

    expect(mockNotesStore.actions.setCurrentNote).toHaveBeenCalledWith(
      'note-2'
    );
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
  });

  it('should call setCurrentNote when navigating to existing note via URL', () => {
    // Setup with valid noteId in params that exists in notes
    (useParams as Mock).mockReturnValue({
      noteId: 'note-2',
    });

    (useLocation as Mock).mockReturnValue({
      pathname: '/notes/note-2',
    });

    mockNavigate.mockClear();
    mockNotesStore.actions.setCurrentNote.mockClear();

    renderHook(() => useStoreRouterSync(), { wrapper });

    // Should call setCurrentNote with the noteId from URL
    expect(mockNotesStore.actions.setCurrentNote).toHaveBeenCalledWith(
      'note-2'
    );
    // Should not navigate since note exists
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should not process navigation when notes is not an array', () => {
    // Mock notes store with non-array notes to trigger early return
    (useNotesStore as Mock).mockReturnValue({
      notes: null, // Not an array
      currentNoteId: 'note-1',
      editedContent: null,
      actions: mockNotesStore.actions,
    });

    (useParams as Mock).mockReturnValue({
      noteId: 'note-1',
    });

    mockNavigate.mockClear();

    renderHook(() => useStoreRouterSync(), { wrapper });

    // Should not navigate when notes is not an array
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should not call setCurrentNote when storeActions is undefined', () => {
    // Mock the useNotesStore to simulate undefined actions
    (useNotesStore as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: null,
      editedContent: null,
      actions: undefined,
    });

    // Mock params with existing note ID
    (useParams as Mock).mockReturnValue({
      noteId: 'note-1',
    });

    (useLocation as Mock).mockReturnValue({
      pathname: '/notes/note-1',
    });

    mockNavigate.mockClear();

    renderHook(() => useStoreRouterSync(), { wrapper });

    // Should not attempt to call setCurrentNote when actions are undefined
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle safeStoreAction with functions that are not defined', async () => {
    // Mock store with missing functions in actions
    (useNotesStore as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      editedContent: null,
      actions: {
        // Missing updateNote and setEditedContent
        fetchNotes: mockNotesStore.actions.fetchNotes,
        createNote: mockNotesStore.actions.createNote,
        deleteNote: mockNotesStore.actions.deleteNote,
        setCurrentNote: mockNotesStore.actions.setCurrentNote,
      },
    });

    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // These should not throw errors even when the functions are undefined
    const updateResult = await result.current.actions.updateNote(
      'note-1',
      'content'
    );
    expect(updateResult).toBeUndefined();

    const setContentResult =
      await result.current.actions.setEditedContent('content');
    expect(setContentResult).toBeUndefined();
  });

  it('should handle setCurrentNote with null ID', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    mockNavigate.mockClear();
    mockNotesStore.actions.setCurrentNote.mockClear();

    act(() => {
      result.current.actions.setCurrentNote(null);
    });

    expect(mockNotesStore.actions.setCurrentNote).toHaveBeenCalledWith(null);
    expect(mockNavigate).toHaveBeenCalledWith('/notes');
  });

  it('should handle async store actions that return values', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // Mock createNote to return a promise with an ID
    mockNotesStore.actions.createNote.mockResolvedValue('new-note-id');

    const noteId = await act(async () => {
      return await result.current.actions.createNote();
    });

    expect(noteId).toBe('new-note-id');
    expect(mockNotesStore.actions.createNote).toHaveBeenCalled();
  });

  it('should handle setCurrentNote when storeActions setCurrentNote is not a function', () => {
    // Mock store with invalid setCurrentNote
    (useNotesStore as Mock).mockReturnValue({
      notes: mockNotes,
      currentNoteId: 'note-1',
      editedContent: null,
      actions: {
        ...mockNotesStore.actions,
        fetchNotes: mockNotesStore.actions.fetchNotes,
        setCurrentNote: 'not-a-function', // Invalid function
      },
    });

    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    mockNavigate.mockClear();

    act(() => {
      result.current.actions.setCurrentNote('note-2');
    });

    // Should still navigate even if store setCurrentNote fails
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
  });

  it('should preserve edit mode when creating a new note', async () => {
    // This test ensures that the bug where new notes don't launch in edit mode is fixed
    // The bug was: routing effect called setCurrentNote which cleared editedContent

    // Mock store with editedContent set (as if createNote was just called)
    (useNotesStore as Mock).mockReturnValue({
      notes: [
        ...mockNotes,
        { id: 'note-3', title: 'New Note', content: '# New Note\n\n' },
      ],
      currentNoteId: 'note-3', // Already set as current by createNote
      editedContent: '# New Note\n\n', // Set by createNote
      actions: mockNotesStore.actions,
    });

    // Mock params to show we're navigating to the new note
    (useParams as Mock).mockReturnValue({
      noteId: 'note-3',
    });

    (useLocation as Mock).mockReturnValue({
      pathname: '/notes/note-3',
    });

    mockNotesStore.actions.setCurrentNote.mockClear();

    renderHook(() => useStoreRouterSync(), { wrapper });

    // The key fix: setCurrentNote should NOT be called because note-3 is already current
    // This prevents editedContent from being cleared
    expect(mockNotesStore.actions.setCurrentNote).not.toHaveBeenCalled();
  });

  it('should successfully call updateNote through safeStoreAction', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    // Mock updateNote to return a value
    mockNotesStore.actions.updateNote.mockResolvedValue({
      id: 'note-1',
      title: 'Updated',
      content: '# Updated\n\nUpdated content',
      createdAt: '2023-01-01',
      updatedAt: '2023-01-02',
    });

    const updatedNote = await act(async () => {
      return await result.current.actions.updateNote(
        'note-1',
        'Updated content'
      );
    });

    expect(mockNotesStore.actions.updateNote).toHaveBeenCalledWith(
      'note-1',
      'Updated content'
    );
    expect(updatedNote).toBeDefined();
  });

  it('should successfully call setEditedContent through safeStoreAction', async () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    mockNotesStore.actions.setEditedContent.mockClear();

    await act(async () => {
      await result.current.actions.setEditedContent('New content');
    });

    expect(mockNotesStore.actions.setEditedContent).toHaveBeenCalledWith(
      'New content'
    );
  });
});
