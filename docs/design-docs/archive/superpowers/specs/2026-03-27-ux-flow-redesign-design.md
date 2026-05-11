# UX Flow Redesign: List-First, Click-First

**Date**: 2026-03-27
**Status**: Approved
**Scope**: Routing, header, command palette, Explorer, note view

## Problem

The current UX is built around a keyboard-first, search-first paradigm. The command palette auto-opens on `/notes`, expecting users to search before seeing anything. Creating a note requires navigating to the Explorer or typing 4+ characters with no results in the palette. This doesn't match the actual workflow: **browse the list first, then search or create**.

## Design Decisions

### Principle Update

Design Principle #4 changes from "Keyboard-first" to:

> **Click-first, scan-friendly** — Design for visual scanning and direct manipulation. The notes list is home base; search is a quick-jump tool, not the front door.

All keyboard shortcuts and hints are removed entirely (code and UI). The palette and Explorer become mouse-driven.

## Changes by Section

### 1. Routing & Default View

| Route | Current | New |
|-|-|-|
| `/notes` | Empty state + auto-open palette | Explorer view (notes list with For You, date groups, sort) |
| `/notes/explore` | Explorer view | Redirect to `/notes` for backwards compatibility |
| `/notes/:noteId` | Note view | Unchanged |

- Remove the empty-state component ("Click the search bar above to find notes")
- Remove the `useEffect` that auto-opens the command palette on `/notes` load
- The Explorer component moves from the `/notes/explore` route to `/notes` (index route)

### 2. Header Redesign

**Current**: `Logo | [Search notes... (wide text button)] | [browse icon] [settings icon] [user dropdown]`

**New**: `Logo | [+ icon] [search icon] [settings icon] [user dropdown]`

- Replace the wide "Search notes..." text button with a compact search icon (magnifying glass). Still opens command palette on click.
- Remove the browse/explorer icon (Explorer is now the default view, no need to navigate to it)
- Add a "+" icon button for create note, positioned as leftmost action icon
- All three icon buttons are **identically styled** — same `IconButton` variant, size, hover, no button looks more "special" than another
- Tooltips on hover: "New note", "Search notes", "Settings"
- User dropdown remains separate from the icon group

### 3. Command Palette — Simplified + Delightful

The palette becomes a focused, mouse-driven search overlay.

**Remove:**
- All keyboard shortcut hints (footer bar removed entirely)
- Arrow key / Enter / Esc keyboard navigation code
- "Create new note" action (create lives in header now)

**Keep:**
- Search input with live filtering
- "Recent" section (5 most recent, shown when search empty)
- "For You" section (blended recommendations)
- Click-to-open behavior
- Framer Motion fade-in (0.15s) + backdrop blur (4px)

**Add (delight):**
- **Warm empty state**: Subtle placeholder text in `neutral.400` — "What are you looking for?" — fades out as user types
- **Result hover warmth**: Note items get `primary.50` background on hover (light burgundy) instead of gray
- **Smooth result transitions**: 0.1s opacity stagger via Framer Motion `AnimatePresence` with `layout` prop when results filter in/out

### 4. Explorer Toolbar Cleanup

**Remove:**
- "+ New Note" button (now in header)
- Keyboard shortcut footer

**Keep:**
- Inline search input (placeholder: "Filter notes...")
- Sort controls (Modified / A-Z / Created + direction toggle)
- For You section at top
- Date-grouped note cards
- Virtualized rendering (react-window for 100+ notes)

Toolbar becomes: `[search input] [sort controls]` — two quiet tools, no buttons competing.

### 5. Note View Cleanup

**Remove:**
- "New Note" button from NoteContent/NoteActions (redundant with header)

**Keep everything else unchanged:**
- Edit/Save/Cancel buttons
- Note metadata display
- Markdown preview / textarea toggle
- Delete action in menu

### 6. Icon Button Normalization

**Standardize all header icon buttons:**
- **One icon library**: FontAwesome consistently (`faPlus`, `faMagnifyingGlass`, `faGear`)
- **Identical styling**: `variant="ghost"`, `colorScheme="primary"`, same `size`
- **Same hover**: `primary.50` background (light mode), `primary.900` (dark mode)
- **Same icon size**: all at same `fontSize` so none appears heavier
- **Tooltips**: Chakra `Tooltip` on each — "New note", "Search notes", "Settings"
- **`aria-label`**: Required on each for accessibility

## What Does NOT Change

- Note editing flow (edit/save/cancel)
- Note deletion flow
- Settings page
- Authentication/OIDC flow
- API endpoints
- For You scoring algorithm
- Dark mode support
- Virtualization behavior

## Files Affected (Estimated)

| File | Change |
|-|-|
| `ui/src/router.tsx` | Move Explorer to index route, remove `/notes/explore`, remove auto-palette logic |
| `ui/src/features/ui/components/Header.tsx` | Replace search text button + browse icon with three normalized icon buttons |
| `ui/src/features/ui/components/CommandPalette.tsx` | Remove keyboard handlers, shortcut footer, create action. Add hover warmth, empty state text, result transitions |
| `ui/src/features/notes/components/NotesExplorer.tsx` | Remove from `/notes/explore` route context |
| `ui/src/features/notes/components/ExplorerToolbar.tsx` | Remove "+ New Note" button, remove shortcut footer |
| `ui/src/features/notes/components/NoteContent.tsx` | Remove "New Note" button |
| `ui/src/features/notes/components/NoteActions.tsx` | Remove "New Note" action if present |
| `ui/src/features/ui/store.ts` | Remove palette auto-open state/logic |
| `AGENTS.md` | Design Principle #4 updated (already done) |

## Design Principles Alignment

| Principle | How This Serves It |
|-|-|
| Content is king | Notes list is immediately visible, no overlay blocking content |
| Speed over spectacle | One less click to see notes, one less click to create |
| Quiet confidence | Icon normalization, warm hover states, no loud CTA buttons |
| Click-first, scan-friendly | Browse first, search second — matches actual workflow |
| Reduce, don't add | Fewer buttons, fewer shortcuts, fewer modes |
