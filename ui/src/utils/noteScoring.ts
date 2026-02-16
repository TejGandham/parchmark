import type { Note, SimilarNote } from '../types';

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

/**
 * Blend heuristic scores with AI similarity scores.
 * When similarity data is available:
 *   finalScore = 0.4 * heuristic + 0.6 * similarity
 * When no similarity data:
 *   Falls back to heuristic-only scoring.
 */
export const getBlendedForYouNotes = (
  notes: Note[],
  currentNoteId: string | null,
  similarNotes: SimilarNote[],
  count: number = 3
): Note[] => {
  const candidates = notes.filter((note) => note.id !== currentNoteId);

  if (similarNotes.length === 0) {
    return getForYouNotes(notes, currentNoteId, count);
  }

  const similarityMap = new Map<string, number>();
  for (const sn of similarNotes) {
    similarityMap.set(sn.id, sn.similarity);
  }

  const scored = candidates.map((note) => {
    const heuristic = computeForYouScore(note);
    const similarity = similarityMap.get(note.id) ?? 0;
    const blended = 0.4 * heuristic + 0.6 * similarity;
    return { note, score: blended };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, count).map((item) => item.note);
};
