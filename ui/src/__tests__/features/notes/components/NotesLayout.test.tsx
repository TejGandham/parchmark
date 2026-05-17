// ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import * as routerDom from 'react-router-dom';
import type {
  NoteEventCallback,
  NoteEventStreamOptions,
} from '../../../../services/notesEventStream';

const notesEventStreamMock = vi.hoisted(() => ({
  subscribe: vi.fn(),
  dispose: vi.fn(),
  lastCallback: undefined as NoteEventCallback | undefined,
  lastOptions: undefined as NoteEventStreamOptions | undefined,
}));

// Mock react-router-dom hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLoaderData: vi.fn(),
    useParams: vi.fn(),
    useRevalidator: vi.fn(),
  };
});

vi.mock('../../../../services/notesEventStream', () => ({
  subscribe: notesEventStreamMock.subscribe,
}));

// Mock Header component
vi.mock('../../../../features/ui/components/Header', () => ({
  default: () => (
    <header data-testid="header">
      <span>Notes</span>
    </header>
  ),
}));

vi.mock('../../../../features/ui/components/CommandPalette', () => ({
  CommandPalette: () => <div data-testid="command-palette" />,
}));

const mockNotes = [
  {
    id: 'note-1',
    title: 'First Note',
    content: '# First Note\n\nContent',
    createdAt: '2026-01-29T10:00:00Z',
    updatedAt: '2026-01-29T10:00:00Z',
  },
  {
    id: 'note-2',
    title: 'Second Note',
    content: '# Second Note\n\nMore content',
    createdAt: '2026-01-29T09:00:00Z',
    updatedAt: '2026-01-29T09:00:00Z',
  },
];

describe('NotesLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    notesEventStreamMock.lastCallback = undefined;
    notesEventStreamMock.lastOptions = undefined;
    notesEventStreamMock.subscribe.mockImplementation(
      (callback: NoteEventCallback, options: NoteEventStreamOptions = {}) => {
        notesEventStreamMock.lastCallback = callback;
        notesEventStreamMock.lastOptions = options;
        return notesEventStreamMock.dispose;
      }
    );
    vi.mocked(routerDom.useLoaderData).mockReturnValue({ notes: mockNotes });
    vi.mocked(routerDom.useParams).mockReturnValue({});
    vi.mocked(routerDom.useRevalidator).mockReturnValue({
      revalidate: vi.fn(),
      state: 'idle',
    });
  });

  async function renderComponent(noteId?: string) {
    vi.mocked(routerDom.useParams).mockReturnValue(noteId ? { noteId } : {});

    const { default: NotesLayout } = await import(
      '../../../../features/notes/components/NotesLayout'
    );

    return render(
      <ChakraProvider>
        <MemoryRouter>
          <NotesLayout />
        </MemoryRouter>
      </ChakraProvider>
    );
  }

  it('renders header', async () => {
    await renderComponent();
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('mounts command palette', async () => {
    await renderComponent();
    expect(screen.getByTestId('command-palette')).toBeInTheDocument();
  });

  it('renders Outlet for child routes', async () => {
    await renderComponent('note-1');
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('renders full-width layout without sidebar', async () => {
    await renderComponent();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
  });

  it('revalidates the notes loader once per received note event', async () => {
    const revalidate = vi.fn();
    vi.mocked(routerDom.useRevalidator).mockReturnValue({
      revalidate,
      state: 'idle',
    });

    await renderComponent();

    expect(notesEventStreamMock.subscribe).toHaveBeenCalledTimes(1);
    notesEventStreamMock.lastCallback?.({
      kind: 'created',
      note_id: 'note-3',
    });
    notesEventStreamMock.lastCallback?.({
      kind: 'updated',
      note_id: 'note-1',
    });
    notesEventStreamMock.lastCallback?.({
      kind: 'deleted',
      note_id: 'note-2',
    });

    expect(revalidate).toHaveBeenCalledTimes(3);
  });

  it('revalidates immediately when the notes event stream opens', async () => {
    const revalidate = vi.fn();
    vi.mocked(routerDom.useRevalidator).mockReturnValue({
      revalidate,
      state: 'idle',
    });

    await renderComponent();

    notesEventStreamMock.lastOptions?.onOpen?.();

    expect(revalidate).toHaveBeenCalledTimes(1);
  });

  it('revalidates again when the notes event stream reconnects', async () => {
    const revalidate = vi.fn();
    vi.mocked(routerDom.useRevalidator).mockReturnValue({
      revalidate,
      state: 'idle',
    });

    await renderComponent();

    notesEventStreamMock.lastOptions?.onOpen?.();
    notesEventStreamMock.lastOptions?.onOpen?.();

    expect(revalidate).toHaveBeenCalledTimes(2);
  });

  it('disposes the notes event stream subscription on unmount', async () => {
    const { unmount } = await renderComponent();

    unmount();

    expect(notesEventStreamMock.dispose).toHaveBeenCalledTimes(1);
  });
});
