# UX Flow Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure ParchMark's UX from search-first/keyboard-first to list-first/click-first by promoting the Explorer to the default view, adding a persistent create button to the header, and simplifying the command palette.

**Architecture:** The Explorer (currently at `/notes/explore`) becomes the index route at `/notes`. The header gets three normalized icon buttons (create, search, settings). The command palette drops keyboard navigation and create actions, gaining warm hover/transition polish instead. All keyboard shortcut code and hints are removed.

**Tech Stack:** React 18, React Router v7, Chakra UI v2, Zustand, Framer Motion, FontAwesome icons

---

### Task 1: Route Explorer to Index

**Files:**
- Modify: `ui/src/router.tsx:73-86`
- Modify: `ui/src/features/notes/components/NotesLayout.tsx:1-95`
- Test: `ui/src/__tests__/router.test.tsx`
- Test: `ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`

- [ ] **Step 1: Update router — make Explorer the index route**

In `ui/src/router.tsx`, replace the empty index route and the `explore` route with the Explorer as the index:

```tsx
// Replace lines 73-86:
    children: [
      {
        index: true,
        lazy: async () => {
          const { default: Component } = await import(
            './features/notes/components/NotesExplorer'
          );
          return { Component };
        },
      },
      {
        path: 'explore',
        loader: () => redirect('/notes'),
      },
      {
```

The `explore` path now redirects to `/notes` for backwards compatibility. Import `redirect` is already imported at line 2.

- [ ] **Step 2: Remove empty state and auto-open palette from NotesLayout**

In `ui/src/features/notes/components/NotesLayout.tsx`:

Remove imports no longer needed: `useEffect`, `useMatch`, `EditIcon`, `Heading`, `Icon`, `VStack`, `Link` (the `Link` from react-router-dom used for "browse all notes"). Remove `useUIStore` import and `openPalette` usage.

Replace the entire component with:

```tsx
import { Outlet, useLoaderData } from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';
import Header from '../../ui/components/Header';
import { CommandPalette } from '../../ui/components/CommandPalette';
import { Note } from '../../../types';
import '../../ui/styles/layout.css';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      <Flex h="100vh" flexDirection="column">
        <Header />
        <CommandPalette notes={notes} />

        <Box
          as="main"
          id="main-content"
          flex="1"
          overflowY="auto"
          className="note-transition"
          aria-label="Note content"
        >
          <Outlet />
        </Box>
      </Flex>
    </Box>
  );
}
```

Key changes: removed the `useEffect` that auto-opens palette, removed the `isExplore` match, removed the empty state VStack, removed conditional padding (Explorer handles its own padding), removed skip-to-content link (it pointed to a now-simpler layout).

- [ ] **Step 3: Update router tests**

In `ui/src/__tests__/router.test.tsx`, update or remove tests that:
- Assert the index route renders `null` (it now renders NotesExplorer)
- Assert `/notes/explore` renders the Explorer (it now redirects to `/notes`)

Add a test that `/notes/explore` redirects to `/notes`:

```tsx
it('redirects /notes/explore to /notes', async () => {
  // Navigate to /notes/explore and verify redirect
});
```

- [ ] **Step 4: Update NotesLayout tests**

In `ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`, remove tests for:
- Auto-opening the command palette
- The empty state ("Click the search bar above")
- The "browse all notes" link

- [ ] **Step 5: Run tests and verify**

Run: `cd ui && npx vitest run --reporter=verbose 2>&1 | head -80`
Expected: All router and NotesLayout tests pass. Some other tests may need attention (addressed in later tasks).

- [ ] **Step 6: Commit**

```bash
git add ui/src/router.tsx ui/src/features/notes/components/NotesLayout.tsx ui/src/__tests__/router.test.tsx ui/src/__tests__/features/notes/components/NotesLayout.test.tsx
git commit -m "feat: promote Explorer to default /notes route, remove empty state"
```

---

### Task 2: Redesign Header — Normalized Icon Buttons

**Files:**
- Modify: `ui/src/features/ui/components/Header.tsx:1-81`
- Test: `ui/src/__tests__/features/ui/components/Header.test.tsx`

- [ ] **Step 1: Read existing Header tests**

Read `ui/src/__tests__/features/ui/components/Header.test.tsx` to understand what's currently tested. Note which test IDs and assertions need updating.

- [ ] **Step 2: Rewrite Header component**

