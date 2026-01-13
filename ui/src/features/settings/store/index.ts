import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';

interface SettingsState {
  isLoading: boolean;
  error: string | null;
}

interface SettingsActions {
  clearError: () => void;
}

interface SettingsStore extends SettingsState {
  actions: SettingsActions;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      isLoading: false,
      error: null,

      actions: {
        clearError: () => set({ error: null }),
      },
    }),
    {
      name: STORAGE_KEYS.SETTINGS,
      partialize: () => ({}),
    }
  )
);
