import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { act } from 'react';
import { ExplorerToolbar } from '../../../../features/notes/components/ExplorerToolbar';
import { useUIStore } from '../../../../features/ui/store/ui';

describe('ExplorerToolbar', () => {
  const defaultProps = {
    totalNotes: 42,
    onCreateNote: vi.fn(),
    isCreating: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    act(() => {
      useUIStore.setState({
        notesSortBy: 'lastModified',
        notesSortDirection: 'desc',
        notesSearchQuery: '',
        actions: useUIStore.getState().actions,
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  function renderToolbar(props: Partial<typeof defaultProps> = {}) {
    return render(
      <ChakraProvider>
        <ExplorerToolbar {...defaultProps} {...props} />
      </ChakraProvider>
    );
  }

  it('renders search input with placeholder', () => {
    renderToolbar();
    expect(screen.getByPlaceholderText('Search notes…')).toBeInTheDocument();
  });

  it('renders sort button showing current sort label', () => {
    renderToolbar();
    const sortBtn = screen.getByTestId('explorer-sort-btn');
    expect(sortBtn).toHaveTextContent('Modified');
  });

  it('renders direction toggle button', () => {
    renderToolbar();
    const dirBtn = screen.getByTestId('explorer-sort-dir');
    expect(dirBtn).toHaveTextContent('↓');
  });

  it('renders New Note button', () => {
    renderToolbar();
    const createBtn = screen.getByTestId('explorer-create-btn');
    expect(createBtn).toHaveTextContent('New Note');
  });

  it('renders note count text', () => {
    renderToolbar();
    expect(screen.getByText('42 notes')).toBeInTheDocument();
  });

  it('clicking sort button cycles to next option', () => {
    renderToolbar();
    const sortBtn = screen.getByTestId('explorer-sort-btn');
    expect(sortBtn).toHaveTextContent('Modified');
    fireEvent.click(sortBtn);
    expect(useUIStore.getState().notesSortBy).toBe('alphabetical');
  });

  it('clicking direction button toggles sort direction', () => {
    renderToolbar();
    const dirBtn = screen.getByTestId('explorer-sort-dir');
    expect(dirBtn).toHaveTextContent('↓');
    fireEvent.click(dirBtn);
    expect(useUIStore.getState().notesSortDirection).toBe('asc');
  });

  it('clicking create button calls onCreateNote prop', () => {
    renderToolbar();
    fireEvent.click(screen.getByTestId('explorer-create-btn'));
    expect(defaultProps.onCreateNote).toHaveBeenCalledTimes(1);
  });

  it('create button shows loading state when isCreating=true', () => {
    renderToolbar({ isCreating: true });
    const createBtn = screen.getByTestId('explorer-create-btn');
    expect(createBtn).toBeDisabled();
  });

  it('search input initializes from store query', () => {
    act(() => {
      useUIStore.setState({
        ...useUIStore.getState(),
        notesSearchQuery: 'existing query',
      });
    });
    renderToolbar();
    const searchInput = screen.getByTestId('explorer-search');
    expect(searchInput).toHaveValue('existing query');
  });

  it('search input clears when store query is externally reset', () => {
    act(() => {
      useUIStore.setState({
        ...useUIStore.getState(),
        notesSearchQuery: 'some search',
      });
    });
    const { rerender } = render(
      <ChakraProvider>
        <ExplorerToolbar {...defaultProps} />
      </ChakraProvider>
    );
    expect(screen.getByTestId('explorer-search')).toHaveValue('some search');

    act(() => {
      useUIStore.getState().actions.setNotesSearchQuery('');
    });
    rerender(
      <ChakraProvider>
        <ExplorerToolbar {...defaultProps} />
      </ChakraProvider>
    );
    expect(screen.getByTestId('explorer-search')).toHaveValue('');
  });

  it('"/" keypress focuses search input', () => {
    renderToolbar();
    const searchInput = screen.getByTestId('explorer-search');
    expect(document.activeElement).not.toBe(searchInput);

    fireEvent.keyDown(window, { key: '/' });
    expect(document.activeElement).toBe(searchInput);
  });

  it('Escape clears search when input is focused', () => {
    renderToolbar();
    const searchInput = screen.getByTestId('explorer-search');

    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.keyDown(searchInput, { key: 'Escape' });

    expect(useUIStore.getState().notesSearchQuery).toBe('');
  });

  it('sort button cycles through all 3 options', () => {
    renderToolbar();
    const sortBtn = screen.getByTestId('explorer-sort-btn');

    expect(sortBtn).toHaveTextContent('Modified');
    fireEvent.click(sortBtn);
    expect(sortBtn).toHaveTextContent('A-Z');
    fireEvent.click(sortBtn);
    expect(sortBtn).toHaveTextContent('Created');
    fireEvent.click(sortBtn);
    expect(sortBtn).toHaveTextContent('Modified');
  });

  it('direction button toggles between desc and asc', () => {
    renderToolbar();
    const dirBtn = screen.getByTestId('explorer-sort-dir');

    expect(dirBtn).toHaveTextContent('↓');
    fireEvent.click(dirBtn);
    expect(dirBtn).toHaveTextContent('↑');
    fireEvent.click(dirBtn);
    expect(dirBtn).toHaveTextContent('↓');
  });
});
