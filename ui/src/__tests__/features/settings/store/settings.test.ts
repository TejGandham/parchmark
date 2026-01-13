import { describe, it, expect } from 'vitest';
import { useSettingsStore } from '../../../../features/settings/store';

describe('Settings Store', () => {
  describe('Error Handling', () => {
    it('should have null error by default', () => {
      const { error } = useSettingsStore.getState();
      expect(error).toBeNull();
    });

    it('should clear error', () => {
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
