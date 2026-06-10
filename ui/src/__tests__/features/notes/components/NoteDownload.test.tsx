// Oracle coverage for WI01 — read-view note download button (markdown export).
// Renders the composed read view (real NoteActions inside NoteContent, real
// markdownService) and asserts on the browser download mechanism
// (object URL + anchor click).
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import * as routerDom from 'react-router-dom';
import * as storeModule from '../../../../store';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteContent from '../../../../features/notes/components/NoteContent';
import { removeH1FromContent } from '../../../../services/markdownService';

// Mock router module — the note arrives via loader data (read view setup)
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
    useRouteLoaderData: vi.fn(),
    useSearchParams: vi.fn(),
    useNavigate: vi.fn(),
    useFetcher: vi.fn(),
  };
});

// Mock store
vi.mock('../../../../store', () => ({
  useNotesUIStore: vi.fn(),
}));

// NoteActions is intentionally NOT mocked — the composed toolbar is under test.
// markdownService is intentionally NOT mocked — the file body contract is
// removeH1FromContent itself.

vi.mock('../../../../features/notes/components/NoteMetadata', () => ({
  default: () => <div data-testid="note-metadata" />,
}));

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => (
    <div data-testid="markdown-preview">{children}</div>
  ),
}));

vi.mock('remark-gfm', () => ({ default: () => {} }));
vi.mock('rehype-raw', () => ({ default: () => {} }));
vi.mock('../../../../components/Mermaid', () => ({
  default: () => <div data-testid="mermaid" />,
}));

const meetingNote = {
  id: 'note-1',
  title: 'Meeting Notes 6/10',
  content: '# Meeting Notes 6/10\n\nAgenda item one.\n\n- Decision recorded.',
  createdAt: '2026-06-10T10:00:00Z',
  updatedAt: '2026-06-10T11:00:00Z',
};

const whitespaceTitleNote = {
  id: 'note-3',
  title: '   ',
  content: '#    \n\nBody of an untitled note.',
  createdAt: '2026-06-09T10:00:00Z',
  updatedAt: '2026-06-09T10:00:00Z',
};

const mockNotes = [meetingNote, whitespaceTitleNote];

describe('NoteDownload (read-view markdown export)', () => {
  const mockSetSearchParams = vi.fn();
  const mockFetcherSubmit = vi.fn();
  const mockSetEditedContent = vi.fn();
  const fetchMock = vi.fn();

  // Captured at click time from the anchor the download handler clicks
  const clickedAnchors: Array<{ download: string; href: string }> = [];
  const createObjectURLMock = vi.fn<(obj: Blob | MediaSource) => string>(
    () => 'blob:mock-note-url'
  );
  const revokeObjectURLMock = vi.fn();

  function setupMocks(options: { noteId?: string; isEditing?: boolean } = {}) {
    const { noteId = 'note-1', isEditing = false } = options;

    vi.mocked(routerDom.useParams).mockReturnValue({ noteId });
    vi.mocked(routerDom.useRouteLoaderData).mockReturnValue({
      notes: mockNotes,
    });
    vi.mocked(routerDom.useSearchParams).mockReturnValue([
      new URLSearchParams(isEditing ? 'editing=true' : ''),
      mockSetSearchParams,
    ] as unknown as ReturnType<typeof routerDom.useSearchParams>);
    vi.mocked(routerDom.useNavigate).mockReturnValue(vi.fn());
    vi.mocked(routerDom.useFetcher).mockReturnValue({
      submit: mockFetcherSubmit,
      state: 'idle',
      data: null,
    } as unknown as ReturnType<typeof routerDom.useFetcher>);

    vi.mocked(storeModule.useNotesUIStore).mockImplementation((selector) => {
      const state = {
        editedContent: isEditing ? meetingNote.content : null,
        setEditedContent: mockSetEditedContent,
      };
      return selector ? selector(state) : state;
    });
  }

  beforeEach(() => {
    vi.clearAllMocks();
    clickedAnchors.length = 0;

    // happy-dom may not implement the object-URL API — define it explicitly
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: createObjectURLMock,
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      writable: true,
      value: revokeObjectURLMock,
    });

    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement
    ) {
      clickedAnchors.push({ download: this.download, href: this.href });
    });

    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    cleanup();
  });

  function renderComponent() {
    return render(
      <TestProvider>
        <NoteContent />
      </TestProvider>
    );
  }

  function clickDownload() {
    fireEvent.click(screen.getByRole('button', { name: 'Download note' }));
  }

  // Oracle /work_items/0/oracle/assertions/0
  it('renders a download icon button in the read-view toolbar alongside Edit and Delete', () => {
    setupMocks();
    renderComponent();

    const downloadButton = screen.getByRole('button', {
      name: 'Download note',
    });
    expect(downloadButton).toBeInTheDocument();
    expect(downloadButton.querySelector('svg')).toBeTruthy();

    // Alongside Edit and Delete in the same action toolbar
    expect(
      screen.getByRole('button', { name: 'Edit note' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Delete note' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Delete note' }).parentElement
    ).toBe(downloadButton.parentElement);
  });

  it('does not render the download button in edit mode', () => {
    setupMocks({ isEditing: true });
    renderComponent();

    expect(
      screen.queryByRole('button', { name: 'Download note' })
    ).not.toBeInTheDocument();
  });

  // Oracle /work_items/0/oracle/assertions/1
  it('downloads the note as slugified-title.md via an object-URL anchor click', () => {
    setupMocks({ noteId: 'note-1' });
    renderComponent();
    clickDownload();

    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(clickedAnchors).toHaveLength(1);
    expect(clickedAnchors.at(0)?.download).toBe('meeting-notes-6-10.md');
    expect(clickedAnchors.at(0)?.href).toContain('blob:mock-note-url');
    expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:mock-note-url');
  });

  // Oracle /work_items/0/oracle/assertions/2
  it('writes the title-stripped markdown (removeH1FromContent) as the file body', async () => {
    setupMocks({ noteId: 'note-1' });
    renderComponent();
    clickDownload();

    const blob = createObjectURLMock.mock.calls[0][0] as unknown as Blob;
    const body = await blob.text();

    expect(body).toBe(removeH1FromContent(meetingNote.content));
    expect(body).not.toContain('# Meeting Notes 6/10');
    expect(body).toContain('Agenda item one.');
  });

  // Oracle /work_items/0/oracle/assertions/3
  it('performs no network request when downloading', () => {
    setupMocks({ noteId: 'note-1' });
    renderComponent();
    clickDownload();

    expect(fetchMock).not.toHaveBeenCalled();
    expect(mockFetcherSubmit).not.toHaveBeenCalled();
  });

  // Oracle /work_items/0/oracle/assertions/4
  it('falls back to note-<id>.md when the title slugifies to empty', () => {
    setupMocks({ noteId: 'note-3' });
    renderComponent();
    clickDownload();

    expect(clickedAnchors).toHaveLength(1);
    expect(clickedAnchors.at(0)?.download).toBe('note-note-3.md');
  });
});
