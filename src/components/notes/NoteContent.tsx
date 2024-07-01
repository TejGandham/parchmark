import {
  Box,
  Flex,
  VStack,
  Text,
  Button,
  Heading,
  Input,
  Textarea,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { Note } from '../../types';
import { COLORS } from '../../utils/constants';
import NoteActions from './NoteActions';
import './styles/notes.css';
import './styles/markdown.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface NoteContentProps {
  currentNote: Note | undefined;
  isEditing: boolean;
  editedContent: string;
  setEditedContent: (content: string | null) => void;
  startEditing: () => void;
  saveNote: () => void;
  createNewNote: () => void;
}

const NoteContent = ({
  currentNote,
  isEditing,
  editedContent,
  setEditedContent,
  startEditing,
  saveNote,
  createNewNote,
}: NoteContentProps) => {
  if (!currentNote) {
    return (
      <VStack spacing={4} align="center" justify="center" h="100%">
        <Text>No note selected.</Text>
        <Button
          leftIcon={<FontAwesomeIcon icon={faPlus} />}
          bg="transparent"
          color={COLORS.primaryColor}
          border="1px solid"
          borderColor={COLORS.primaryLight}
          _hover={{ bg: 'rgba(88, 12, 36, 0.08)', transform: 'scale(1.05)' }}
          transition="all 0.2s"
          onClick={createNewNote}
        >
          Create New Note
        </Button>
      </VStack>
    );
  }

  // Extract the first line after the H1 to avoid duplicating the title in content
  const renderContent = () => {
    if (isEditing) {
      return editedContent;
    }

    // For viewing, remove the H1 title to prevent duplication
    const contentWithoutH1 = currentNote.content
      .replace(/^#\s+(.+)($|\n)/, '')
      .trim();
    return contentWithoutH1;
  };

  // Check if content has an H1 heading
  const hasH1Heading = editedContent.match(/^#\s+(.+)($|\n)/);

  // Get the title from H1 if it exists
  const h1TitleContent = hasH1Heading ? hasH1Heading[1].trim() : null;

  // Title is directly from the note object
  const title =
    isEditing && h1TitleContent ? h1TitleContent : currentNote.title;

  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="flex-start" mb={4}>
        <Heading size="lg" fontFamily="'Playfair Display', serif" mb={2}>
          {isEditing ? (
            <>
              <Input
                value={title}
                isReadOnly={true}
                fontWeight="bold"
                size="lg"
                width="100%"
                cursor="not-allowed"
                _hover={{
                  borderColor: 'gray.300',
                  background: 'gray.50',
                }}
                title="Title is controlled by the H1 heading in your content"
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Title is automatically set from H1 heading.
              </Text>
            </>
          ) : (
            currentNote.title
          )}
        </Heading>
        <NoteActions
          isEditing={isEditing}
          onEdit={startEditing}
          onSave={saveNote}
        />
      </Flex>

      {/* Content area */}
      <Box mt={4}>
        {isEditing ? (
          <Box className="edit-mode-indicator">
            <Textarea
              value={editedContent}
              onChange={(e) => {
                setEditedContent(e.target.value);
              }}
              minH="500px"
              p={4}
              width="100%"
              placeholder="# Your Title Here&#10;&#10;Start writing content..."
            />
          </Box>
        ) : (
          <>
            <Box className="decorative-divider" mb={5}></Box>
            <Box className="markdown-preview" p={4}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {renderContent()}
              </ReactMarkdown>
            </Box>
          </>
        )}
      </Box>
    </Box>
  );
};

export default NoteContent;