Replace the entire `ui/src/features/ui/components/Header.tsx` with:

```tsx
import { Flex, HStack, Heading, IconButton, Image, Tooltip } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faMagnifyingGlass, faGear } from '@fortawesome/free-solid-svg-icons';
import { useNavigate, useFetcher } from 'react-router-dom';
import { UserLoginStatus } from '../../auth/components';
import { useUIStore } from '../store/ui';
import Logo from '../../../../assets/images/parchmark.svg';
import { useCallback, useEffect, useRef } from 'react';

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
        <Heading size="md" ml={1} fontFamily="heading">
          <Image src={Logo} alt="ParchMark Logo" h="46px" mr="10px" />
        </Heading>
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
```

Key changes:
- Three identically-styled icon buttons via shared `ICON_BUTTON_PROPS`
- FontAwesome icons consistently: `faPlus`, `faMagnifyingGlass`, `faGear`
- Create button uses `useFetcher` to POST to `/notes` directly
- Browse/explorer icon removed (Explorer is now the default view)
- Wide "Search notes..." text button replaced with compact icon
- Tooltips on all three buttons
- Removed `SearchIcon` and `Button` imports from Chakra, removed `faTableList` import

- [ ] **Step 3: Update Header tests**

Update `ui/src/__tests__/features/ui/components/Header.test.tsx`:
- Remove test for "Search notes..." text button
- Remove test for explorer-link icon button
- Add test for `header-create-btn` (new note button exists and is clickable)
- Update palette-trigger test (now an IconButton, not a Button with text)
- Add test for `header-settings-btn`
- Verify all three buttons render with tooltips

- [ ] **Step 4: Run tests**

Run: `cd ui && npx vitest run src/__tests__/features/ui/components/Header.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/src/features/ui/components/Header.tsx ui/src/__tests__/features/ui/components/Header.test.tsx
git commit -m "feat: redesign header with normalized icon buttons (create, search, settings)"
```

---

### Task 3: Simplify Command Palette

**Files:**
- Modify: `ui/src/features/ui/components/CommandPalette.tsx:1-517`
- Test: `ui/src/__tests__/features/ui/components/CommandPalette.test.tsx`

- [ ] **Step 1: Read existing CommandPalette tests**

Read `ui/src/__tests__/features/ui/components/CommandPalette.test.tsx` to understand current test coverage.

- [ ] **Step 2: Remove keyboard navigation and create action**

In `ui/src/features/ui/components/CommandPalette.tsx`:

**Remove these imports** (no longer needed):
- `useCallback`, `useState` from react (keep `useRef`, `useEffect`, `useMemo`)
- `useFetcher`, `useNavigation` from react-router-dom (keep `useNavigate`, `useParams`)
- `Button`, `Skeleton` from chakra (keep rest)

**Remove these state/refs:**
- `const [activeIndex, setActiveIndex] = useState(0);` — no keyboard nav
- `const fetcher = useFetcher(...)` — no create action
- `const navigation = useNavigation()` — skeleton was for route loading
- `const isRouteLoading = ...`
- `const createInitiatedRef = useRef(false)`
- `const canCreate = ...`
- `const isCreating = ...`

**Remove the keyboard handler** `useEffect` block (lines 196-238) — the one that listens for `window.addEventListener('keydown', ...)`.

**Remove the `handleCreate` callback** and the `useEffect` that navigates after create (lines 171-194).

**Remove the `activeIndex` reset** `useEffect` (lines 149-151).

**Update `PaletteNoteItem`:**
- Remove `isActive` prop entirely — no keyboard selection state
- Change hover to warm burgundy: `_hover={{ bg: 'primary.50' }}`
- Remove conditional `bg` based on `isActive`
- Remove conditional color based on `isActive`

**Update the palette body:**
- Remove the skeleton loading block (lines 303-327)
- Remove the create action block within search results (lines 367-392) — the "Create 'xyz'" button
- Remove the zero-notes "Create your first note" button (lines 396-417) — replace with just a "No notes yet" text
- Remove the keyboard shortcuts footer (lines 500-510)
- Update "Browse All Notes →" link to navigate to `/notes` instead of `/notes/explore`
- Change search input placeholder from `"Search notes..."` to `"What are you looking for?"`

**Add delight:**
- On `PaletteNoteItem`, add `transition="background 0.15s ease"` for smooth hover
- Wrap the results `VStack` items with Framer Motion `layout` prop for smooth filtering:

