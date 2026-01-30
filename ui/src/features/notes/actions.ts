// ui/src/features/notes/actions.ts
import { redirect, ActionFunctionArgs } from 'react-router-dom';
import * as api from '../../services/api';
import {
  extractTitleFromMarkdown,
  createEmptyNoteContent,
} from '../../services/markdownService';

export async function createNoteAction() {
  const content = createEmptyNoteContent('Untitled');
  const title = extractTitleFromMarkdown(content);
  const newNote = await api.createNote({ title, content });
  return redirect(`/notes/${newNote.id}?editing=true`);
}

export async function updateNoteAction({
  request,
  params,
}: ActionFunctionArgs) {
  if (!params.noteId) {
    throw new Response('Note ID required', { status: 400 });
  }
  const formData = await request.formData();
  const content = formData.get('content') as string;

  await api.updateNote(params.noteId, { content });
  return { ok: true };
}

export async function deleteNoteAction({ params }: ActionFunctionArgs) {
  if (!params.noteId) {
    throw new Response('Note ID required', { status: 400 });
  }
  await api.deleteNote(params.noteId);
  return redirect('/notes');
}
