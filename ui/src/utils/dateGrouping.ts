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
export const groupNotesByDate = (notes: Note[]): GroupedNotes[] => {
  const groups: Map<DateGroup, Note[]> = new Map();

  // Initialize all groups
  const allGroups: DateGroup[] = [
    'Today',
    'Yesterday',
    'This Week',
    'This Month',
    'Older',
  ];
  allGroups.forEach((group) => groups.set(group, []));

  // Group notes
  notes.forEach((note) => {
    const group = getDateGroup(new Date(note.updated_at));
    const existingNotes = groups.get(group) || [];
    groups.set(group, [...existingNotes, note]);
  });

  // Convert to array and filter out empty groups
  return allGroups
    .map((group) => ({
      group,
      notes: groups.get(group) || [],
      count: (groups.get(group) || []).length,
    }))
    .filter((groupData) => groupData.count > 0);
};

/**
 * Sort notes by different criteria
 */
export type SortOption = 'lastModified' | 'alphabetical' | 'createdDate';

export const sortNotes = (notes: Note[], sortBy: SortOption): Note[] => {
  const sorted = [...notes];

  switch (sortBy) {
    case 'lastModified':
      return sorted.sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
    case 'alphabetical':
      return sorted.sort((a, b) =>
        a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })
      );
    case 'createdDate':
      return sorted.sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    default:
      return sorted;
  }
};

/**
 * Filter notes by search query
 */
export const filterNotes = (notes: Note[], searchQuery: string): Note[] => {
  if (!searchQuery.trim()) {
    return notes;
  }

  const query = searchQuery.toLowerCase();
  return notes.filter(
    (note) =>
      note.title.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query)
  );
};