```tsx
<motion.div layout transition={{ duration: 0.1 }}>
  <PaletteNoteItem ... />
</motion.div>
```

- [ ] **Step 3: Write the simplified CommandPalette**

The full replacement component (showing key structural changes):

```tsx
import { useRef, useEffect, useMemo, type MouseEvent, type MutableRefObject } from 'react';
import { Portal, Box, Input, Text, VStack, HStack } from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { useUIStore } from '../store/ui';
import { Note, SimilarNote } from '../../../types';
import { filterNotes, sortNotes } from '../../../utils/dateGrouping';
import { formatCompactTime } from '../../../utils/compactTime';
import { getBlendedForYouNotes } from '../../../utils/noteScoring';
import { trackNoteAccess, getSimilarNotes } from '../../../services/api';
import { highlightKeyword } from './commandPaletteUtils';
import { useState } from 'react';

interface CommandPaletteProps {
  notes?: Note[];
}

interface PaletteNoteItemProps {
  note: Note;
  searchQuery?: string;
  onSelect: (id: string) => void;
}

function PaletteNoteItem({ note, searchQuery, onSelect }: PaletteNoteItemProps) {
  return (
    <HStack
      px={4}
      py={2}
      cursor="pointer"
      bg="transparent"
      _hover={{ bg: 'primary.50' }}
      onClick={() => onSelect(note.id)}
      spacing={3}
      transition="background 0.15s ease"
      data-testid="palette-note-item"
    >
      <Text fontSize="sm" noOfLines={1} flex={1} color="text.primary">
        {searchQuery ? highlightKeyword(note.title, searchQuery) : note.title}
      </Text>
      <Text fontSize="xs" color="text.muted" flexShrink={0}>
        {formatCompactTime(note.updatedAt)}
      </Text>
    </HStack>
  );
}

export const CommandPalette = ({ notes = [] }: CommandPaletteProps) => {
  const isPaletteOpen = useUIStore((state) => state.isPaletteOpen);
  const closePalette = useUIStore((state) => state.actions.closePalette);
  const searchQuery = useUIStore((state) => state.paletteSearchQuery);
  const setSearchQuery = useUIStore((state) => state.actions.setPaletteSearchQuery);
  const searchInputRef = useRef<HTMLInputElement>(null) as MutableRefObject<HTMLInputElement | null>;
  const navigate = useNavigate();
  const { noteId: currentNoteId } = useParams<{ noteId: string }>();

  const [similarNotes, setSimilarNotes] = useState<SimilarNote[]>([]);

  const setSearchInputRef = (node: HTMLInputElement | null) => {
    searchInputRef.current = node;
    if (node) node.focus();
  };

  useEffect(() => {
    if (!isPaletteOpen || !currentNoteId) {
      setSimilarNotes([]);
      return;
    }
    let cancelled = false;
    getSimilarNotes(currentNoteId).then((result) => {
      if (!cancelled) setSimilarNotes(result);
    });
    return () => { cancelled = true; };
  }, [isPaletteOpen, currentNoteId]);

  const recentNotes = useMemo(
    () => sortNotes(notes, 'lastModified', 'desc').slice(0, 5),
    [notes]
  );

  const forYouNotes = useMemo(
    () => getBlendedForYouNotes(notes, currentNoteId ?? null, similarNotes, 3),
    [notes, currentNoteId, similarNotes]
  );

  const filteredNotes = useMemo(
    () => (searchQuery ? filterNotes(notes, searchQuery) : []),
    [notes, searchQuery]
  );

  const isSearching = searchQuery.length > 0;

  useEffect(() => {
    if (isPaletteOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isPaletteOpen]);

  const handleSelect = (noteId: string) => {
    navigate(`/notes/${noteId}`);
    closePalette();
    trackNoteAccess(noteId);
  };

  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === e.currentTarget) closePalette();
  };

  return (
    <Portal>
      <AnimatePresence>
        {isPaletteOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <Box
              position="fixed"
              top={0} left={0} right={0} bottom={0}
              bg="blackAlpha.600"
              backdropFilter="blur(4px)"
              zIndex={1400}
              onClick={handleBackdropClick}
              data-testid="command-palette-backdrop"
            />

            <Box
              role="dialog"
              aria-label="Command palette"
              position="fixed"
              top="15vh"
              left="50%"
              transform="translateX(-50%)"
              width={{ base: '90vw', md: '520px' }}
              maxHeight="60vh"
              bg="bg.surface"
              borderRadius="xl"
              boxShadow="xl"
              overflow="hidden"
              zIndex={1500}
              data-testid="command-palette"
            >
              <Input
                ref={setSearchInputRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="What are you looking for?"
                size="lg"
                border="none"
                borderBottom="1px solid"
                borderColor="border.default"
                borderRadius={0}
                _focus={{ borderColor: 'primary.300', boxShadow: 'none' }}
                _placeholder={{ color: 'neutral.400' }}
                data-testid="command-palette-search"
              />

              <VStack spacing={0} align="stretch" overflowY="auto" maxHeight="50vh">
                {isSearching && (
                  <>
                    <Box px={4} py={1.5} borderBottom="1px" borderColor="neutral.200" bg="neutral.100">
                      <Text fontSize="xs" color="text.muted" data-testid="search-result-count">
                        {filteredNotes.length} {filteredNotes.length === 1 ? 'result' : 'results'}
                      </Text>
                    </Box>
                    <AnimatePresence mode="popLayout">
                      {filteredNotes.map((note) => (
                        <motion.div
                          key={note.id}
                          layout
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.1 }}
                        >
                          <PaletteNoteItem note={note} searchQuery={searchQuery} onSelect={handleSelect} />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                    {filteredNotes.length === 0 && (
                      <Box px={4} py={3} textAlign="center">
                        <Text fontSize="sm" color="text.muted" data-testid="no-notes-found">
                          No notes found
                        </Text>
                      </Box>
                    )}
                  </>
                )}

                {!isSearching && notes.length === 0 && (
                  <Box p={8} textAlign="center" data-testid="zero-notes-state">
                    <Text color="text.muted" fontSize="sm">No notes yet</Text>
                  </Box>
                )}

                {!isSearching && forYouNotes.length > 0 && (
                  <>
                    <Box px={4} py={1.5} borderBottom="1px" borderColor="secondary.100" bg="secondary.50">
                      <Text fontSize="xs" fontWeight="bold" color="section.forYou" letterSpacing="wide" data-testid="for-you-header">
                        FOR YOU
                      </Text>
                    </Box>
                    {forYouNotes.map((note) => (
                      <PaletteNoteItem key={`fy-${note.id}`} note={note} onSelect={handleSelect} />
                    ))}
                  </>
                )}

                {!isSearching && notes.length > 0 && (
                  <>
                    <Box px={4} py={1.5} borderBottom="1px" borderColor="primary.100" bg="primary.50">
                      <Text fontSize="xs" fontWeight="bold" color="section.recent" letterSpacing="wide" data-testid="recent-header">
                        RECENT
                      </Text>
                    </Box>
                    {recentNotes.map((note) => (
                      <PaletteNoteItem key={note.id} note={note} onSelect={handleSelect} />
                    ))}
                  </>
                )}
              </VStack>

              {!isSearching && notes.length > 0 && (
                <Box
                  px={4} py={2}
                  borderTop="1px solid"
                  borderColor="border.default"
                  cursor="pointer"
                  _hover={{ bg: 'primary.50' }}
                  onClick={() => { navigate('/notes'); closePalette(); }}
                  data-testid="browse-all-link"
                >
                  <Text fontSize="sm" color="primary.600">Browse All Notes →</Text>
                </Box>
              )}
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
};
```

