import { useMemo, useEffect, useRef, useCallback } from 'react';
import {
  useParams,
  useRouteLoaderData,
  useSearchParams,
  useFetcher,
} from 'react-router-dom';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Button,
  Heading,
  Input,
  Textarea,
  Icon,
  Skeleton,
  SkeletonText,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
} from '@chakra-ui/react';
import { AddIcon, EditIcon, InfoIcon } from '@chakra-ui/icons';
import { Note } from '../../../types';
import {
  extractTitleFromMarkdown,
  removeH1FromContent,
} from '../../../services/markdownService';
import NoteActions from './NoteActions';
import NoteMetadata from './NoteMetadata';
import '../styles/notes.css';
import '../styles/markdown.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import Mermaid from '../../../components/Mermaid';
import { useNotesUIStore } from '../../../store';

// Stable reference for markdown plugins - prevents recreation on each render
const remarkPlugins = [remarkGfm];
const rehypePlugins = [rehypeRaw];

const NoteContent = () => {
  // Data router hooks
  const { noteId } = useParams<{ noteId: string }>();
  const loaderData = useRouteLoaderData('notes-layout') as
    | { notes: Note[] }
    | undefined;
  const notes = loaderData?.notes ?? [];
  const [searchParams, setSearchParams] = useSearchParams();
  const fetcher = useFetcher();

  // UI state from store
  const editedContent = useNotesUIStore((s) => s.editedContent);
  const setEditedContent = useNotesUIStore((s) => s.setEditedContent);

  // Track pending save to clear state after success
  // Stores the noteId that was being saved to handle rapid saves correctly
  const pendingSaveNoteIdRef = useRef<string | null>(null);

  const {
    isOpen: isDeleteDialogOpen,
    onOpen: openDeleteDialog,
    onClose: closeDeleteDialog,
  } = useDisclosure();
  const cancelDeleteRef = useRef<HTMLButtonElement>(null);

  // Derived state
  const isEditing = searchParams.get('editing') === 'true';
  const currentNote = notes.find((n) => n.id === noteId) || null;
  const isSaving = fetcher.state === 'submitting';

  // Clear editing state only after save completes successfully
  // Check that the completed save matches the note we're viewing to handle rapid saves
  useEffect(() => {
    if (
      pendingSaveNoteIdRef.current === noteId &&
      fetcher.state === 'idle' &&
      fetcher.data?.ok
    ) {
      setSearchParams({});
      setEditedContent(null);
      pendingSaveNoteIdRef.current = null;
    }
  }, [fetcher.state, fetcher.data, noteId, setSearchParams, setEditedContent]);

  // Handlers
  const startEditing = () => {
    if (currentNote) {
      setEditedContent(currentNote.content);
      setSearchParams({ editing: 'true' });
    }
  };

  const cancelEditing = useCallback(() => {
    setSearchParams({});
    setEditedContent(null);
  }, [setSearchParams, setEditedContent]);

  const saveNote = () => {
    if (!noteId || !editedContent) return;
    pendingSaveNoteIdRef.current = noteId;
    fetcher.submit(
      { content: editedContent },
      { method: 'post', action: `/notes/${noteId}` }
    );
  };

  // Escape key exits edit mode
  useEffect(() => {
    if (!isEditing) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        cancelEditing();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isEditing, cancelEditing]);

  const createNewNote = () => {
    fetcher.submit(null, { method: 'post', action: '/notes' });
  };

  const confirmDelete = () => {
    if (!noteId) return;
    fetcher.submit(null, {
      method: 'post',
      action: `/notes/${noteId}/delete`,
    });
    closeDeleteDialog();
  };

  // Memoize markdown components to prevent recreation on every render
  // Must be called before any early returns to satisfy Rules of Hooks
  const markdownComponents = useMemo(
    () => ({
      code({
        className,
        children,
        ...props
      }: {
        className?: string;
        children?: React.ReactNode;
      }) {
        const match = /language-(\w+)/.exec(className || '');
        if (match && match[1] === 'mermaid') {
          return <Mermaid chart={String(children).replace(/\n$/, '')} />;
        }
        return (
          <code className={className} {...props}>
            {children}
          </code>
        );
      },
    }),
    [] // Empty deps - components definition is stable
  );

  const isDeleting = fetcher.formAction?.includes('/delete') ?? false;

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
              onCancel={cancelEditing}
              isSaving={isSaving}
            />
          </Flex>
          <Box className="edit-mode-indicator">
            <Textarea
              value={editedContent}
              onChange={(e) => {
                setEditedContent(e.target.value);
              }}
              minH="calc(100vh - 250px)"
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
      <VStack spacing={6} align="center" justify="center" h="100%" px={8}>
        <Box
          w="120px"
          h="120px"
          bg="primary.50"
          borderRadius="full"
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <Icon as={EditIcon} fontSize="5xl" color="primary.300" />
        </Box>

        <VStack spacing={2}>
          <Heading
            size="lg"
            color="text.primary"
            fontFamily="'Playfair Display', serif"
          >
            Ready to capture your thoughts?
          </Heading>
          <Text
            fontSize="md"
            color="text.muted"
            textAlign="center"
            maxW="400px"
          >
            Press Ctrl+Shift+Space to search or create a new note to get started
          </Text>
        </VStack>

        <Button
          size="lg"
          colorScheme="primary"
          leftIcon={<Icon as={AddIcon} />}
          onClick={createNewNote}
          boxShadow="md"
          _hover={{
            transform: 'translateY(-2px)',
            boxShadow: 'lg',
          }}
        >
          Create New Note
        </Button>

        <VStack spacing={3} mt={8} align="stretch" maxW="400px">
          <HStack spacing={3} align="flex-start">
            <Icon as={InfoIcon} color="primary.500" mt={0.5} />
            <Text fontSize="sm" textAlign="left" color="text.secondary">
              Full Markdown support for rich formatting
            </Text>
          </HStack>
          <HStack spacing={3} align="flex-start">
            <Icon as={EditIcon} color="primary.500" mt={0.5} />
            <Text fontSize="sm" textAlign="left" color="text.secondary">
              Click Save to keep your work safe
            </Text>
          </HStack>
        </VStack>
      </VStack>
    );
  }

  // Extract the first line after the H1 to avoid duplicating the title in content
  const renderContent = () => {
    if (isEditing) {
      // When editing, show the full content
      return editedContent ?? '';
    }

    // Remove the H1 title to prevent duplication in the rendered output
    return removeH1FromContent(currentNote.content);
  };

  // Get the title - when editing use the H1 heading from content
  const title = isEditing
    ? extractTitleFromMarkdown(editedContent ?? '')
    : currentNote.title;

  const previewContent = renderContent();

  if (isSaving && !isEditing) {
    return (
      <Box data-testid="note-loading-skeleton">
        <Skeleton height="32px" width="60%" mb={4} />
        <Skeleton height="16px" width="40%" mb={6} />
        <SkeletonText noOfLines={8} spacing={4} />
      </Box>
    );
  }

  return (
    <Box
      opacity={isDeleting ? 0.3 : 1}
      transition="opacity 0.3s ease"
      data-testid="note-content-wrapper"
    >
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
                  borderColor: 'border.default',
                  background: 'bg.subtle',
                }}
                title="Title is controlled by the H1 heading in your content"
              />
              <Text fontSize="xs" color="text.muted" mt={1}>
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
          onCancel={cancelEditing}
          onDelete={openDeleteDialog}
          isSaving={isSaving}
          isDeleting={isDeleting}
        />
      </Flex>

      {!isEditing && (
        <NoteMetadata
          createdAt={currentNote.createdAt}
          updatedAt={currentNote.updatedAt}
        />
      )}

      {/* Content area */}
      <Box mt={4}>
        {isEditing ? (
          <Box className="edit-mode-indicator">
            <Textarea
              value={editedContent ?? ''}
              onChange={(e) => {
                setEditedContent(e.target.value);
              }}
              minH="calc(100vh - 250px)"
              p={4}
              width="100%"
              placeholder="# Your Title Here&#10;&#10;Start writing content..."
            />
          </Box>
        ) : (
          <>
            <Box className="decorative-divider" mb={5}></Box>
            <Box className="markdown-preview" p={4}>
              <ReactMarkdown
                remarkPlugins={remarkPlugins}
                rehypePlugins={rehypePlugins}
                components={markdownComponents}
              >
                {previewContent}
              </ReactMarkdown>
            </Box>
          </>
        )}
      </Box>

      <AlertDialog
        isOpen={isDeleteDialogOpen}
        leastDestructiveRef={cancelDeleteRef}
        onClose={closeDeleteDialog}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Delete Note
            </AlertDialogHeader>
            <AlertDialogBody>
              Are you sure you want to delete &ldquo;{currentNote.title}
              &rdquo;? This action cannot be undone.
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelDeleteRef} onClick={closeDeleteDialog}>
                Cancel
              </Button>
              <Button colorScheme="red" onClick={confirmDelete} ml={3}>
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default NoteContent;
