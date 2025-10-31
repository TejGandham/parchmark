import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';
import { handleError } from '../../../utils/errorHandler';

export interface EditorPreferences {
  fontFamily: 'monospace' | 'sans-serif' | 'serif';
  fontSize: number;
  lineHeight: number;
  autoSaveDelay: number;
  showLineNumbers: boolean;
  wordWrap: boolean;
  spellCheck: boolean;
}

export interface AppearancePreferences {
  sidebarWidth: number;
}

export type SettingsState = {
  editorPreferences: EditorPreferences;
  appearancePreferences: AppearancePreferences;
  isLoading: boolean;
  error: string | null;
  actions: {
    updateEditorPreferences: (preferences: Partial<EditorPreferences>) => void;
    updateAppearancePreferences: (
      preferences: Partial<AppearancePreferences>
    ) => void;
    resetToDefaults: () => void;
    clearError: () => void;
  };
};

const defaultEditorPreferences: EditorPreferences = {
  fontFamily: 'monospace',
  fontSize: 16,
  lineHeight: 1.6,
  autoSaveDelay: 1000,
  showLineNumbers: false,
  wordWrap: true,
  spellCheck: true,
};

const defaultAppearancePreferences: AppearancePreferences = {
  sidebarWidth: 280,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    immer((set) => ({
      editorPreferences: defaultEditorPreferences,
      appearancePreferences: defaultAppearancePreferences,
      isLoading: false,
      error: null,
      actions: {
        updateEditorPreferences: (preferences) => {
          try {
            set((state) => {
              state.editorPreferences = {
                ...state.editorPreferences,
                ...preferences,
              };
              state.error = null;
            });
          } catch (error: unknown) {
            const appError = handleError(error);
            set((state) => {
              state.error = appError.message;
            });
          }
        },

        updateAppearancePreferences: (preferences) => {
          try {
            set((state) => {
              state.appearancePreferences = {
                ...state.appearancePreferences,
                ...preferences,
              };
              state.error = null;
            });
          } catch (error: unknown) {
            const appError = handleError(error);
            set((state) => {
              state.error = appError.message;
            });
          }
        },

        resetToDefaults: () => {
          set((state) => {
            state.editorPreferences = defaultEditorPreferences;
            state.appearancePreferences = defaultAppearancePreferences;
            state.error = null;
          });
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },
      },
    })),
    {
      name: STORAGE_KEYS.SETTINGS,
      partialize: (state) => ({
        editorPreferences: state.editorPreferences,
        appearancePreferences: state.appearancePreferences,
      }),
    }
  )
);