- [ ] **Step 4: Update CommandPalette tests**

In `ui/src/__tests__/features/ui/components/CommandPalette.test.tsx`:
- Remove all keyboard navigation tests (ArrowDown, ArrowUp, Enter, Escape, Cmd+Enter)
- Remove create-from-search tests
- Remove "Create your first note" button test
- Remove skeleton/loading state tests
- Remove `activeIndex` / `isActive` related assertions
- Update the `PaletteNoteItem` tests to not pass `isActive`
- Add test: hover on note item shows `primary.50` background
- Add test: search input placeholder is "What are you looking for?"
- Keep tests for: opening/closing palette, search filtering, Recent section, For You section, Browse All link

- [ ] **Step 5: Run tests**

Run: `cd ui && npx vitest run src/__tests__/features/ui/components/CommandPalette.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ui/src/features/ui/components/CommandPalette.tsx ui/src/__tests__/features/ui/components/CommandPalette.test.tsx
git commit -m "feat: simplify command palette — remove keyboard nav, create action, add warm hover"
```

---

### Task 4: Clean Up Explorer — Remove Toolbar Button and Keyboard Shortcuts

**Files:**
- Modify: `ui/src/features/notes/components/ExplorerToolbar.tsx:1-146`
- Modify: `ui/src/features/notes/components/NotesExplorer.tsx:1-366`
- Test: `ui/src/__tests__/features/notes/components/ExplorerToolbar.test.tsx`
- Test: `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx`

