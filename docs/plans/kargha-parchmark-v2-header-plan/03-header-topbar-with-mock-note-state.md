---
id: 03-header-topbar-with-mock-note-state
title: Implement header topbar with mock note state
type: task
parent: parchmark-v2-header
depends_on: [01-v2-custom-design-system-and-tokens, 02-foundational-app-shell-with-mock-notes]
estimate: M
status: In Review
assignee: woodhouse@sam123.org
---

## Context

Implement the foundational ParchMark V2 header exactly from the mock: breadcrumb, read/edit segment, editing indicator, theme toggle, overflow menu, and mobile drawer trigger wired to mock note state.

**Parent / group:** parchmark-v2-header
**Depends on:** [01-v2-custom-design-system-and-tokens, 02-foundational-app-shell-with-mock-notes]

## Design Reference

- **Design file:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- **View:** `notes/read` — initial read view topbar
- **Components in scope:** `AppTopbar`, `BreadcrumbTrail`, `ReadEditSegment`, `EditingFlag`, `ThemeToggleButton`, `OverflowNoteMenu`, mobile menu trigger
- **Screenshots:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/screenshots/`

## Component-to-Library Map

| Design Component | Library Mapping | Notes |
| ---------------- | ------------------------------------------------ | ----------------------------- |
| `.topbar` | **Custom** — `AppTopbar.vue` | App chrome, tokenized exact layout |
| `.crumb` | **Custom** — `BreadcrumbTrail.vue` | Domain-specific breadcrumb text |
| `.seg` | **Custom** — `DsSegment` composed by `ReadEditSegment` | Reuses DS primitive from ticket 01 |
| `.editing-flag` | **Custom** — `EditingFlag.vue` | Small status indicator with pulse |
| theme tool button | **Custom** — `DsToolButton` | Uses sun/moon icons and `data-theme` state |
| overflow menu | **Custom** — `DsMenu` composed by `OverflowNoteMenu` | Edit, copy, export, delete actions |
| mobile menu trigger | **Custom** — `DsToolButton` | Opens shell drawer |

## Icon Mapping

| Design Icon | Source | Import | Notes |
| ----------- | ------ | ------ | ----- |
| `menu` | Custom SVG | `MenuIcon` from `@/design-system/icons` | mobile drawer trigger |
| `eye` | Custom SVG | `EyeIcon` from `@/design-system/icons` | Read segment item |
| `edit` | Custom SVG | `EditIcon` from `@/design-system/icons` | Edit segment/menu item |
| `moon` | Custom SVG | `MoonIcon` from `@/design-system/icons` | light-mode theme toggle |
| `sun` | Custom SVG | `SunIcon` from `@/design-system/icons` | dark-mode theme toggle |
| `more` | Custom SVG | `MoreIcon` from `@/design-system/icons` | overflow trigger |
| `copy` | Custom SVG | `CopyIcon` from `@/design-system/icons` | copy markdown menu item |
| `download` | Custom SVG | `DownloadIcon` from `@/design-system/icons` | export menu item |
| `trash` | Custom SVG | `TrashIcon` from `@/design-system/icons` | delete menu item |

## Component Plan

### AppTopbar (custom)

- **File:** `ui/src/features/shell/AppTopbar.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface AppTopbarProps {
      activeNote: NoteMock | null
      activeTags: string[]
      mode: 'read' | 'edit'
      dirty?: boolean
      theme: 'light' | 'dark'
      menuOpen: boolean
    }
    ```
- **Styles:** tokenized from `.topbar`: flex, gap `--topbar-gap`, padding `--topbar-padding-y`/`--topbar-padding-x`, border `--line`, background `--topbar-bg`, backdrop blur 8px.
- **Library components used:** `DsToolButton`, `DsSegment`, `DsMenu`.
- **Key behaviors:** emits open drawer, start edit, change mode, toggle theme, toggle overflow menu, copy, export, request delete.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:207-245`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:121-143`

### BreadcrumbTrail (custom)

- **File:** `ui/src/features/shell/BreadcrumbTrail.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface BreadcrumbTrailProps {
      title: string
      activeTags: string[]
    }
    ```
- **Styles:** 13px muted flex row, 7px gap, title in text-2 with 600 weight, separator tokenized rather than primitive `--n300`.
- **Library components used:** none
- **Key behaviors:** displays `Filtered #tag... / Title` when filters are active, otherwise `All notes / Title`.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:209-214`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:126-127`

