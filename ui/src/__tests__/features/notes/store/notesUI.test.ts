// ui/src/__tests__/features/notes/store/notesUI.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useNotesUIStore } from '../../../../features/notes/store';

describe('useNotesUIStore', () => {
  beforeEach(() => {
    useNotesUIStore.setState({ editedContent: null });
  });

  it('should initialize with null editedContent', () => {
    const state = useNotesUIStore.getState();
    expect(state.editedContent).toBeNull();
  });

  it('should set editedContent', () => {
    const { setEditedContent } = useNotesUIStore.getState();
    setEditedContent('# New Content');
    expect(useNotesUIStore.getState().editedContent).toBe('# New Content');
  });

  it('should clear editedContent when set to null', () => {
    const { setEditedContent } = useNotesUIStore.getState();
    setEditedContent('# Some Content');
    setEditedContent(null);
    expect(useNotesUIStore.getState().editedContent).toBeNull();
  });
});
