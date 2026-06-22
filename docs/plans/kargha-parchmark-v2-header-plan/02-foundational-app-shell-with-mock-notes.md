---
id: 02-foundational-app-shell-with-mock-notes
title: Implement foundational app shell with mock notes
type: task
parent: parchmark-v2-header
depends_on: [01-v2-custom-design-system-and-tokens]
estimate: M
status: Done
assignee: woodhouse@sam123.org
---

## Context

Implement the minimum V2 app shell needed for the header to render against realistic mock note state: desktop sidebar, mobile drawer, note filtering/list chrome, and app-level theme/nav state.

**Parent / group:** parchmark-v2-header
**Depends on:** [01-v2-custom-design-system-and-tokens]

## Design Reference

- **Design file:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- **View:** `notes/read` — initial read view with sidebar shell
- **Components in scope:** `AppShell`, `SidebarDrawer`, `BrandRow`, `SearchBox`, `TagFilter`, `NoteCard`, `UserFooter`, mobile scrim, mock note helpers
- **Screenshots:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/screenshots/`

## Component-to-Library Map

| Design Component | Library Mapping | Notes |
| ---------------- | ------------------------------------------------ | ----------------------------- |
| `App` shell | **Custom** — `AppShell.vue` | Owns active note, theme, nav drawer, mock state |
| `Sidebar` | **Custom** — `SidebarDrawer.vue` | Desktop fixed grid column, mobile off-canvas drawer |
| `NoteCard` | **Custom** — `NoteCard.vue` | Domain card with title, preview, time, tags |
| search field | **Custom** — `SearchBox.vue` | No component library; compose input + icon + clear button |
| tag filter | **Custom** — `TagFilter.vue` | Tokenized pill buttons |
| user footer | **Custom** — `UserFooter.vue` | Static mock identity, settings affordance |
| scrim | **Custom** — shell overlay | Uses `--scrim` token |

## Icon Mapping

| Design Icon | Source | Import | Notes |
| ----------- | ------ | ------ | ----- |
| `plus` | Custom SVG | `PlusIcon` from `@/design-system/icons` | New note button |
| `search` | Custom SVG | `SearchIcon` from `@/design-system/icons` | Search field |
| `x` | Custom SVG | `XIcon` from `@/design-system/icons` | Clear search |
| `gear` | Custom SVG | `GearIcon` from `@/design-system/icons` | Settings affordance |

## Component Plan

### AppShell (custom)

- **File:** `ui/src/features/shell/AppShell.vue`
- **Type:** view-controller
- **Props:**
    ```typescript
    interface AppShellProps {}
    ```
- **Styles:** CSS grid with `grid-template-columns: var(--sidebar-w) 1fr`, full viewport height, fixed grain overlay via `--paper-grain`.
- **Library components used:** none
- **Data ownership** (if applicable): owns local mock note array and derived active/filtered notes.
    ```typescript
    interface NoteMock {
      id: string
      tags: string[]
      createdAt: number
      updatedAt: number
      content: string
    }
    ```
- **Key behaviors:** initializes first note by newest `updatedAt`, opens/closes mobile drawer, sets `data-theme`, filters notes by search/tag state.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:15-73`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:187-198`

### SidebarDrawer (custom)

- **File:** `ui/src/features/shell/SidebarDrawer.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface SidebarDrawerProps {
      notes: NoteMock[]
      activeId: string | null
      search: string
      tags: Array<{ tag: string; count: number }>
      activeTags: string[]
      settingsActive?: boolean
    }
    ```
- **Styles:** tokenized sidebar background, border, desktop static column, mobile fixed drawer at `max-width: var(--sidebar-collapse)`.
- **Library components used:** `DsToolButton` only where icon-only button behavior is needed.
- **Key behaviors:** emits note select, new note, search update, clear search, tag toggle, open settings.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx:42-99`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:39-117`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:276-287`

### NoteCard (custom)

- **File:** `ui/src/features/notes/NoteCard.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface NoteCardProps {
      note: NoteMock
      active?: boolean
    }
    ```
