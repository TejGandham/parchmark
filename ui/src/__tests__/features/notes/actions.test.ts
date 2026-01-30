// ui/src/__tests__/features/notes/actions.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { redirect } from 'react-router-dom';

// Mock the API
vi.mock('../../../services/api', () => ({
  createNote: vi.fn(),
  updateNote: vi.fn(),
  deleteNote: vi.fn(),
}));

// Mock react-router-dom redirect
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    redirect: vi.fn((path) => ({ type: 'redirect', path })),
  };
});

describe('notes actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createNoteAction', () => {
    it('creates note and redirects with editing flag', async () => {
      const { createNote } = await import('../../../services/api');
      const { createNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (createNote as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'new-note-123',
        title: 'Untitled',
        content: '# Untitled\n\n',
      });

      await createNoteAction();

      expect(createNote).toHaveBeenCalledWith({
        title: 'Untitled',
        content: '# Untitled\n\n',
      });
      expect(redirect).toHaveBeenCalledWith('/notes/new-note-123?editing=true');
    });
  });

  describe('updateNoteAction', () => {
    it('updates note and returns success', async () => {
      const { updateNote } = await import('../../../services/api');
      const { updateNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (updateNote as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'note-123',
        title: 'Updated Title',
        content: '# Updated Title\n\nContent here',
      });

      const formData = new FormData();
      formData.append('content', '# Updated Title\n\nContent here');

      const request = new Request('http://localhost/notes/note-123', {
        method: 'POST',
        body: formData,
      });

      const result = await updateNoteAction({
        request,
        params: { noteId: 'note-123' },
      });

      // FormData encodes newlines as CRLF (\r\n) per HTTP standards
      expect(updateNote).toHaveBeenCalledWith('note-123', {
        content: '# Updated Title\r\n\r\nContent here',
      });
      expect(result).toEqual({ ok: true });
    });

    it('throws 400 error when noteId is missing', async () => {
      const { updateNoteAction } = await import(
        '../../../features/notes/actions'
      );

      const formData = new FormData();
      formData.append('content', '# Test');

      const request = new Request('http://localhost/notes', {
        method: 'POST',
        body: formData,
      });

      await expect(
        updateNoteAction({ request, params: {} })
      ).rejects.toBeInstanceOf(Response);

      try {
        await updateNoteAction({ request, params: {} });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(400);
      }
    });
  });

  describe('deleteNoteAction', () => {
    it('deletes note and redirects to /notes', async () => {
      const { deleteNote } = await import('../../../services/api');
      const { deleteNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (deleteNote as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

      await deleteNoteAction({ params: { noteId: 'note-123' } });

      expect(deleteNote).toHaveBeenCalledWith('note-123');
      expect(redirect).toHaveBeenCalledWith('/notes');
    });

    it('throws 400 error when noteId is missing', async () => {
      const { deleteNoteAction } = await import(
        '../../../features/notes/actions'
      );

      await expect(deleteNoteAction({ params: {} })).rejects.toBeInstanceOf(
        Response
      );

      try {
        await deleteNoteAction({ params: {} });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(400);
      }
    });
  });
});
