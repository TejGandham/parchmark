import type { Note } from '../types';

// Score = (0.6 * recency) + (0.4 * frequency)
// recency = 1/(1+hours)  frequency = min(count/20, 1.0)
// Falls back to updatedAt when no access data exists.
export const computeForYouScore = (note: Note): number => {
  const now = new Date();

  const lastAccessDate = note.lastAccessedAt
    ? new Date(note.lastAccessedAt)
    : new Date(note.updatedAt);

  const hoursSince =
    (now.getTime() - lastAccessDate.getTime()) / (1000 * 60 * 60);
  const recencyScore = 1 / (1 + hoursSince);

  const accessCount = note.accessCount ?? 0;
  const frequencyScore = Math.min(accessCount / 20, 1.0);

  return 0.6 * recencyScore + 0.4 * frequencyScore;
};

export const getForYouNotes = (
  notes: Note[],
  currentNoteId: string | null,
  count: number = 3
): Note[] => {
  const candidates = notes.filter((note) => note.id !== currentNoteId);

  const scored = candidates.map((note) => ({
    note,
    score: computeForYouScore(note),
  }));

  scored.sort((a, b) => b.score - a.score);

  return scored.slice(0, count).map((item) => item.note);
};