- [ ] **Step 1: Read existing tests**

Read both test files to understand current coverage.

- [ ] **Step 2: Simplify ExplorerToolbar**

In `ui/src/features/notes/components/ExplorerToolbar.tsx`:

Remove the `onCreateNote` and `isCreating` props from `ExplorerToolbarProps`. Remove the `AddIcon` import. Remove the "New Note" `Button` (lines 128-137). Remove the `useEffect` for the `/` keyboard shortcut (lines 72-83). Update placeholder to `"Filter notes..."`.

Updated interface and component:

```tsx
interface ExplorerToolbarProps {
  totalNotes: number;
}
```

Remove the `useEffect` block (lines 72-83) that handles the `/` key focus shortcut.

Remove the `Button` with `data-testid="explorer-create-btn"` from the HStack (lines 128-137).

Update Input placeholder from `"Search notes…"` to `"Filter notes..."`.

- [ ] **Step 3: Remove keyboard shortcuts from NotesExplorer**

In `ui/src/features/notes/components/NotesExplorer.tsx`:

Remove the `activeIndex` state and all references to it:
- `const [activeIndex, setActiveIndex] = useState(-1);` (line 61)
- The `useEffect` that resets activeIndex (lines 96-98)
- The entire keyboard handler `useEffect` (lines 133-171)
- All `isActive={... === activeIndex}` props on `ExplorerNoteCard`
- `activeIndex` from `VirtualRowData` interface and `VirtualExplorerRow` props

Remove the keyboard shortcut footer (lines 354-363):
```tsx
<Box px={{ base: 4, md: 6 }} py={2} borderTopWidth="1px" borderColor="border.default">
  <Text fontSize="xs" color="text.muted">
    ↑↓ navigate · Enter open · / search · Esc back
  </Text>
</Box>
```

Update the `ExplorerToolbar` call to remove `onCreateNote` and `isCreating` props:

```tsx
<ExplorerToolbar totalNotes={notes.length} />
```

Remove the `handleCreate` callback entirely — create is now in the Header. Also remove the `createInitiatedRef`, the `fetcher` usage, `isCreating`, `canCreate`, and the `useEffect` that navigates after create.

Remove the "Create from search" button in the search results empty state (lines 287-298). Keep the "No notes found" text.

Remove the "Create your first note" button in the empty state (lines 312-320). Keep the "No notes yet" text.

- [ ] **Step 4: Update ExplorerToolbar tests**

In `ui/src/__tests__/features/notes/components/ExplorerToolbar.test.tsx`:
- Remove tests for the "+ New Note" button (`explorer-create-btn`)
- Remove tests for the `/` keyboard shortcut
- Update component rendering to not pass `onCreateNote` or `isCreating`
- Keep tests for search input, sort controls

- [ ] **Step 5: Update NotesExplorer tests**

In `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx`:
- Remove all keyboard navigation tests (ArrowUp/Down, Enter, Escape)
- Remove shortcut footer assertion
- Remove create-from-search tests
- Remove "Create your first note" button test
- Remove `activeIndex`-related assertions
- Keep tests for: rendering notes, search filtering, sort, For You section, date groups

- [ ] **Step 6: Run tests**

Run: `cd ui && npx vitest run src/__tests__/features/notes/components/ExplorerToolbar.test.tsx src/__tests__/features/notes/components/NotesExplorer.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add ui/src/features/notes/components/ExplorerToolbar.tsx ui/src/features/notes/components/NotesExplorer.tsx ui/src/__tests__/features/notes/components/ExplorerToolbar.test.tsx ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx
git commit -m "feat: clean up Explorer — remove create button, keyboard shortcuts, shortcut footer"
```

---

### Task 5: Clean Up NoteContent — Remove Create Fallback

**Files:**
- Modify: `ui/src/features/notes/components/NoteContent.tsx:127-216`
- Test: `ui/src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx`

- [ ] **Step 1: Remove create action from NoteContent**

In `ui/src/features/notes/components/NoteContent.tsx`:

