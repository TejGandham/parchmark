import { useEffect } from 'react';
import { useUIStore } from '../store/ui';

export const useCommandPalette = () => {
  const isPaletteOpen = useUIStore((state) => state.isPaletteOpen);
  const openPalette = useUIStore((state) => state.actions.openPalette);
  const closePalette = useUIStore((state) => state.actions.closePalette);
  const togglePalette = useUIStore((state) => state.actions.togglePalette);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && !e.shiftKey && e.key === '.') {
        e.preventDefault();
        togglePalette();
      }

      if (e.key === 'Escape' && isPaletteOpen) {
        e.preventDefault();
        closePalette();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPaletteOpen, togglePalette, closePalette]);

  return {
    isOpen: isPaletteOpen,
    open: openPalette,
    close: closePalette,
    toggle: togglePalette,
  };
};
