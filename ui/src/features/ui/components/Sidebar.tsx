import {
  Box,
  Flex,
  Heading,
  IconButton,
  List,
  VStack,
  Text,
  Icon,
  Button,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { AddIcon } from '@chakra-ui/icons';
import { Note } from '../../../types';
import NoteItem from '../../notes/components/NoteItem';

interface SidebarProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string | null) => void;
  onCreateNote: () => void;
  onDeleteNote: (id: string) => void;
}

const Sidebar = ({
  notes,
  currentNoteId,
  onSelectNote,
  onCreateNote,
  onDeleteNote,
}: SidebarProps) => {
  return (
    <Box
      w="250px"
      bg="bg.surface"
      p={4}
      borderRight="1px solid"
      borderColor="border.default"
      overflowY="auto"
      className="sidebar-shadow"
    >
      <Flex justify="space-between" mb={4}>
        <Heading size="sm" fontFamily="'Playfair Display', serif">
          Notes
        </Heading>
        <IconButton
          aria-label="Create new note"
          icon={<FontAwesomeIcon icon={faPlus} />}
          size="sm"
          onClick={onCreateNote}
          variant="ghost"
          colorScheme="primary"
          _hover={{ transform: 'scale(1.05)' }}
        />
      </Flex>
      <List spacing={1}>
        {Array.isArray(notes) && notes.length > 0 ? (
          notes.map((note) => (
            <NoteItem
              key={note.id}
              note={note}
              isActive={note.id === currentNoteId}
              onSelect={onSelectNote}
              onDelete={onDeleteNote}
            />
          ))
        ) : (
          <VStack spacing={4} py={8} px={2}>
            <Box
              w="60px"
              h="60px"
              bg="primary.50"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              _dark={{
                bg: 'primary.900',
              }}
            >
              <Icon as={AddIcon} fontSize="2xl" color="primary.600" />
            </Box>
            <VStack spacing={2}>
              <Heading
                size="sm"
                color="text.primary"
                fontFamily="'Playfair Display', serif"
                textAlign="center"
              >
                No notes yet
              </Heading>
              <Text fontSize="xs" color="text.muted" textAlign="center" maxW="180px">
                Start capturing your thoughts and ideas
              </Text>
            </VStack>
            <Button
              size="sm"
              colorScheme="primary"
              onClick={onCreateNote}
              leftIcon={<Icon as={AddIcon} />}
              boxShadow="sm"
              _hover={{
                transform: 'translateY(-2px)',
                boxShadow: 'md',
              }}
            >
              Create Note
            </Button>
          </VStack>
        )}
      </List>
    </Box>
  );
};

export default Sidebar;
