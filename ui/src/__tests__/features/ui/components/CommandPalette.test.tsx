import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { act } from 'react';
import { CommandPalette } from '../../../../features/ui/components/CommandPalette';
import { useUIStore } from '../../../../features/ui/store/ui';

function renderPalette() {
  return render(
    <ChakraProvider>
      <CommandPalette />
    </ChakraProvider>
  );
}

function openPalette() {
  act(() => {
    useUIStore.getState().actions.openPalette();
  });
}

function closePaletteViaStore() {
  act(() => {
    useUIStore.getState().actions.closePalette();
  });
}

describe('CommandPalette', () => {
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

  it('does not render when closed', () => {
    renderPalette();
    expect(screen.queryByTestId('command-palette')).not.toBeInTheDocument();
  });

  it('renders when open', () => {
    openPalette();
    renderPalette();
    expect(screen.getByTestId('command-palette')).toBeInTheDocument();
  });

  it('has correct dialog role and aria-label', () => {
    openPalette();
    renderPalette();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-label', 'Command palette');
  });

  it('auto-focuses search input on open', () => {
    const focusSpy = vi.spyOn(HTMLInputElement.prototype, 'focus');
    openPalette();
    renderPalette();
    expect(focusSpy).toHaveBeenCalled();
    focusSpy.mockRestore();
  });

  it('renders footer keyboard hints', () => {
    openPalette();
    renderPalette();
    expect(
      screen.getByText('↑↓ navigate • ↵ open • esc to close')
    ).toBeInTheDocument();
  });

  it('renders search input with placeholder', () => {
    openPalette();
    renderPalette();
    expect(screen.getByPlaceholderText('Search notes...')).toBeInTheDocument();
  });

  it('updates search query on input change', () => {
    openPalette();
    renderPalette();
    const searchInput = screen.getByTestId('command-palette-search');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    expect(useUIStore.getState().paletteSearchQuery).toBe('test query');
  });

  it('closes when backdrop is clicked', () => {
    openPalette();
    renderPalette();
    const backdrop = screen.getByTestId('command-palette-backdrop');
    fireEvent.click(backdrop);
    expect(useUIStore.getState().isPaletteOpen).toBe(false);
  });

  it('does not close when palette body is clicked', () => {
    openPalette();
    renderPalette();
    const palette = screen.getByTestId('command-palette');
    fireEvent.click(palette);
    expect(useUIStore.getState().isPaletteOpen).toBe(true);
  });

  it('clears search query on close', () => {
    openPalette();
    act(() => {
      useUIStore.getState().actions.setPaletteSearchQuery('some text');
    });
    renderPalette();
    closePaletteViaStore();
    expect(useUIStore.getState().paletteSearchQuery).toBe('');
  });

  it('renders backdrop with correct test id', () => {
    openPalette();
    renderPalette();
    expect(screen.getByTestId('command-palette-backdrop')).toBeInTheDocument();
  });
});
