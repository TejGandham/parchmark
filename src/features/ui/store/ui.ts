import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';

export type UIState = {
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  actions: {
    toggleSidebar: () => void;
    toggleDarkMode: () => void;
  };
};

export const useUIStore = create<UIState>()(
  persist(
    immer((set) => ({
      isSidebarOpen: true,
      isDarkMode: false,
      actions: {
        toggleSidebar: () =>
          set((state) => {
            state.isSidebarOpen = !state.isSidebarOpen;
          }),
        toggleDarkMode: () =>
          set((state) => {
            state.isDarkMode = !state.isDarkMode;
          }),
      },
    })),
    { name: 'parchmark-ui' }
  )
);
