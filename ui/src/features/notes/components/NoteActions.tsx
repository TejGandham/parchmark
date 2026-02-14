import { HStack, Button } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faSave } from '@fortawesome/free-solid-svg-icons';

interface NoteActionsProps {
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
  isSaving?: boolean;
}

const NoteActions = ({
  isEditing,
  onEdit,
  onSave,
  isSaving = false,
}: NoteActionsProps) => {
  return (
    <HStack>
      {isEditing ? (
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
      ) : (
        <Button
          leftIcon={<FontAwesomeIcon icon={faEdit} />}
          onClick={onEdit}
          variant="secondary"
          aria-label="Edit note"
          _hover={{ transform: 'scale(1.05)' }}
        >
          Edit
        </Button>
      )}
    </HStack>
  );
};

export default NoteActions;
