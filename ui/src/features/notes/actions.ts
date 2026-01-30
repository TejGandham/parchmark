// ui/src/features/notes/actions.ts
import { redirect, ActionFunctionArgs } from 'react-router-dom';
import * as api from '../../services/api';
import {
  extractTitleFromMarkdown,
  createEmptyNoteContent,
} from '../../services/markdownService';

export async function createNoteAction() {
  try {
    const content = createEmptyNoteContent('Untitled');
    const title = extractTitleFromMarkdown(content);
    const newNote = await api.createNote({ title, content });
    return redirect(`/notes/${newNote.id}?editing=true`);
  } catch (error) {
    throw new Response(
      error instanceof Error ? error.message : 'Failed to create note',
      { status: 500 }
    );
  }
}

export async function updateNoteAction({
  request,
  params,
}: ActionFunctionArgs) {
  const noteId = params.noteId;
  if (!noteId) {
    throw new Response('Note ID required', { status: 400 });
  }

  try {
    const formData = await request.formData();
    const content = formData.get('content') as string;

    await api.updateNote(noteId, { content });
    return { ok: true };
  } catch (error) {
    throw new Response(
      error instanceof Error ? error.message : 'Failed to update note',
      { status: 500 }
    );
  }
}

export async function deleteNoteAction({ params }: ActionFunctionArgs) {
  const noteId = params.noteId;
  if (!noteId) {
    throw new Response('Note ID required', { status: 400 });
  }

  try {
    await api.deleteNote(noteId);
    return redirect('/notes');
  } catch (error) {
    throw new Response(
      error instanceof Error ? error.message : 'Failed to delete note',
      { status: 500 }
    );
  }
}
