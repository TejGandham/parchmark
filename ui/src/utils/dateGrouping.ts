// Utility functions for date-based grouping of notes

import { Note } from '../types';

export type DateGroup =
  | 'Today'
  | 'Yesterday'
  | 'This Week'
  | 'This Month'
  | 'Older';

export interface GroupedNotes {
  group: DateGroup;
  notes: Note[];
  count: number;
}

/**
 * Get the date group for a given date
 */
export const getDateGroup = (date: Date): DateGroup => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const monthAgo = new Date(today);
  monthAgo.setMonth(monthAgo.getMonth() - 1);

  const noteDate = new Date(date);
  const noteDateOnly = new Date(
    noteDate.getFullYear(),
    noteDate.getMonth(),
    noteDate.getDate()
  );

  if (noteDateOnly.getTime() === today.getTime()) {
    return 'Today';
  } else if (noteDateOnly.getTime() === yesterday.getTime()) {
    return 'Yesterday';
  } else if (noteDate >= weekAgo) {
    return 'This Week';
  } else if (noteDate >= monthAgo) {
    return 'This Month';
  } else {
    return 'Older';
  }
};

/**
 * Group notes by date
 */
export const groupNotesByDate = (
  notes: Note[],
  direction: SortDirection = 'desc'
): GroupedNotes[] => {
  const groups: Map<DateGroup, Note[]> = new Map();

  const newestFirst: DateGroup[] = [
    'Today',
    'Yesterday',
    'This Week',
    'This Month',
    'Older',
  ];

  const allGroups =
    direction === 'asc' ? [...newestFirst].reverse() : newestFirst;

  notes.forEach((note) => {
    const group = getDateGroup(new Date(note.updated_at));
    const existingNotes = groups.get(group) ?? [];
    groups.set(group, [...existingNotes, note]);
  });

  return allGroups
    .map((group) => {
      const groupedNotes = groups.get(group) ?? [];
      return {
        group,
        notes: groupedNotes,
        count: groupedNotes.length,
      };
    })
    .filter((groupData) => groupData.count > 0);
};

/**
 * Sort notes by different criteria
 */
export type SortOption = 'lastModified' | 'alphabetical' | 'createdDate';
export type SortDirection = 'asc' | 'desc';

export const sortNotes = (
  notes: Note[],
  sortBy: SortOption,
  direction: SortDirection = 'desc'
): Note[] => {
  const sorted = [...notes];
  const dir = direction === 'asc' ? 1 : -1;

  switch (sortBy) {
    case 'lastModified':
      return sorted.sort(
        (a, b) =>
          dir *
          (new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime())
      );
    case 'alphabetical':
      return sorted.sort(
        (a, b) =>
          dir *
          a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })
      );
    case 'createdDate':
      return sorted.sort(
        (a, b) =>
          dir *
          (new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      );
    default:
      return sorted;
  }
};

/**
 * Filter notes by search query
 */
export const filterNotes = (notes: Note[], searchQuery: string): Note[] => {
  if (!searchQuery || !searchQuery.trim()) {
    return notes;
  }

  const query = searchQuery.trim().toLowerCase();
  return notes.filter(
    (note) =>
      note.title.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query)
  );
};
