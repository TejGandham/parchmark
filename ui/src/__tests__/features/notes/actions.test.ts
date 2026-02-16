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
    const makeCreateRequest = () =>
      new Request('http://localhost/notes', {
        method: 'POST',
        body: new FormData(),
      });

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

      await createNoteAction({ request: makeCreateRequest(), params: {} });

      expect(createNote).toHaveBeenCalledWith({
        title: 'Untitled',
        content: '# Untitled\n\n',
      });
      expect(redirect).toHaveBeenCalledWith('/notes/new-note-123?editing=true');
    });

    it('returns data instead of redirect when custom title provided', async () => {
      const { createNote } = await import('../../../services/api');
      const { createNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (createNote as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'new-note-456',
        title: 'My Topic',
        content: '# My Topic\n\n',
      });

      const formData = new FormData();
      formData.append('title', 'My Topic');
      formData.append('content', '# My Topic\n\n');
      const request = new Request('http://localhost/notes', {
        method: 'POST',
        body: formData,
      });

      const result = await createNoteAction({ request, params: {} });
      expect(result).toEqual({ id: 'new-note-456', title: 'My Topic' });
      expect(redirect).not.toHaveBeenCalled();
    });

    it('throws 500 error when API fails with Error', async () => {
      const { createNote } = await import('../../../services/api');
      const { createNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (createNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      try {
        await createNoteAction({ request: makeCreateRequest(), params: {} });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Network error');
      }
    });

    it('throws 500 error with default message for non-Error', async () => {
      const { createNote } = await import('../../../services/api');
      const { createNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (createNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        'string error'
      );

      try {
        await createNoteAction({ request: makeCreateRequest(), params: {} });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Failed to create note');
      }
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

    it('throws 500 error when API fails with Error', async () => {
      const { updateNote } = await import('../../../services/api');
      const { updateNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (updateNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      const formData = new FormData();
      formData.append('content', '# Test');

      const request = new Request('http://localhost/notes/note-123', {
        method: 'POST',
        body: formData,
      });

      try {
        await updateNoteAction({ request, params: { noteId: 'note-123' } });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Network error');
      }
    });

    it('throws 500 error with default message for non-Error', async () => {
      const { updateNote } = await import('../../../services/api');
      const { updateNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (updateNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        'string error'
      );

      const formData = new FormData();
      formData.append('content', '# Test');

      const request = new Request('http://localhost/notes/note-123', {
        method: 'POST',
        body: formData,
      });

      try {
        await updateNoteAction({ request, params: { noteId: 'note-123' } });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Failed to update note');
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

    it('throws 500 error when API fails with Error', async () => {
      const { deleteNote } = await import('../../../services/api');
      const { deleteNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (deleteNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      try {
        await deleteNoteAction({ params: { noteId: 'note-123' } });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Network error');
      }
    });

    it('throws 500 error with default message for non-Error', async () => {
      const { deleteNote } = await import('../../../services/api');
      const { deleteNoteAction } = await import(
        '../../../features/notes/actions'
      );

      (deleteNote as ReturnType<typeof vi.fn>).mockRejectedValue(
        'string error'
      );

      try {
        await deleteNoteAction({ params: { noteId: 'note-123' } });
      } catch (error) {
        expect(error).toBeInstanceOf(Response);
        expect((error as Response).status).toBe(500);
        const text = await (error as Response).text();
        expect(text).toBe('Failed to delete note');
      }
    });
  });
});
