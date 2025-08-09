import { renderHook, act } from '@testing-library/react';
import { MemoryRouter, useNavigate, useParams, useLocation } from 'react-router-dom';
import { useStoreRouterSync } from '../../../../features/notes/hooks/useStoreRouterSync';
import { useNotesStore } from '../../../../store';
import { mockNotes, mockNotesStore } from '../../../__mocks__/mockStores';

// Mock the modules
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn(),
  useNavigate: jest.fn(),
  useLocation: jest.fn(),
}));

jest.mock('../../../../store', () => ({
  useNotesStore: jest.fn(),
}));

describe('useStoreRouterSync', () => {
  // Mock react-router hooks
  const mockNavigate = jest.fn();
  const mockParams = { noteId: undefined };
  const mockLocation = { pathname: '/notes' };

  // Setup test harness
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/notes']}>{children}</MemoryRouter>
  );

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mocks
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    (require('react-router-dom').useParams as jest.Mock).mockReturnValue(
      mockParams
    );
    (require('react-router-dom').useLocation as jest.Mock).mockReturnValue(
      mockLocation
    );

    // Mock the store
    (useNotesStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector(mockNotesStore);
      }
      return mockNotesStore;
    });
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
    (require('react-router-dom').useLocation as jest.Mock).mockReturnValue({
      pathname: '/notes',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-1', {
      replace: true,
    });
  });

  it('should navigate to not-found if noteId in URL doesnt exist', () => {
    // Mock params with non-existent note ID and an empty notes array
    (require('react-router-dom').useParams as jest.Mock).mockReturnValue({
      noteId: 'non-existent',
    });

    // Mock the store to return no notes, which would trigger the not-found redirect
    (useNotesStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector({
          notes: [],
          currentNoteId: null,
          editedContent: null,
          actions: mockNotesStore.actions,
        });
      }
      return {
        notes: [],
        currentNoteId: null,
        editedContent: null,
        actions: mockNotesStore.actions,
      };
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    expect(mockNavigate).toHaveBeenCalledWith('/not-found', { replace: true });
  });

  it('should update store when valid noteId is in URL', () => {
    // Mock params with existing note ID
    (require('react-router-dom').useParams as jest.Mock).mockReturnValue({
      noteId: 'note-2',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    expect(mockNotesStore.actions.setCurrentNote).toHaveBeenCalledWith(
      'note-2'
    );
  });

  it('should handle createNote action correctly', () => {
    mockNotesStore.actions.createNote.mockReturnValue('new-note-id');

    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    act(() => {
      result.current.actions.createNote();
    });

    expect(mockNotesStore.actions.createNote).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/notes/new-note-id');
  });

  it('should handle deleteNote action with correct navigation', () => {
    // Setup the findNextNoteId functionality test
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    act(() => {
      // Delete current note
      result.current.actions.deleteNote('note-1');
    });

    expect(mockNotesStore.actions.deleteNote).toHaveBeenCalledWith('note-1');
    // Should navigate to the next note
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
  });

  it('should handle setCurrentNote action with navigation', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    act(() => {
      result.current.actions.setCurrentNote('note-2');
    });

    expect(mockNotesStore.actions.setCurrentNote).toHaveBeenCalledWith(
      'note-2'
    );
    expect(mockNavigate).toHaveBeenCalledWith('/notes/note-2');
  });

  it('should pass through updateNote action', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    act(() => {
      result.current.actions.updateNote('note-1', 'New content');
    });

    expect(mockNotesStore.actions.updateNote).toHaveBeenCalledWith(
      'note-1',
      'New content'
    );
  });

  it('should pass through setEditedContent action', () => {
    const { result } = renderHook(() => useStoreRouterSync(), { wrapper });

    act(() => {
      result.current.actions.setEditedContent('Edited content');
    });

    expect(mockNotesStore.actions.setEditedContent).toHaveBeenCalledWith(
      'Edited content'
    );
  });

  it('should handle empty notes array correctly', () => {
    // Mock empty notes store
    (useNotesStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector({
          notes: [],
          currentNoteId: null,
          editedContent: null,
          actions: mockNotesStore.actions,
        });
      }
      return {
        notes: [],
        currentNoteId: null,
        editedContent: null,
        actions: mockNotesStore.actions,
      };
    });

    // Mock params with a non-existent ID to trigger path for non-existent note
    (require('react-router-dom').useParams as jest.Mock).mockReturnValue({
      noteId: 'non-existent',
    });

    // Mock location to trigger the navigation effect
    (require('react-router-dom').useLocation as jest.Mock).mockReturnValue({
      pathname: '/notes/non-existent',
    });

    renderHook(() => useStoreRouterSync(), { wrapper });

    // Should navigate to not-found when no notes are available with a non-existent ID
    expect(mockNavigate).toHaveBeenCalledWith('/not-found', { replace: true });
  });

  it('should handle case when storeActions is undefined during initial load', () => {
    // Mock the useNotesStore to simulate initial load with undefined actions
    (useNotesStore as jest.Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        // When the selector is looking for actions, return undefined
        if (selector({ actions: undefined }) === undefined) {
          return undefined;
        }
        // For other selectors, return normal data
        return selector({
          notes: mockNotes,
          currentNoteId: null,
          editedContent: null,
          actions: undefined, // This simulates the error condition
        });
      }
      return {
        notes: mockNotes,
        currentNoteId: null,
        editedContent: null,
        actions: undefined,
      };
    });

    // Mock params with existing note ID
    (require('react-router-dom').useParams as jest.Mock).mockReturnValue({
      noteId: 'note-1',
    });

    // This should not throw an error despite actions being undefined
    renderHook(() => useStoreRouterSync(), { wrapper });

    // We're not expecting any specific behavior here, just that it doesn't crash
    // The component should handle the undefined actions gracefully
    expect(true).toBe(true);
  });
});