Remove the `createNewNote` function (lines 127-129). Remove the `AddIcon` import (line 27). Remove `Icon` from the Chakra import.

Replace the "no note selected" fallback (lines 202-216) with a simple redirect or message:

```tsx
// Default "no note" view — user should be on Explorer
return (
  <VStack spacing={4} align="center" justify="center" h="100%" px={8}>
    <Text fontSize="md" color="text.muted">
      Select a note to view it
    </Text>
  </VStack>
);
```

This state is rarely reachable since Explorer is now the default, but it's a safe fallback.

- [ ] **Step 2: Update NoteContent tests**

In `ui/src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx`:
- Remove test for "New Note" button in the empty state
- Update the empty state test to expect "Select a note to view it" text instead

- [ ] **Step 3: Run tests**

Run: `cd ui && npx vitest run src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add ui/src/features/notes/components/NoteContent.tsx ui/src/__tests__/features/notes/components/NoteContentDataRouter.test.tsx
git commit -m "feat: remove create note fallback from NoteContent, simplify empty state"
```

---

### Task 6: Clean Up UI Store

**Files:**
- Modify: `ui/src/features/ui/store/ui.ts`
- Test: `ui/src/__tests__/features/ui/store/ui.test.ts`

- [ ] **Step 1: Remove togglePalette if unused**

Check if `togglePalette` is used anywhere now that keyboard shortcuts are removed:

Run: `grep -r "togglePalette" ui/src/ --include="*.ts" --include="*.tsx" | grep -v "store/ui.ts" | grep -v "__tests__"`

If no results (nothing uses it), remove `togglePalette` from the store actions and type.

- [ ] **Step 2: Update store tests**

Remove the `togglePalette` test if the action was removed.

- [ ] **Step 3: Run tests**

Run: `cd ui && npx vitest run src/__tests__/features/ui/store/ui.test.ts --reporter=verbose`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add ui/src/features/ui/store/ui.ts ui/src/__tests__/features/ui/store/ui.test.ts
git commit -m "chore: remove unused togglePalette from UI store"
```

---

### Task 7: Full Test Suite + Lint

**Files:**
- All modified files from Tasks 1-6

- [ ] **Step 1: Run full UI test suite**

Run: `cd ui && npx vitest run --reporter=verbose 2>&1 | tail -30`
Expected: All tests pass

- [ ] **Step 2: Run UI lint**

Run: `cd ui && npm run lint`
Expected: No errors (0 warnings allowed)

- [ ] **Step 3: Fix any failures**

If tests fail, read the failure output, identify the root cause, and fix. Common issues:
- Test files importing removed exports (like `togglePalette`)
- Snapshot tests with stale snapshots
- Tests expecting removed elements (keyboard hints, create buttons)

- [ ] **Step 4: Run full CI pipeline**

Run: `make test`
Expected: All checks pass (UI lint + tests, backend lint + format + types + pytest)

- [ ] **Step 5: Commit any fixes**

```bash
git add -u
git commit -m "fix: resolve test failures from UX redesign"
```

---

### Task 8: Update Explorer Padding in NotesLayout

**Files:**
- Modify: `ui/src/features/notes/components/NotesLayout.tsx`

- [ ] **Step 1: Adjust padding for note view vs Explorer**

The Explorer handles its own padding internally (`px={{ base: 4, md: 6 }}`). But `NoteContent` expects padding from the parent layout. Update NotesLayout to apply padding only when viewing a note:

In `NotesLayout.tsx`, the `<Box as="main">` needs conditional padding. Since we removed `isExplore`, use the route match:

```tsx
import { Outlet, useLoaderData, useParams } from 'react-router-dom';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      <Flex h="100vh" flexDirection="column">
        <Header />
        <CommandPalette notes={notes} />

        <Box
          as="main"
          id="main-content"
          flex="1"
          p={noteId ? 6 : 0}
          overflowY={noteId ? 'auto' : 'hidden'}
          className="note-transition"
          aria-label="Note content"
        >
          <Outlet />
        </Box>
      </Flex>
    </Box>
  );
}
```

- [ ] **Step 2: Run affected tests**

Run: `cd ui && npx vitest run src/__tests__/features/notes/components/NotesLayout.test.tsx --reporter=verbose`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add ui/src/features/notes/components/NotesLayout.tsx
git commit -m "fix: restore conditional padding for note view vs Explorer"
```
