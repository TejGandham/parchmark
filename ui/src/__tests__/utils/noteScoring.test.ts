import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  computeForYouScore,
  getForYouNotes,
  getBlendedForYouNotes,
} from '../../utils/noteScoring';
import type { Note, SimilarNote } from '../../types';

const makeNote = (overrides: Partial<Note> = {}): Note => ({
  id: 'note-1',
  title: 'Test Note',
  content: '# Test',
  createdAt: '2024-01-01T00:00:00.000Z',
  updatedAt: '2024-01-15T12:00:00.000Z',
  ...overrides,
});

describe('noteScoring', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-01-15T12:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('computeForYouScore', () => {
    it('returns a score between 0 and 1 for a recently accessed note', () => {
      const note = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 5,
      });
      const score = computeForYouScore(note);
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(1);
    });

    it('weights recency at 60% and frequency at 40%', () => {
      const recentNoFrequency = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 0,
      });
      const oldHighFrequency = makeNote({
        lastAccessedAt: new Date(
          Date.now() - 7 * 24 * 60 * 60 * 1000
        ).toISOString(),
        accessCount: 20,
      });

      expect(computeForYouScore(recentNoFrequency)).toBeGreaterThan(
        computeForYouScore(oldHighFrequency)
      );
    });

    it('returns ~1.0 for just-accessed note with max frequency', () => {
      const note = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 100,
      });
      const score = computeForYouScore(note);
      // recency = 1/(1+0) = 1.0, frequency = min(100/20, 1) = 1.0
      // score = 0.6*1.0 + 0.4*1.0 = 1.0
      expect(score).toBeCloseTo(1.0, 1);
    });

    it('caps frequency score at 1.0 when accessCount >= 20', () => {
      const at20 = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 20,
      });
      const at100 = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 100,
      });
      expect(computeForYouScore(at20)).toBeCloseTo(
        computeForYouScore(at100),
        5
      );
    });

    it('falls back to updatedAt when lastAccessedAt is undefined', () => {
      const note = makeNote({
        updatedAt: new Date().toISOString(),
        accessCount: 0,
        lastAccessedAt: undefined,
      });
      const score = computeForYouScore(note);
      // recency based on updatedAt (just now) = 1/(1+0) ≈ 1.0
      // frequency = 0
      expect(score).toBeCloseTo(0.6, 1);
    });

    it('falls back to updatedAt when lastAccessedAt is missing (no property)', () => {
      const note = makeNote({ updatedAt: '2024-01-15T10:00:00.000Z' });
      delete (note as Partial<Note>).lastAccessedAt;
      const score = computeForYouScore(note);
      // 2 hours ago: recency = 1/(1+2) = 0.333
      // frequency = 0 (no accessCount)
      expect(score).toBeCloseTo(0.6 * (1 / 3), 2);
    });

    it('returns lower score for older notes', () => {
      const recentNote = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 5,
      });
      const oldNote = makeNote({
        lastAccessedAt: new Date(
          Date.now() - 30 * 24 * 60 * 60 * 1000
        ).toISOString(),
        accessCount: 5,
      });
      expect(computeForYouScore(recentNote)).toBeGreaterThan(
        computeForYouScore(oldNote)
      );
    });

    it('gives higher score to more frequently accessed notes (same recency)', () => {
      const lowFreq = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 2,
      });
      const highFreq = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 15,
      });
      expect(computeForYouScore(highFreq)).toBeGreaterThan(
        computeForYouScore(lowFreq)
      );
    });

    it('handles accessCount of 0', () => {
      const note = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: 0,
      });
      const score = computeForYouScore(note);
      // recency ≈ 1.0, frequency = 0
      expect(score).toBeCloseTo(0.6, 1);
    });

    it('handles undefined accessCount (nullish coalescing)', () => {
      const note = makeNote({
        lastAccessedAt: new Date().toISOString(),
        accessCount: undefined,
      });
      const score = computeForYouScore(note);
      expect(score).toBeCloseTo(0.6, 1);
    });

    it('computes correct score for known values', () => {
      // 24 hours ago, 10 accesses
      const note = makeNote({
        lastAccessedAt: new Date(
          Date.now() - 24 * 60 * 60 * 1000
        ).toISOString(),
        accessCount: 10,
      });
      const score = computeForYouScore(note);
      // recency = 1/(1+24) = 0.04, frequency = 10/20 = 0.5
      // score = 0.6*0.04 + 0.4*0.5 = 0.024 + 0.2 = 0.224
      expect(score).toBeCloseTo(0.224, 2);
    });
  });

  describe('getForYouNotes', () => {
    const notes: Note[] = [
      makeNote({
        id: '1',
        lastAccessedAt: '2024-01-15T12:00:00.000Z',
        accessCount: 10,
      }),
      makeNote({
        id: '2',
        lastAccessedAt: '2024-01-08T12:00:00.000Z',
        accessCount: 0,
      }),
      makeNote({
        id: '3',
        lastAccessedAt: '2024-01-15T11:00:00.000Z',
        accessCount: 5,
      }),
      makeNote({
        id: '4',
        lastAccessedAt: '2024-01-15T10:00:00.000Z',
        accessCount: 15,
      }),
    ];

    it('excludes the current note from results', () => {
      const result = getForYouNotes(notes, '1', 3);
      expect(result).not.toContainEqual(expect.objectContaining({ id: '1' }));
    });

    it('returns top N scored notes', () => {
      const result = getForYouNotes(notes, null, 2);
      expect(result).toHaveLength(2);
      expect(result[0].id).toBe('1');
    });

    it('defaults count to 3', () => {
      const result = getForYouNotes(notes, null);
      expect(result).toHaveLength(3);
    });

    it('returns fewer than count when not enough notes', () => {
      const twoNotes = [notes[0], notes[1]];
      const result = getForYouNotes(twoNotes, null, 5);
      expect(result).toHaveLength(2);
    });

    it('returns empty array when all notes are excluded', () => {
      const singleNote = [makeNote({ id: 'only' })];
      const result = getForYouNotes(singleNote, 'only', 3);
      expect(result).toEqual([]);
    });

    it('returns empty array for empty input', () => {
      const result = getForYouNotes([], null, 3);
      expect(result).toEqual([]);
    });

    it('handles null currentNoteId (no exclusion)', () => {
      const result = getForYouNotes(notes, null, 4);
      expect(result).toHaveLength(4);
    });

    it('sorts by descending score', () => {
      const result = getForYouNotes(notes, null, 4);
      for (let i = 1; i < result.length; i++) {
        expect(computeForYouScore(result[i - 1])).toBeGreaterThanOrEqual(
          computeForYouScore(result[i])
        );
      }
    });

    it('returns Note objects (not scored wrappers)', () => {
      const result = getForYouNotes(notes, null, 1);
      expect(result[0]).toHaveProperty('id');
      expect(result[0]).toHaveProperty('title');
      expect(result[0]).not.toHaveProperty('score');
    });
  });

  describe('getBlendedForYouNotes', () => {
    const notes: Note[] = [
      makeNote({
        id: '1',
        lastAccessedAt: '2024-01-15T12:00:00.000Z',
        accessCount: 10,
      }),
      makeNote({
        id: '2',
        lastAccessedAt: '2024-01-08T12:00:00.000Z',
        accessCount: 0,
      }),
      makeNote({
        id: '3',
        lastAccessedAt: '2024-01-15T11:00:00.000Z',
        accessCount: 5,
      }),
      makeNote({
        id: '4',
        lastAccessedAt: '2024-01-15T10:00:00.000Z',
        accessCount: 15,
      }),
    ];

    it('returns heuristic-only when similarNotes is empty array', () => {
      const blended = getBlendedForYouNotes(notes, null, [], 3);
      const heuristic = getForYouNotes(notes, null, 3);
      expect(blended.map((n) => n.id)).toEqual(heuristic.map((n) => n.id));
    });

    it('returns blended scores when similarNotes provided', () => {
      const similarNotes: SimilarNote[] = [
        { id: '2', title: 'Note 2', similarity: 0.95, updatedAt: '' },
      ];
      const result = getBlendedForYouNotes(notes, null, similarNotes, 4);
      expect(result).toHaveLength(4);
    });

    it('excludes current note from results', () => {
      const similarNotes: SimilarNote[] = [
        { id: '2', title: 'Note 2', similarity: 0.9, updatedAt: '' },
      ];
      const result = getBlendedForYouNotes(notes, '1', similarNotes, 3);
      expect(result).not.toContainEqual(expect.objectContaining({ id: '1' }));
    });

    it('similarity-heavy notes rank higher when similar', () => {
      const similarNotes: SimilarNote[] = [
        { id: '2', title: 'Note 2', similarity: 1.0, updatedAt: '' },
      ];
      const result = getBlendedForYouNotes(notes, null, similarNotes, 4);
      expect(result[0].id).toBe('2');
    });

    it('returns at most count notes', () => {
      const similarNotes: SimilarNote[] = [
        { id: '2', title: 'Note 2', similarity: 0.8, updatedAt: '' },
      ];
      const result = getBlendedForYouNotes(notes, null, similarNotes, 2);
      expect(result).toHaveLength(2);
    });

    it('handles notes not in similarity map (similarity = 0)', () => {
      const similarNotes: SimilarNote[] = [
        { id: '3', title: 'Note 3', similarity: 0.99, updatedAt: '' },
      ];
      const result = getBlendedForYouNotes(notes, null, similarNotes, 4);
      const note3Idx = result.findIndex((n) => n.id === '3');
      expect(note3Idx).toBe(0);
    });
  });
});