### ReadEditSegment (custom)

- **File:** `ui/src/features/shell/ReadEditSegment.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface ReadEditSegmentProps {
      mode: 'read' | 'edit'
      disabled?: boolean
    }
    ```
- **Styles:** delegates to `DsSegment`; no new layout tokens.
- **Library components used:** `DsSegment`
- **Key behaviors:** shows only when active note exists and mode is `read`; read item active; edit item emits start edit.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:217-221`

### EditingFlag (custom)

- **File:** `ui/src/features/shell/EditingFlag.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface EditingFlagProps {
      label?: string
    }
    ```
- **Styles:** inline-flex 13px/600 accent color, 7px pulse dot using `--accent`; dark mode uses `--accent-600`.
- **Library components used:** none
- **Key behaviors:** renders only when active note exists and mode is `edit`.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:223-225`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:204-207`

### OverflowNoteMenu (custom)

- **File:** `ui/src/features/shell/OverflowNoteMenu.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface OverflowNoteMenuProps {
      open: boolean
      note: NoteMock
    }
    ```
- **Styles:** delegates to `DsMenu`; positioned relative with menu top offset 42px and right aligned.
- **Library components used:** `DsToolButton`, `DsMenu`
- **Key behaviors:** click outside close, Edit note, Copy markdown, Export .md, Delete note. For this ticket, copy/export/delete can use mock local behavior and emit events; destructive confirmation modal is out of scope.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/app.jsx:231-244`, `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:255-261`

## Route / Layout

- **Route:** Vite app root renders `AppShell`, which includes `AppTopbar`.
- **Served URL:** `/`
- **Layout changes:** topbar sits at the top of the main content column, above the note content placeholder or future read view.
- **Navigation:** load root route with newest mock note selected; use mobile menu button to open the sidebar drawer.

## Data Layer

- **Operation:** local mock fixture inherited from ticket 02.
    ```typescript
    interface HeaderNoteViewModel {
      id: string
      title: string
      content: string
      tags: string[]
      updatedAt: number
    }
    ```
- **Fetch policy / caching:** N/A, no network call.
- **Schema gaps:** none for this mock-data slice; backend persistence intentionally excluded.
- **Mock handlers:** none. Unit tests pass mock note props directly.

## Design Token Map

Full map: `docs/plans/kargha-parchmark-v2-header-plan/00-token-map.md`

The project's token/theme system is the **source of truth** for all design tokens. Do NOT copy the design's tokens stylesheet into the app — use project tokens via the custom design-system variables/classes. For a tiered (DTCG) system, map to the **consumable tier only** (typically semantic, never primitives — the Tier column makes this explicit).

| Design Token | Project Token (tier) | Usage |
| ------------------------ | --------------------------------- | ------------------------------------------ |
| `rgba(246,244,239,.85)` | `semantic.color.topbar-bg` (semantic) | topbar translucent background |
| `rgba(27,25,23,.82)` | `semantic.color.topbar-bg` dark override (semantic) | dark topbar translucent background |
| `12px 28px` | `semantic.dimension.topbar-padding-y/x` (semantic) | topbar padding |
| `14px` | `semantic.dimension.topbar-gap` (semantic) | topbar flex gap |
| `34px` | `semantic.dimension.tool-size` (semantic) | icon button size |
| `9px` | `semantic.dimension.tool-radius` (semantic) | icon button radius |
| `--surface` | `semantic.color.surface` (semantic) | tool/menu active backgrounds |
| `--line` | `semantic.color.line` (semantic) | topbar bottom border |
| `--line-2` | `semantic.color.line-2` (semantic) | tool/menu borders |
| `--text-2` | `semantic.color.text-2` (semantic) | icon button and breadcrumb title |
| `--muted` | `semantic.color.muted` (semantic) | breadcrumb base text |
| `--accent` | `semantic.color.accent` (semantic) | active read segment, hover states |
| `#b3261e` | `semantic.color.danger` (semantic) | delete menu text |
| `#fdecea` | `semantic.color.danger-surface` (semantic) | delete hover background |

**Tokens with no consumable-tier match:** component-level topbar/menu literals listed in Token Changes.

