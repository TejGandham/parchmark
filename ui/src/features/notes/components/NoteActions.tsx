import { HStack, Button, IconButton, Tooltip } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faSave, faTrash } from '@fortawesome/free-solid-svg-icons';

interface NoteActionsProps {
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel?: () => void;
  onDelete?: () => void;
  isSaving?: boolean;
  isDeleting?: boolean;
}

const NoteActions = ({
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onDelete,
  isSaving = false,
  isDeleting = false,
}: NoteActionsProps) => {
  return (
    <HStack>
      {isEditing ? (
        <>
          <Button
            onClick={onCancel}
            variant="ghost"
            aria-label="Cancel editing"
            isDisabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            leftIcon={<FontAwesomeIcon icon={faSave} />}
            onClick={onSave}
            isLoading={isSaving}
            loadingText="Saving"
            variant="secondary"
            aria-label="Save note changes"
            _hover={{ transform: 'scale(1.05)' }}
          >
            Save
          </Button>
        </>
      ) : (
        <>
          {onDelete && (
            <Tooltip label="Delete note" placement="bottom">
              <IconButton
                aria-label="Delete note"
                icon={<FontAwesomeIcon icon={faTrash} />}
                variant="ghost"
                size="sm"
                color="text.muted"
                isLoading={isDeleting}
                _hover={{ color: 'red.500', bg: 'red.50' }}
                onClick={onDelete}
              />
            </Tooltip>
          )}
          <Button
            leftIcon={<FontAwesomeIcon icon={faEdit} />}
            onClick={onEdit}
            variant="secondary"
            aria-label="Edit note"
            isDisabled={isDeleting}
            _hover={{ transform: 'scale(1.05)' }}
          >
            Edit
          </Button>
        </>
      )}
    </HStack>
  );
};

export default NoteActions;
