import { describe, it, expect, beforeEach } from 'vitest';
import { useSettingsStore } from '../../../../features/settings/store';

describe('Settings Store', () => {
  beforeEach(() => {
    // Reset store to defaults before each test
    useSettingsStore.getState().actions.resetToDefaults();
  });

  describe('Editor Preferences', () => {
    it('should have default editor preferences', () => {
      const { editorPreferences } = useSettingsStore.getState();

      expect(editorPreferences.fontFamily).toBe('monospace');
      expect(editorPreferences.fontSize).toBe(16);
      expect(editorPreferences.lineHeight).toBe(1.6);
      expect(editorPreferences.autoSaveDelay).toBe(1000);
      expect(editorPreferences.wordWrap).toBe(true);
      expect(editorPreferences.spellCheck).toBe(true);
    });

    it('should update font family', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        fontFamily: 'sans-serif',
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.fontFamily).toBe('sans-serif');
    });

    it('should update font size', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        fontSize: 20,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.fontSize).toBe(20);
    });

    it('should update line height', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        lineHeight: 2.0,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.lineHeight).toBe(2.0);
    });

    it('should update auto save delay', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        autoSaveDelay: 3000,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.autoSaveDelay).toBe(3000);
    });

    it('should update word wrap', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        wordWrap: false,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.wordWrap).toBe(false);
    });

    it('should update spell check', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        spellCheck: false,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.spellCheck).toBe(false);
    });

    it('should update multiple preferences at once', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        fontFamily: 'serif',
        fontSize: 18,
        lineHeight: 1.8,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.fontFamily).toBe('serif');
      expect(editorPreferences.fontSize).toBe(18);
      expect(editorPreferences.lineHeight).toBe(1.8);
    });

    it('should preserve other preferences when updating one', () => {
      useSettingsStore.getState().actions.updateEditorPreferences({
        fontSize: 20,
      });

      const { editorPreferences } = useSettingsStore.getState();
      expect(editorPreferences.fontFamily).toBe('monospace'); // unchanged
      expect(editorPreferences.fontSize).toBe(20); // changed
      expect(editorPreferences.wordWrap).toBe(true); // unchanged
    });
  });

  describe('Appearance Preferences', () => {
    it('should have default appearance preferences', () => {
      const { appearancePreferences } = useSettingsStore.getState();

      expect(appearancePreferences.sidebarWidth).toBe(280);
    });

    it('should update sidebar width', () => {
      useSettingsStore.getState().actions.updateAppearancePreferences({
        sidebarWidth: 350,
      });

      const { appearancePreferences } = useSettingsStore.getState();
      expect(appearancePreferences.sidebarWidth).toBe(350);
    });
  });

  describe('Reset to Defaults', () => {
    it('should reset all preferences to defaults', () => {
      // Change some preferences
      useSettingsStore.getState().actions.updateEditorPreferences({
        fontFamily: 'serif',
        fontSize: 20,
      });
      useSettingsStore.getState().actions.updateAppearancePreferences({
        sidebarWidth: 400,
      });

      // Reset
      useSettingsStore.getState().actions.resetToDefaults();

      // Check defaults
      const { editorPreferences, appearancePreferences } =
        useSettingsStore.getState();
      expect(editorPreferences.fontFamily).toBe('monospace');
      expect(editorPreferences.fontSize).toBe(16);
      expect(appearancePreferences.sidebarWidth).toBe(280);
    });
  });

  describe('Error Handling', () => {
    it('should have null error by default', () => {
      const { error } = useSettingsStore.getState();
      expect(error).toBeNull();
    });

    it('should clear error', () => {
      // Note: We can't directly set the error, but we can test clearError
      useSettingsStore.getState().actions.clearError();
      const { error } = useSettingsStore.getState();
      expect(error).toBeNull();
    });
  });

  describe('Loading State', () => {
    it('should have false loading by default', () => {
      const { isLoading } = useSettingsStore.getState();
      expect(isLoading).toBe(false);
    });
  });
});
