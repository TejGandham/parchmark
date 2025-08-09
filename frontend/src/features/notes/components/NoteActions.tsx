import { HStack, Button } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faSave } from '@fortawesome/free-solid-svg-icons';
import { COLORS } from '../../../utils/constants';

interface NoteActionsProps {
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
}

const NoteActions = ({ isEditing, onEdit, onSave }: NoteActionsProps) => {
  const buttonStyle = {
    bg: 'transparent',
    color: COLORS.primaryColor,
    border: '1px solid',
    borderColor: COLORS.primaryLight,
    _hover: { bg: 'rgba(88, 12, 36, 0.08)', transform: 'scale(1.05)' },
    transition: 'all 0.2s',
  };

  return (
    <HStack>
      {isEditing ? (
        <Button
          leftIcon={<FontAwesomeIcon icon={faSave} />}
          onClick={onSave}
          {...buttonStyle}
        >
          Save
        </Button>
      ) : (
        <Button
          leftIcon={<FontAwesomeIcon icon={faEdit} />}
          onClick={onEdit}
          {...buttonStyle}
        >
          Edit
        </Button>
      )}
    </HStack>
  );
};

export default NoteActions;