- **Styles:** tokenized card radius, active border/elevation, left accent rule, serif title, clamped preview.
- **Library components used:** none
- **Key behaviors:** click selects note; active card is visually identical to mock.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx:101-118`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:91-104`

### SearchBox (custom)

- **File:** `ui/src/features/shell/SearchBox.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface SearchBoxProps {
      modelValue: string
      placeholder?: string
    }
    ```
- **Styles:** tokenized surface, border, focus ring, icon and clear button states.
- **Library components used:** none
- **Key behaviors:** emits `update:modelValue`, clear button appears only when search has a value.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx:59-63`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:60-71`

## Route / Layout

- **Route:** Vite app root renders `AppShell` directly.
- **Served URL:** `/`
- **Layout changes:** desktop grid shell with sidebar column; mobile drawer hidden until menu button opens it.
- **Navigation:** initial route loads the shell and selects the newest mock note.

## Data Layer

- **Operation:** local mock fixture only for this V2 foundational slice.
    ```typescript
    export interface NoteMock {
      id: string
      tags: string[]
      createdAt: number
      updatedAt: number
      content: string
    }

    export const mockNotes: NoteMock[] = [...]
    ```
- **Fetch policy / caching:** N/A, no network call.
- **Schema gaps:** none for this mock-data slice; backend persistence intentionally excluded.
- **Mock handlers:** none. Unit tests import `mockNotes`.

## Design Token Map

Full map: `docs/plans/kargha-parchmark-v2-header-plan/00-token-map.md`

The project's token/theme system is the **source of truth** for all design tokens. Do NOT copy the design's tokens stylesheet into the app — use project tokens via the custom design-system variables/classes. For a tiered (DTCG) system, map to the **consumable tier only** (typically semantic, never primitives — the Tier column makes this explicit).

| Design Token | Project Token (tier) | Usage |
| ------------------------ | --------------------------------- | ------------------------------------------ |
| `--sidebar-w` / `312px` | `layout.sidebar-width` wrapped by shell variable | desktop grid column |
| `--surface-2` / `#fbfaf7` | `semantic.color.surface-2` (semantic) | sidebar background |
| `--line-2` / `#e2ddd4` | `semantic.color.line-2` (semantic) | sidebar border, cards, inputs |
| `--surface` / `#ffffff` | `semantic.color.surface` (semantic) | cards, search field |
| `--paper-grain` | `semantic.color.paper-grain` (semantic) | app grain overlay |
| `--scrim` | `semantic.color.scrim` (semantic) | mobile drawer scrim |
| `--drawer-width` / `300px` | `semantic.dimension.drawer-width` (semantic) | mobile sidebar width |
| `--sidebar-collapse` / `860px` | `semantic.breakpoint.sidebar-collapse` (semantic) | mobile breakpoint |

**Tokens with no consumable-tier match:** none beyond the Token Changes inherited from ticket 01.

## Token Changes

| Token (path → var) | Op | Value — base / dark | Source file(s) | Covers | Auth |
|-|-|-|-|-|-|
| `semantic.color.paper-grain` → `--paper-grain` | `add` | `rgba(88,12,36,.025)` / dark `rgba(255,255,255,.022)` | `semantic.json`, `semantic.dark.json` | app shell grain pattern | autonomous |
| `semantic.color.scrim` → `--scrim` | `add` | `rgba(43,40,37,.3)` / dark `rgba(0,0,0,.42)` | `semantic.json`, `semantic.dark.json` | mobile drawer scrim | autonomous |
| `semantic.dimension.drawer-width` → `--drawer-width` | `add` | `300px` / dark same | `semantic.json` | mobile drawer width | autonomous |
| `semantic.breakpoint.sidebar-collapse` → `--sidebar-collapse` | `add` | `860px` / dark same | `semantic.json` | mobile shell breakpoint | autonomous |

## Acceptance Criteria

