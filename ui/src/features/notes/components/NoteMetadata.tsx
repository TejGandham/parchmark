import { HStack, Text, Tooltip } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faClock, faPenToSquare } from '@fortawesome/free-regular-svg-icons';
import {
  formatRelativeDate,
  formatFullDate,
  datesAreDifferent,
} from '../../../utils/dateFormatting';

interface NoteMetadataProps {
  createdAt: string;
  updatedAt: string;
}

const NoteMetadata = ({ createdAt, updatedAt }: NoteMetadataProps) => {
  const showModified = datesAreDifferent(createdAt, updatedAt);

  return (
    <HStack
      spacing={4}
      mt={1}
      mb={2}
      color="text.muted"
      fontSize="xs"
      fontWeight="normal"
      letterSpacing="wide"
    >
      <Tooltip label={formatFullDate(createdAt)} placement="bottom" hasArrow>
        <HStack spacing={1.5} cursor="default">
          <FontAwesomeIcon icon={faClock} fontSize="11px" />
          <Text as="span">{formatRelativeDate(createdAt)}</Text>
        </HStack>
      </Tooltip>

      {showModified && (
        <>
          <Text as="span" opacity={0.4}>
            ·
          </Text>
          <Tooltip
            label={formatFullDate(updatedAt)}
            placement="bottom"
            hasArrow
          >
            <HStack spacing={1.5} cursor="default">
              <FontAwesomeIcon icon={faPenToSquare} fontSize="11px" />
              <Text as="span">edited {formatRelativeDate(updatedAt)}</Text>
            </HStack>
          </Tooltip>
        </>
      )}
    </HStack>
  );
};

export default NoteMetadata;
