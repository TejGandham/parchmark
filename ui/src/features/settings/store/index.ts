import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';

export type FontFamily = 'monospace' | 'sans-serif' | 'serif';

export interface EditorPreferences {
  fontFamily: FontFamily;
  fontSize: number;
  lineHeight: number;
  autoSaveDelay: number;
  wordWrap: boolean;
  spellCheck: boolean;
}

export interface AppearancePreferences {
  sidebarWidth: number;
}

interface SettingsState {
  editorPreferences: EditorPreferences;
  appearancePreferences: AppearancePreferences;
  isLoading: boolean;
  error: string | null;
}

interface SettingsActions {
  updateEditorPreferences: (prefs: Partial<EditorPreferences>) => void;
  updateAppearancePreferences: (prefs: Partial<AppearancePreferences>) => void;
  resetToDefaults: () => void;
  clearError: () => void;
}

interface SettingsStore extends SettingsState {
  actions: SettingsActions;
}

const DEFAULT_EDITOR_PREFERENCES: EditorPreferences = {
  fontFamily: 'monospace',
  fontSize: 16,
  lineHeight: 1.6,
  autoSaveDelay: 1000,
  wordWrap: true,
  spellCheck: true,
};

const DEFAULT_APPEARANCE_PREFERENCES: AppearancePreferences = {
  sidebarWidth: 280,
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      editorPreferences: DEFAULT_EDITOR_PREFERENCES,
      appearancePreferences: DEFAULT_APPEARANCE_PREFERENCES,
      isLoading: false,
      error: null,

      actions: {
        updateEditorPreferences: (prefs) =>
          set((state) => ({
            editorPreferences: { ...state.editorPreferences, ...prefs },
          })),

        updateAppearancePreferences: (prefs) =>
          set((state) => ({
            appearancePreferences: { ...state.appearancePreferences, ...prefs },
          })),

        resetToDefaults: () =>
          set({
            editorPreferences: DEFAULT_EDITOR_PREFERENCES,
            appearancePreferences: DEFAULT_APPEARANCE_PREFERENCES,
          }),

        clearError: () => set({ error: null }),
      },
    }),
    {
      name: STORAGE_KEYS.SETTINGS,
      partialize: (state) => ({
        editorPreferences: state.editorPreferences,
        appearancePreferences: state.appearancePreferences,
      }),
    }
  )
);
