import { useRef, useCallback, useEffect } from 'react';
import {
  Flex,
  HStack,
  Heading,
  IconButton,
  Image,
  Tooltip,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPlus,
  faMagnifyingGlass,
  faGear,
} from '@fortawesome/free-solid-svg-icons';
import { useNavigate, useFetcher, Link } from 'react-router-dom';
import { UserLoginStatus } from '../../auth/components';
import { useUIStore } from '../store/ui';
import Logo from '../../../../assets/images/parchmark.svg';

const ICON_BUTTON_PROPS = {
  variant: 'ghost' as const,
  colorScheme: 'primary' as const,
  size: 'md' as const,
  fontSize: 'lg' as const,
  _hover: { bg: 'primary.50' },
};

const Header = () => {
  const navigate = useNavigate();
  const openPalette = useUIStore((s) => s.actions.openPalette);
  const fetcher = useFetcher<{ id: string; title: string }>();
  const createInitiatedRef = useRef(false);

  const handleCreate = useCallback(() => {
    if (fetcher.state !== 'idle') return;
    createInitiatedRef.current = true;
    fetcher.submit(
      { content: '# New Note\n\n', title: 'New Note' },
      { method: 'post', action: '/notes' }
    );
  }, [fetcher]);

  useEffect(() => {
    if (
      createInitiatedRef.current &&
      fetcher.state === 'idle' &&
      fetcher.data?.id
    ) {
      createInitiatedRef.current = false;
      navigate(`/notes/${fetcher.data.id}?editing=true`);
    }
  }, [fetcher.state, fetcher.data, navigate]);

  return (
    <Flex
      as="header"
      bg="bg.surface"
      color="primary.800"
      p={3}
      align="center"
      justify="space-between"
      borderBottom="1px solid"
      borderColor="border.default"
    >
      <HStack spacing={3}>
        <Link
          to="/notes"
          aria-label="Go to notes list"
          style={{ textDecoration: 'none' }}
        >
          <Heading size="md" ml={1} fontFamily="heading">
            <Image src={Logo} alt="ParchMark Logo" h="46px" mr="10px" />
          </Heading>
        </Link>
      </HStack>

      <HStack spacing={2}>
        <Tooltip label="New note" placement="bottom">
          <IconButton
            aria-label="New note"
            icon={<FontAwesomeIcon icon={faPlus} />}
            onClick={handleCreate}
            isLoading={fetcher.state !== 'idle'}
            data-testid="header-create-btn"
            {...ICON_BUTTON_PROPS}
          />
        </Tooltip>
        <Tooltip label="Search notes" placement="bottom">
          <IconButton
            aria-label="Search notes"
            icon={<FontAwesomeIcon icon={faMagnifyingGlass} />}
            onClick={openPalette}
            data-testid="palette-trigger"
            {...ICON_BUTTON_PROPS}
          />
        </Tooltip>
        <Tooltip label="Settings" placement="bottom">
          <IconButton
            aria-label="Settings"
            icon={<FontAwesomeIcon icon={faGear} />}
            onClick={() => navigate('/settings')}
            data-testid="header-settings-btn"
            {...ICON_BUTTON_PROPS}
          />
        </Tooltip>
        <UserLoginStatus />
      </HStack>
    </Flex>
  );
};

export default Header;