## Token Changes

| Token (path → var) | Op | Value — base / dark | Source file(s) | Covers | Auth |
|-|-|-|-|-|-|
| `semantic.color.topbar-bg` → `--topbar-bg` | `add` | `rgba(246,244,239,.85)` / dark `rgba(27,25,23,.82)` | `semantic.json`, `semantic.dark.json` | topbar translucent backdrop | autonomous |
| `semantic.color.danger` → `--danger` | `add` | `#b3261e` / dark `#f08a80` | `semantic.json`, `semantic.dark.json` | overflow delete action | autonomous |
| `semantic.color.danger-surface` → `--danger-surface` | `add` | `#fdecea` / dark `#3a1f1d` | `semantic.json`, `semantic.dark.json` | danger hover background | autonomous |
| `semantic.dimension.topbar-padding-x` → `--topbar-padding-x` | `add` | `28px` / dark same | `semantic.json` | topbar horizontal padding | autonomous |
| `semantic.dimension.topbar-padding-y` → `--topbar-padding-y` | `add` | `12px` / dark same | `semantic.json` | topbar vertical padding | autonomous |
| `semantic.dimension.topbar-gap` → `--topbar-gap` | `add` | `14px` / dark same | `semantic.json` | topbar flex gap | autonomous |
| `semantic.dimension.tool-size` → `--tool-size` | `add` | `34px` / dark same | `semantic.json` | icon button dimensions | autonomous |
| `semantic.dimension.tool-radius` → `--tool-radius` | `add` | `9px` / dark same | `semantic.json` | icon button radius | autonomous |
| `semantic.dimension.segment-radius` → `--segment-radius` | `add` | `9px` / dark same | `semantic.json` | segment container radius | autonomous |
| `semantic.dimension.segment-item-radius` → `--segment-item-radius` | `add` | `7px` / dark same | `semantic.json` | segment item radius | autonomous |
| `semantic.dimension.menu-radius` → `--menu-radius` | `add` | `12px` / dark same | `semantic.json` | overflow menu radius | autonomous |

## Acceptance Criteria

- [ ] Header topbar matches desktop screenshot `01-initial-read-view.png`.
- [ ] Overflow menu matches screenshot `08-overflow-menu.png`, including danger row and separator.
- [ ] Mobile topbar and drawer trigger match screenshots `18-mobile-read-view.png` and `19-mobile-nav-drawer.png`.
- [ ] Theme toggle updates `document.documentElement.dataset.theme` between light and dark.
- [ ] Breadcrumb displays active note title derived from first H1.
- [ ] Read/Edit segment and editing flag render in the same conditions as the mock.
- [ ] Overflow menu closes on outside click and Escape.
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
- Follow the mock-data contract from ticket 02.
- Use custom DS components per the mapping table — do not add Chakra or an external UI kit.
- All styling must reference project theme tokens — use project token variables/classes in custom styles. Never hardcode hex colors, px spacing, or px radii that duplicate project token values. For a tiered (DTCG) system, consume the **semantic tier only** — primitives are deny-listed for new code, and any needed-but-missing token is in this ticket's Token Changes section.
- Design uses inline styles — implementation must use Vue SFC styles and tokenized CSS.
- Design uses hardcoded mock data — implementation must use local typed mock fixtures.
- Design uses client-side `useState` navigation — implementation uses Vue state for this slice.
- **If a design-validation tool/skill is available:** run it in a loop (up to 3 rounds) to verify fidelity against the design prototype — see Verification

## Files to Create

- `ui/src/features/shell/AppTopbar.vue`
- `ui/src/features/shell/BreadcrumbTrail.vue`
- `ui/src/features/shell/ReadEditSegment.vue`
- `ui/src/features/shell/EditingFlag.vue`
- `ui/src/features/shell/ThemeToggleButton.vue`
- `ui/src/features/shell/OverflowNoteMenu.vue`
- `ui/src/features/shell/__tests__/AppTopbar.test.ts`
- `ui/src/features/shell/__tests__/OverflowNoteMenu.test.ts`
- `ui/src/features/shell/__tests__/ThemeToggleButton.test.ts`

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
- Focus areas: topbar spacing, breadcrumb, read/edit segment, tool buttons, overflow menu
