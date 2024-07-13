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
import { Note } from '../../../types';
import { COLORS } from '../../../utils/constants';
import {
  extractTitleFromMarkdown,
  removeH1FromContent,
} from '../../../services/markdownService';
import NoteActions from './NoteActions';
import '../styles/notes.css';
import '../styles/markdown.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface NoteContentProps {
  currentNote: Note | null | undefined;
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
  // Handle case when no note is selected, or we're in the process of creating one
  if (!currentNote) {
    // If we're editing (creating a new note) but currentNote is not yet set
    if (isEditing && editedContent) {
      return (
        <Box>
          <Flex justifyContent="space-between" alignItems="flex-start" mb={4}>
            <Heading size="lg" fontFamily="'Playfair Display', serif" mb={2}>
              {extractTitleFromMarkdown(editedContent)}
            </Heading>
            <NoteActions
              isEditing={isEditing}
              onEdit={() => {
                /* Already editing */
              }}
              onSave={saveNote}
            />
          </Flex>
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
        </Box>
      );
    }

    // Default "no note" view
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
      // When editing, show the full content
      return editedContent;
    }

    // Remove the H1 title to prevent duplication in the rendered output
    return removeH1FromContent(currentNote.content);
  };

  // Get the title - when editing use the H1 heading from content
  const title = isEditing
    ? extractTitleFromMarkdown(editedContent)
    : currentNote.title;

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
