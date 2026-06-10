import { Note } from '../../../types';
import { removeH1FromContent } from '../../../services/markdownService';

/**
 * Slugifies a note title into a filesystem-safe filename stem.
 * Lowercases, replaces runs of non-alphanumeric characters with single
 * hyphens, and trims leading/trailing hyphens.
 * 'Meeting Notes 6/10' -> 'meeting-notes-6-10'
 */
export const slugifyNoteTitle = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

/**
 * Filename for a downloaded note: slugified title + '.md', falling back
 * to 'note-<id>.md' when the title slugifies to empty.
 */
export const noteDownloadFilename = (
  note: Pick<Note, 'id' | 'title'>
): string => {
  const slug = slugifyNoteTitle(note.title);
  return `${slug || `note-${note.id}`}.md`;
};

/**
 * Downloads a note as a markdown file, generated entirely in the browser
 * from already-loaded note data — no backend route, no fetch. The body is
 * the title-stripped markdown the read view renders (removeH1FromContent);
 * the title is carried only in the filename.
 */
export const downloadNoteAsMarkdown = (note: Note): void => {
  const body = removeH1FromContent(note.content);
  const blob = new Blob([body], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = noteDownloadFilename(note);
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
};
