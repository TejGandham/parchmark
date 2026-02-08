import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getDateGroup,
  groupNotesByDate,
  sortNotes,
  filterNotes,
  SortOption,
} from '../../utils/dateGrouping';
import { Note } from '../../types';

describe('dateGrouping utilities', () => {
  let mockDate: Date;

  beforeEach(() => {
    // Set a fixed date for consistent testing: 2024-01-15 12:00:00
    mockDate = new Date('2024-01-15T12:00:00.000Z');
    vi.setSystemTime(mockDate);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('getDateGroup', () => {
    it('should return "Today" for current date', () => {
      const today = new Date('2024-01-15T12:00:00.000Z');
      expect(getDateGroup(today)).toBe('Today');
    });

    it('should return "Today" for afternoon of current day', () => {
      const today = new Date('2024-01-15T18:00:00.000Z');
      expect(getDateGroup(today)).toBe('Today');
    });

    it('should return "Yesterday" for previous day', () => {
      const yesterday = new Date('2024-01-14T12:00:00.000Z');
      expect(getDateGroup(yesterday)).toBe('Yesterday');
    });

    it('should return "This Week" for 3 days ago', () => {
      const threeDaysAgo = new Date('2024-01-12T14:30:00.000Z');
      expect(getDateGroup(threeDaysAgo)).toBe('This Week');
    });

    it('should return "This Week" for 6 days ago', () => {
      const sixDaysAgo = new Date('2024-01-09T14:30:00.000Z');
      expect(getDateGroup(sixDaysAgo)).toBe('This Week');
    });

    it('should return "This Month" for 10 days ago', () => {
      const tenDaysAgo = new Date('2024-01-05T14:30:00.000Z');
      expect(getDateGroup(tenDaysAgo)).toBe('This Month');
    });

    it('should return "This Month" for 20 days ago', () => {
      const twentyDaysAgo = new Date('2023-12-26T14:30:00.000Z');
      expect(getDateGroup(twentyDaysAgo)).toBe('This Month');
    });

    it('should return "Older" for 2 months ago', () => {
      const twoMonthsAgo = new Date('2023-11-15T14:30:00.000Z');
      expect(getDateGroup(twoMonthsAgo)).toBe('Older');
    });

    it('should return "Older" for 1 year ago', () => {
      const oneYearAgo = new Date('2023-01-15T14:30:00.000Z');
      expect(getDateGroup(oneYearAgo)).toBe('Older');
    });
  });

  describe('groupNotesByDate', () => {
    const createNote = (
      id: string,
      title: string,
      updated_at: string
    ): Note => ({
      id,
      title,
      content: `# ${title}\n\nContent`,
      created_at: updated_at,
      updated_at,
    });

    it('should group notes by date categories', () => {
      const notes: Note[] = [
        createNote('1', 'Today Note', '2024-01-15T10:00:00.000Z'),
        createNote('2', 'Yesterday Note', '2024-01-14T10:00:00.000Z'),
        createNote('3', 'This Week Note', '2024-01-10T10:00:00.000Z'),
        createNote('4', 'This Month Note', '2024-01-05T10:00:00.000Z'),
        createNote('5', 'Older Note', '2023-11-15T10:00:00.000Z'),
      ];

      const grouped = groupNotesByDate(notes);

      expect(grouped).toHaveLength(5);
      expect(grouped[0].group).toBe('Today');
      expect(grouped[0].count).toBe(1);
      expect(grouped[0].notes[0].title).toBe('Today Note');

      expect(grouped[1].group).toBe('Yesterday');
      expect(grouped[1].count).toBe(1);
      expect(grouped[1].notes[0].title).toBe('Yesterday Note');

      expect(grouped[2].group).toBe('This Week');
      expect(grouped[2].count).toBe(1);
      expect(grouped[2].notes[0].title).toBe('This Week Note');

      expect(grouped[3].group).toBe('This Month');
      expect(grouped[3].count).toBe(1);
      expect(grouped[3].notes[0].title).toBe('This Month Note');

      expect(grouped[4].group).toBe('Older');
      expect(grouped[4].count).toBe(1);
      expect(grouped[4].notes[0].title).toBe('Older Note');
    });

    it('should filter out empty groups', () => {
      const notes: Note[] = [
        createNote('1', 'Today Note', '2024-01-15T10:00:00.000Z'),
        createNote('2', 'Older Note', '2023-11-15T10:00:00.000Z'),
      ];

      const grouped = groupNotesByDate(notes);

      expect(grouped).toHaveLength(2);
      expect(grouped.map((g) => g.group)).toEqual(['Today', 'Older']);
    });

    it('should handle multiple notes in the same group', () => {
      const notes: Note[] = [
        createNote('1', 'Today Note 1', '2024-01-15T10:00:00.000Z'),
        createNote('2', 'Today Note 2', '2024-01-15T14:00:00.000Z'),
        createNote('3', 'Today Note 3', '2024-01-15T18:00:00.000Z'),
      ];

      const grouped = groupNotesByDate(notes);

      expect(grouped).toHaveLength(1);
      expect(grouped[0].group).toBe('Today');
      expect(grouped[0].count).toBe(3);
      expect(grouped[0].notes).toHaveLength(3);
    });

    it('should handle empty notes array', () => {
      const grouped = groupNotesByDate([]);
      expect(grouped).toEqual([]);
    });

    it('should maintain note order within groups', () => {
      const notes: Note[] = [
        createNote('1', 'Note A', '2024-01-15T10:00:00.000Z'),
        createNote('2', 'Note B', '2024-01-15T14:00:00.000Z'),
        createNote('3', 'Note C', '2024-01-15T18:00:00.000Z'),
      ];

      const grouped = groupNotesByDate(notes);

      expect(grouped[0].notes.map((n) => n.title)).toEqual([
        'Note A',
        'Note B',
        'Note C',
      ]);
    });
  });

  describe('sortNotes', () => {
    const createNote = (
      id: string,
      title: string,
      created_at: string,
      updated_at: string
    ): Note => ({
      id,
      title,
      content: `# ${title}\n\nContent`,
      created_at,
      updated_at,
    });

    describe('lastModified sorting', () => {
      it('should sort by updated_at descending (newest first)', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Old',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'New',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Medium',
            '2024-01-01T10:00:00.000Z',
            '2024-01-10T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'lastModified');

        expect(sorted.map((n) => n.title)).toEqual(['New', 'Medium', 'Old']);
      });

      it('should handle same updated_at timestamps', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'A',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
          createNote(
            '2',
            'B',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'lastModified');

        // Order should be stable
        expect(sorted).toHaveLength(2);
      });
    });

    describe('alphabetical sorting', () => {
      it('should sort by title descending (Z-A) by default', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Zebra',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'Apple',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Mango',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'alphabetical');

        expect(sorted.map((n) => n.title)).toEqual(['Zebra', 'Mango', 'Apple']);
      });

      it('should handle case-insensitive sorting descending', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'zebra',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'Apple',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'MANGO',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'alphabetical');

        expect(sorted.map((n) => n.title)).toEqual(['zebra', 'MANGO', 'Apple']);
      });

      it('should handle special characters and numbers', () => {
        const notes: Note[] = [
          createNote(
            '1',
            '2024 Goals',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            '!Important',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Zebra',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'alphabetical');

        // Natural ordering based on locale
        expect(sorted).toHaveLength(3);
      });
    });

    describe('createdDate sorting', () => {
      it('should sort by created_at descending (newest first)', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Old',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
          createNote(
            '2',
            'New',
            '2024-01-15T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Medium',
            '2024-01-10T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'createdDate');

        expect(sorted.map((n) => n.title)).toEqual(['New', 'Medium', 'Old']);
      });

      it('should handle same created_at timestamps', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'A',
            '2024-01-15T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'B',
            '2024-01-15T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'createdDate');

        // Order should be stable
        expect(sorted).toHaveLength(2);
      });
    });

    describe('ascending direction', () => {
      it('should sort lastModified ascending (oldest first)', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Old',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'New',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Medium',
            '2024-01-01T10:00:00.000Z',
            '2024-01-10T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'lastModified', 'asc');

        expect(sorted.map((n) => n.title)).toEqual(['Old', 'Medium', 'New']);
      });

      it('should sort alphabetical descending (Z-A)', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Zebra',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'Apple',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Mango',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'alphabetical', 'desc');

        expect(sorted.map((n) => n.title)).toEqual(['Zebra', 'Mango', 'Apple']);
      });

      it('should sort alphabetical ascending (A-Z) explicitly', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Zebra',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'Apple',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Mango',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'alphabetical', 'asc');

        expect(sorted.map((n) => n.title)).toEqual(['Apple', 'Mango', 'Zebra']);
      });

      it('should sort createdDate ascending (oldest first)', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Old',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
          createNote(
            '2',
            'New',
            '2024-01-15T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '3',
            'Medium',
            '2024-01-10T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
        ];

        const sorted = sortNotes(notes, 'createdDate', 'asc');

        expect(sorted.map((n) => n.title)).toEqual(['Old', 'Medium', 'New']);
      });

      it('should default to descending when direction is omitted', () => {
        const notes: Note[] = [
          createNote(
            '1',
            'Old',
            '2024-01-01T10:00:00.000Z',
            '2024-01-01T10:00:00.000Z'
          ),
          createNote(
            '2',
            'New',
            '2024-01-01T10:00:00.000Z',
            '2024-01-15T10:00:00.000Z'
          ),
        ];

        const withDefault = sortNotes(notes, 'lastModified');
        const withExplicit = sortNotes(notes, 'lastModified', 'desc');

        expect(withDefault.map((n) => n.title)).toEqual(
          withExplicit.map((n) => n.title)
        );
      });
    });

    it('should not mutate original array', () => {
      const notes: Note[] = [
        createNote(
          '1',
          'C',
          '2024-01-01T10:00:00.000Z',
          '2024-01-01T10:00:00.000Z'
        ),
        createNote(
          '2',
          'A',
          '2024-01-01T10:00:00.000Z',
          '2024-01-01T10:00:00.000Z'
        ),
        createNote(
          '3',
          'B',
          '2024-01-01T10:00:00.000Z',
          '2024-01-01T10:00:00.000Z'
        ),
      ];

      const original = [...notes];
      sortNotes(notes, 'alphabetical');

      expect(notes).toEqual(original);
    });

    it('should handle empty array', () => {
      const sorted = sortNotes([], 'lastModified');
      expect(sorted).toEqual([]);
    });

    it('should return unsorted array for invalid sort option', () => {
      const notes: Note[] = [
        createNote(
          '1',
          'C',
          '2024-01-01T10:00:00.000Z',
          '2024-01-01T10:00:00.000Z'
        ),
        createNote(
          '2',
          'A',
          '2024-01-01T10:00:00.000Z',
          '2024-01-01T10:00:00.000Z'
        ),
      ];

      // TypeScript allows any string, so we test the default case
      const sorted = sortNotes(notes, 'invalid' as SortOption);

      // Should return a copy of the array without sorting
      expect(sorted).toEqual(notes);
      expect(sorted).not.toBe(notes); // Should be a new array
    });
  });

  describe('filterNotes', () => {
    const createNote = (id: string, title: string, content: string): Note => ({
      id,
      title,
      content,
      created_at: '2024-01-01T10:00:00.000Z',
      updated_at: '2024-01-01T10:00:00.000Z',
    });

    it('should return all notes when search query is empty', () => {
      const notes: Note[] = [
        createNote('1', 'Note 1', '# Note 1\n\nContent'),
        createNote('2', 'Note 2', '# Note 2\n\nContent'),
      ];

      const filtered = filterNotes(notes, '');
      expect(filtered).toEqual(notes);
    });

    it('should return all notes when search query is only whitespace', () => {
      const notes: Note[] = [
        createNote('1', 'Note 1', '# Note 1\n\nContent'),
        createNote('2', 'Note 2', '# Note 2\n\nContent'),
      ];

      const filtered = filterNotes(notes, '   ');
      expect(filtered).toEqual(notes);
    });

    it('should filter by title (case insensitive)', () => {
      const notes: Note[] = [
        createNote('1', 'Shopping List', '# Shopping List\n\nBuy milk'),
        createNote('2', 'Meeting Notes', '# Meeting Notes\n\nDiscuss project'),
        createNote('3', 'Shopping Ideas', '# Shopping Ideas\n\nGift ideas'),
      ];

      const filtered = filterNotes(notes, 'shopping');

      expect(filtered).toHaveLength(2);
      expect(filtered.map((n) => n.title)).toEqual([
        'Shopping List',
        'Shopping Ideas',
      ]);
    });

    it('should filter by content (case insensitive)', () => {
      const notes: Note[] = [
        createNote('1', 'Note 1', '# Note 1\n\nBuy milk and eggs'),
        createNote('2', 'Note 2', '# Note 2\n\nCall the plumber'),
        createNote('3', 'Note 3', '# Note 3\n\nBuy bread and butter'),
      ];

      const filtered = filterNotes(notes, 'buy');

      expect(filtered).toHaveLength(2);
      expect(filtered.map((n) => n.title)).toEqual(['Note 1', 'Note 3']);
    });

    it('should filter by either title or content', () => {
      const notes: Note[] = [
        createNote('1', 'Shopping List', '# Shopping List\n\nBuy groceries'),
        createNote('2', 'Meeting Notes', '# Meeting Notes\n\nDiscuss shopping'),
        createNote('3', 'Random Note', '# Random Note\n\nSome content'),
      ];

      const filtered = filterNotes(notes, 'shopping');

      expect(filtered).toHaveLength(2);
      expect(filtered.map((n) => n.title).sort()).toEqual([
        'Meeting Notes',
        'Shopping List',
      ]);
    });

    it('should handle partial matches', () => {
      const notes: Note[] = [
        createNote('1', 'JavaScript Tutorial', '# JavaScript\n\nLearning JS'),
        createNote('2', 'Java Basics', '# Java\n\nJava programming'),
        createNote('3', 'Python Guide', '# Python\n\nPython coding'),
      ];

      const filtered = filterNotes(notes, 'java');

      expect(filtered).toHaveLength(2);
      expect(filtered.map((n) => n.title).sort()).toEqual([
        'Java Basics',
        'JavaScript Tutorial',
      ]);
    });

    it('should return empty array when no matches found', () => {
      const notes: Note[] = [
        createNote('1', 'Note 1', '# Note 1\n\nContent'),
        createNote('2', 'Note 2', '# Note 2\n\nContent'),
      ];

      const filtered = filterNotes(notes, 'nonexistent');

      expect(filtered).toEqual([]);
    });

    it('should handle special characters in search query', () => {
      const notes: Note[] = [
        createNote('1', 'C++ Tutorial', '# C++\n\nLearning C++'),
        createNote('2', 'C# Guide', '# C#\n\nC# programming'),
        createNote('3', 'Python Guide', '# Python\n\nPython coding'),
      ];

      const filtered = filterNotes(notes, 'c++');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].title).toBe('C++ Tutorial');
    });

    it('should trim whitespace from search query', () => {
      const notes: Note[] = [
        createNote('1', 'Shopping List', '# Shopping List\n\nBuy groceries'),
        createNote('2', 'Meeting Notes', '# Meeting Notes\n\nDiscuss project'),
      ];

      const filtered = filterNotes(notes, '  shopping  ');

      expect(filtered).toHaveLength(1);
      expect(filtered[0].title).toBe('Shopping List');
    });

    it('should handle empty notes array', () => {
      const filtered = filterNotes([], 'search');
      expect(filtered).toEqual([]);
    });

    it('should not mutate original array', () => {
      const notes: Note[] = [
        createNote('1', 'Note 1', '# Note 1\n\nContent'),
        createNote('2', 'Note 2', '# Note 2\n\nContent'),
      ];

      const original = [...notes];
      filterNotes(notes, 'note 1');

      expect(notes).toEqual(original);
    });
  });
});
