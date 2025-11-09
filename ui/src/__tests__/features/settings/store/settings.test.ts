import { vi } from 'vitest';
import { act } from 'react';
import {
  useSettingsStore,
  SettingsState,
} from '../../../../features/settings/store/settings';

describe('Settings Store', () => {
  let store: SettingsState;

  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useSettingsStore.setState({
        editorPreferences: {
          fontFamily: 'monospace',
          fontSize: 16,
          lineHeight: 1.6,
          autoSaveDelay: 1000,
          wordWrap: true,
          spellCheck: true,
        },
        appearancePreferences: {
          sidebarWidth: 280,
        },
        isLoading: false,
        error: null,
        actions: useSettingsStore.getState().actions,
      });
    });

    store = useSettingsStore.getState();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with default editor preferences', () => {
      expect(store.editorPreferences).toEqual({
        fontFamily: 'monospace',
        fontSize: 16,
        lineHeight: 1.6,
        autoSaveDelay: 1000,
        wordWrap: true,
        spellCheck: true,
      });
    });

    it('should initialize with default appearance preferences', () => {
      expect(store.appearancePreferences).toEqual({
        sidebarWidth: 280,
      });
    });

    it('should initialize with no error', () => {
      expect(store.error).toBeNull();
      expect(store.isLoading).toBe(false);
    });
  });

  describe('Editor Preferences', () => {
    it('should update font family', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ fontFamily: 'sans-serif' });
      });

      const newState = useSettingsStore.getState();
      expect(newState.editorPreferences.fontFamily).toBe('sans-serif');
      expect(newState.error).toBeNull();
    });

    it('should update font size', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ fontSize: 18 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.editorPreferences.fontSize).toBe(18);
      expect(newState.error).toBeNull();
    });

    it('should update line height', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ lineHeight: 1.8 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.editorPreferences.lineHeight).toBe(1.8);
      expect(newState.error).toBeNull();
    });

    it('should update auto-save delay', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ autoSaveDelay: 3000 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.editorPreferences.autoSaveDelay).toBe(3000);
      expect(newState.error).toBeNull();
    });

    it('should toggle word wrap', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ wordWrap: false });
      });

      let newState = useSettingsStore.getState();
      expect(newState.editorPreferences.wordWrap).toBe(false);

      act(() => {
        actions.updateEditorPreferences({ wordWrap: true });
      });

      newState = useSettingsStore.getState();
      expect(newState.editorPreferences.wordWrap).toBe(true);
    });

    it('should toggle spell check', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({ spellCheck: false });
      });

      let newState = useSettingsStore.getState();
      expect(newState.editorPreferences.spellCheck).toBe(false);

      act(() => {
        actions.updateEditorPreferences({ spellCheck: true });
      });

      newState = useSettingsStore.getState();
      expect(newState.editorPreferences.spellCheck).toBe(true);
    });

    it('should update multiple editor preferences at once', () => {
      const { actions } = store;

      act(() => {
        actions.updateEditorPreferences({
          fontFamily: 'serif',
          fontSize: 20,
          lineHeight: 2.0,
        });
      });

      const newState = useSettingsStore.getState();
      expect(newState.editorPreferences.fontFamily).toBe('serif');
      expect(newState.editorPreferences.fontSize).toBe(20);
      expect(newState.editorPreferences.lineHeight).toBe(2.0);
      // Other preferences should remain unchanged
      expect(newState.editorPreferences.autoSaveDelay).toBe(1000);
      expect(newState.editorPreferences.wordWrap).toBe(true);
    });
  });

  describe('Appearance Preferences', () => {
    it('should update sidebar width', () => {
      const { actions } = store;

      act(() => {
        actions.updateAppearancePreferences({ sidebarWidth: 350 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.appearancePreferences.sidebarWidth).toBe(350);
      expect(newState.error).toBeNull();
    });

    it('should handle minimum sidebar width', () => {
      const { actions } = store;

      act(() => {
        actions.updateAppearancePreferences({ sidebarWidth: 200 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.appearancePreferences.sidebarWidth).toBe(200);
    });

    it('should handle maximum sidebar width', () => {
      const { actions } = store;

      act(() => {
        actions.updateAppearancePreferences({ sidebarWidth: 400 });
      });

      const newState = useSettingsStore.getState();
      expect(newState.appearancePreferences.sidebarWidth).toBe(400);
    });
  });

  describe('Reset to Defaults', () => {
    it('should reset all preferences to defaults', () => {
      const { actions } = store;

      // Change some preferences
      act(() => {
        actions.updateEditorPreferences({
          fontFamily: 'serif',
          fontSize: 24,
          lineHeight: 2.0,
          autoSaveDelay: 5000,
          wordWrap: false,
          spellCheck: false,
        });
        actions.updateAppearancePreferences({ sidebarWidth: 400 });
      });

      // Verify changes were applied
      let newState = useSettingsStore.getState();
      expect(newState.editorPreferences.fontFamily).toBe('serif');
      expect(newState.appearancePreferences.sidebarWidth).toBe(400);

      // Reset to defaults
      act(() => {
        actions.resetToDefaults();
      });

      newState = useSettingsStore.getState();
      expect(newState.editorPreferences).toEqual({
        fontFamily: 'monospace',
        fontSize: 16,
        lineHeight: 1.6,
        autoSaveDelay: 1000,
        wordWrap: true,
        spellCheck: true,
      });
      expect(newState.appearancePreferences).toEqual({
        sidebarWidth: 280,
      });
      expect(newState.error).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should clear error', () => {
      const { actions } = store;

      // Manually set an error
      act(() => {
        useSettingsStore.setState({ error: 'Test error' });
      });

      expect(useSettingsStore.getState().error).toBe('Test error');

      // Clear the error
      act(() => {
        actions.clearError();
      });

      expect(useSettingsStore.getState().error).toBeNull();
    });

    it('should clear error when updating preferences', () => {
      const { actions } = store;

      // Manually set an error
      act(() => {
        useSettingsStore.setState({ error: 'Test error' });
      });

      expect(useSettingsStore.getState().error).toBe('Test error');

      // Update preferences should clear error
      act(() => {
        actions.updateEditorPreferences({ fontSize: 18 });
      });

      expect(useSettingsStore.getState().error).toBeNull();
    });
  });
});
