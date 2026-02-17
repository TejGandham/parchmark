import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, cleanup, fireEvent } from '@testing-library/react';
import { act } from 'react';
import { useCommandPalette } from '../../../../features/ui/hooks/useCommandPalette';
import { useUIStore } from '../../../../features/ui/store/ui';

function TestComponent() {
  const { isOpen } = useCommandPalette();
  return <div data-testid="is-open">{String(isOpen)}</div>;
}

function renderHook() {
  return render(<TestComponent />);
}

describe('useCommandPalette', () => {
  beforeEach(() => {
    act(() => {
      useUIStore.setState({
        isPaletteOpen: false,
        paletteSearchQuery: '',
        actions: useUIStore.getState().actions,
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('starts with palette closed', () => {
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('toggles palette on Ctrl+Shift+P', () => {
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(false);

    act(() => {
      fireEvent.keyDown(window, { key: 'P', ctrlKey: true, shiftKey: true });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(true);
  });

  it('does not toggle on Ctrl+K (old shortcut)', () => {
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(false);

    act(() => {
      fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('closes palette on Ctrl+Shift+P when already open', () => {
    act(() => {
      useUIStore.getState().actions.openPalette();
    });
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(true);

    act(() => {
      fireEvent.keyDown(window, { key: 'P', ctrlKey: true, shiftKey: true });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('closes palette on Escape', () => {
    act(() => {
      useUIStore.getState().actions.openPalette();
    });
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(true);

    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('does not close on Escape when already closed', () => {
    renderHook();
    expect(useUIStore.getState().isPaletteOpen).toBe(false);

    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('does not toggle on P without modifiers', () => {
    renderHook();

    act(() => {
      fireEvent.keyDown(window, { key: 'p' });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('does not toggle on Ctrl+P without Shift', () => {
    renderHook();

    act(() => {
      fireEvent.keyDown(window, { key: 'p', ctrlKey: true });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('prevents default on Ctrl+Shift+P', () => {
    renderHook();
    const event = new KeyboardEvent('keydown', {
      key: 'P',
      ctrlKey: true,
      shiftKey: true,
      cancelable: true,
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

    act(() => {
      window.dispatchEvent(event);
    });

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('cleans up event listener on unmount', () => {
    const { unmount } = renderHook();
    unmount();

    act(() => {
      fireEvent.keyDown(window, { key: 'P', ctrlKey: true, shiftKey: true });
    });

    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });
});
