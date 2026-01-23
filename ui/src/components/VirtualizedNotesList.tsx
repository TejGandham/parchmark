import React, { useMemo } from 'react';
import { List, type RowComponentProps } from 'react-window';
import { Box } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import NoteItem from '../features/notes/components/NoteItem';
import { Note } from '../types';

const MotionBox = motion(Box);

interface VirtualizedNotesListProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string | null) => void;
  onDeleteNote: (id: string) => void;
  height: number;
}

const ITEM_HEIGHT = 48; // Height of NoteItem in pixels

// Custom props passed to each row
interface NoteRowProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string | null) => void;
  onDeleteNote: (id: string) => void;
}

// Row component for react-window v2
const NoteRow = ({
  index,
  style,
  notes,
  currentNoteId,
  onSelectNote,
  onDeleteNote,
}: RowComponentProps<NoteRowProps>) => {
  const note = notes[index];
  return (
    <MotionBox
      style={style}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.3) }}
    >
      <NoteItem
        note={note}
        isActive={note.id === currentNoteId}
        onSelect={onSelectNote}
        onDelete={onDeleteNote}
      />
    </MotionBox>
  );
};

/**
 * Virtualized notes list for improved performance with large note collections.
 * Only renders visible items in the DOM.
 */
const VirtualizedNotesList: React.FC<VirtualizedNotesListProps> = ({
  notes,
  currentNoteId,
  onSelectNote,
  onDeleteNote,
  height,
}) => {
  // Memoize row props to prevent unnecessary re-renders
  const rowProps = useMemo(
    () => ({
      notes,
      currentNoteId,
      onSelectNote,
      onDeleteNote,
    }),
    [notes, currentNoteId, onSelectNote, onDeleteNote]
  );

  return (
    <List
      style={{ height, width: '100%' }}
      rowCount={notes.length}
      rowHeight={ITEM_HEIGHT}
      rowComponent={NoteRow}
      rowProps={rowProps}
    />
  );
};

export default React.memo(VirtualizedNotesList);