- [ ] App renders the desktop shell with a 312px sidebar and main content area.
- [ ] App renders the mobile drawer state matching screenshot `19-mobile-nav-drawer.png`.
- [ ] Mock note list groups by Today, Yesterday, Earlier this week, Earlier using the prototype helper logic.
- [ ] Search filters title/content and clear button behavior matches the mock.
- [ ] Tag filter toggles active tags and filters notes.
- [ ] Selecting a note closes the mobile drawer and updates active state.
- [ ] Components render matching design layout
- [ ] Library components used wherever mapped (see Component-to-Library Map)
- [ ] Interactive states work (hover, active, focus, disabled)
- [ ] Accessible: semantic HTML, keyboard navigation, ARIA where needed
- [ ] Co-located test files exist with smoke tests
- [ ] `cd ui && npm run lint` passes
- [ ] `cd ui && npm run test` passes
- [ ] (DTCG token systems) Token-conformance passes: no primitive-tier variable consumption in new code, no hand-edits to generated token artifacts, no hardcoded values duplicating tokens
- [ ] Design validation passes (match, or partial with only cosmetic/minor issues) — see Verification

## Implementation Notes

- Follow the V2 stack decision, not the current `ui/` React/Chakra implementation.
- Follow the local mock-data contract in this ticket; do not add backend work.
- Use custom DS components per the mapping table — do not add Chakra.
- All styling must reference project theme tokens — use project token variables/classes in custom styles. Never hardcode hex colors, px spacing, or px radii that duplicate project token values. For a tiered (DTCG) system, consume the **semantic tier only** — primitives are deny-listed for new code, and any needed-but-missing token is in this ticket's Token Changes section.
- Design uses inline styles — implementation must use Vue SFC styles and tokenized CSS.
- Design uses hardcoded mock data — implementation must use local typed mock fixtures.
- Design uses client-side `useState` navigation — implementation uses Vue state for this slice.
- **If a design-validation tool/skill is available:** run it in a loop (up to 3 rounds) to verify fidelity against the design prototype — see Verification

## Files to Create

- `ui/src/features/shell/AppShell.vue`
- `ui/src/features/shell/SidebarDrawer.vue`
- `ui/src/features/shell/SearchBox.vue`
- `ui/src/features/shell/TagFilter.vue`
- `ui/src/features/shell/UserFooter.vue`
- `ui/src/features/notes/NoteCard.vue`
- `ui/src/features/notes/mockNotes.ts`
- `ui/src/features/notes/noteMockHelpers.ts`
- `ui/src/features/shell/__tests__/AppShell.test.ts`
- `ui/src/features/shell/__tests__/SidebarDrawer.test.ts`
- `ui/src/features/notes/__tests__/noteMockHelpers.test.ts`

## Verification

```bash
cd ui && npm run build:tokens
cd ui && npm run lint
cd ui && npm run test
cd ui && npm run build
```

### Design Validation Loop (if available)

If the environment provides a design-validation tool/skill, run it to compare the running app against the design prototype. Treat it as a **required loop** — up to 3 rounds. Each round fixes `critical` then `major` discrepancies; the exit bar is **zero critical and zero major** (a `match`, or a `partial` with only minor/cosmetic left). Minor and cosmetic issues are acceptable — do not burn rounds chasing them; list any residuals in the PR body.

1. **Round 1:** Validate with the design file, app route, and navigation. Fix critical, then major, discrepancies.
2. **Round 2:** Re-validate after fixes. Fix any remaining critical/major.
3. **Round 3:** Final pass. Exit when zero critical and zero major remain; document any minor/cosmetic residuals as follow-up work.

Stop early once zero critical and zero major remain. Do not exceed 3 rounds — if major issues persist, document them as follow-up work. If no validation tool exists, this becomes a manual visual checklist against the design file.

**Validation parameters for this ticket:**

- Design file: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- App route: `/`
- Design navigation: load initial prototype view
- App navigation: load app root
- Viewport: `1440x900`
- Theme context(s): `base + dark (full)`
- Context switch (only for a `full` alternate context): click the theme toggle in the top bar
- Focus areas: desktop sidebar geometry, mobile drawer/scrim, note list active/hover/filter states
