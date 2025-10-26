import { HStack, Button } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faSave } from '@fortawesome/free-solid-svg-icons';

interface NoteActionsProps {
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
}

const NoteActions = ({ isEditing, onEdit, onSave }: NoteActionsProps) => {
  return (
    <HStack>
      {isEditing ? (
        <Button
          leftIcon={<FontAwesomeIcon icon={faSave} />}
          onClick={onSave}
          variant="secondary"
          _hover={{ transform: 'scale(1.05)' }}
        >
          Save
        </Button>
      ) : (
        <Button
          leftIcon={<FontAwesomeIcon icon={faEdit} />}
          onClick={onEdit}
          variant="secondary"
          _hover={{ transform: 'scale(1.05)' }}
        >
          Edit
        </Button>
      )}
    </HStack>
  );
};

export default NoteActions;
