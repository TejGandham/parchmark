---
id: 01-v2-custom-design-system-and-tokens
title: Establish Vue V2 custom design system and tokens
type: task
parent: parchmark-v2-header
depends_on: []
estimate: M
status: Done
assignee: woodhouse@sam123.org
---

## Context

Set up the new Vue V2 frontend foundation and custom design system so later header and shell work can implement the mock 1:1 without Chakra or current React UI decisions.

**Parent / group:** parchmark-v2-header
**Depends on:** none

## Design Reference

- **Design file:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- **View:** `none` — setup ticket, design validation not applicable
- **Components in scope:** token build, generated token CSS, font loading, base app styles, `DsIcon`, `DsToolButton`, `DsSegment`, `DsMenu`
- **Screenshots:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/screenshots/`

## Component-to-Library Map

| Design Component | Library Mapping | Notes |
| ---------------- | ------------------------------------------------ | ----------------------------- |
| `I` icon object | **Custom** — Vue DS icon components | Port exact SVG paths from `prototype/components.jsx` |
| `.tool` | **Custom** — `DsToolButton` | 34px square icon button, tokenized radius/border/surface |
| `.seg` | **Custom** — `DsSegment` | Read/Edit segmented control primitive |
| `.menu` | **Custom** — `DsMenu` | Tokenized popover menu primitive |
| token CSS | **Custom** — DTCG token pipeline | Adopt the mock's token source and generate app CSS |

## Icon Mapping

| Design Icon | Source | Import | Notes |
| ----------- | ------ | ------ | ----- |
| `plus` | Custom SVG | `PlusIcon` from `@/design-system/icons` | direct port |
| `search` | Custom SVG | `SearchIcon` from `@/design-system/icons` | direct port |
| `gear` | Custom SVG | `GearIcon` from `@/design-system/icons` | direct port |
| `more` | Custom SVG | `MoreIcon` from `@/design-system/icons` | direct port |
| `edit` | Custom SVG | `EditIcon` from `@/design-system/icons` | direct port |
| `eye` | Custom SVG | `EyeIcon` from `@/design-system/icons` | direct port |
| `trash` | Custom SVG | `TrashIcon` from `@/design-system/icons` | direct port |
| `download` | Custom SVG | `DownloadIcon` from `@/design-system/icons` | direct port |
| `copy` | Custom SVG | `CopyIcon` from `@/design-system/icons` | direct port |
| `x` | Custom SVG | `XIcon` from `@/design-system/icons` | direct port |
| `menu` | Custom SVG | `MenuIcon` from `@/design-system/icons` | direct port |
| `sun` / `moon` | Custom SVG | `SunIcon`, `MoonIcon` from `@/design-system/icons` | direct port |

## Component Plan

### DsIcon (custom)

- **File:** `ui/src/design-system/icons/index.ts`
- **Type:** presentational
- **Props:**
    ```typescript
    export interface IconProps {
      class?: string
      title?: string
      ariaHidden?: boolean
    }
    ```
- **Styles:** icons use `currentColor`, fixed viewBox/paths from the mock, and no external icon library.
- **Library components used:** none
- **Key behaviors:** all icons render accessible SVG; decorative usages set `aria-hidden="true"`.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx:5-23`

### DsToolButton (custom)

- **File:** `ui/src/design-system/components/DsToolButton.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface DsToolButtonProps {
      label: string
      active?: boolean
      disabled?: boolean
      type?: 'button' | 'submit'
    }
    ```
- **Styles:** tokenized from `.tool`: `--tool-size`, `--tool-radius`, `--surface`, `--line-2`, `--text-2`, `--accent`, `--focus-ring`.
- **Library components used:** none
- **Key behaviors:** hover, focus-visible, disabled, active states; slot for icon.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:139-143`

### DsSegment (custom)

- **File:** `ui/src/design-system/components/DsSegment.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface SegmentOption {
      value: string
      label: string
      icon?: Component
      disabled?: boolean
    }

    interface DsSegmentProps {
      modelValue: string
      options: SegmentOption[]
      ariaLabel: string
    }
    ```
- **Styles:** tokenized from `.seg`: `--segment-radius`, `--segment-item-radius`, `--surface`, `--surface-2`, `--text-2`, `--accent`, `--shadow-sm`.
- **Library components used:** none
- **Key behaviors:** keyboard-operable roving buttons, active option styling, emits `update:modelValue`.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:130-137`

### DsMenu (custom)

- **File:** `ui/src/design-system/components/DsMenu.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface DsMenuItem {
      id: string
      label: string
      icon?: Component
      danger?: boolean
      separatorBefore?: boolean
    }

    interface DsMenuProps {
      open: boolean
      items: DsMenuItem[]
      labelledBy: string
    }
    ```
- **Styles:** tokenized from `.menu`: `--surface`, `--line-2`, `--menu-radius`, `--shadow-lg`, `--text`, `--danger`, `--danger-surface`.
- **Library components used:** none
- **Key behaviors:** click outside close handled by caller, Escape closes via emit, full keyboard access.
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css:255-261`

## Data Layer

This setup ticket does not touch the backend or data layer.

## Design Token Map

Full map: `docs/plans/kargha-parchmark-v2-header-plan/00-token-map.md`

The project's token/theme system is the **source of truth** for all design tokens. Do NOT copy the design's generated `tokens.css` into the app as a hand-maintained stylesheet. Copy/adopt the DTCG JSON sources into the V2 token source directory, generate CSS from those sources, and consume the generated variables through semantic/project tokens only.

| Design Token | Project Token (tier) | Usage |
| ------------------------ | --------------------------------- | ------------------------------------------ |
| `--canvas` / `#f6f4ef` | `semantic.color.canvas` (semantic) | app background |
| `--surface` / `#ffffff` | `semantic.color.surface` (semantic) | button/menu/panel surfaces |
| `--line-2` / `#e2ddd4` | `semantic.color.line-2` (semantic) | tool button and menu borders |
| `--shadow-sm` | `semantic.shadow.sm` (semantic) | active segment/tool elevation |
| `--shadow-lg` | `semantic.shadow.lg` (semantic) | menu and drawer elevation |

**Tokens with no consumable-tier match:** component-level shell/header literals listed in Token Changes.

## Token Changes

| Token (path → var) | Op | Value — base / dark | Source file(s) | Covers | Auth |
|-|-|-|-|-|-|
| `semantic.color.topbar-bg` → `--topbar-bg` | `add` | `rgba(246,244,239,.85)` / dark `rgba(27,25,23,.82)` | `semantic.json`, `semantic.dark.json` | topbar translucent backdrop | autonomous |
| `semantic.color.paper-grain` → `--paper-grain` | `add` | `rgba(88,12,36,.025)` / dark `rgba(255,255,255,.022)` | `semantic.json`, `semantic.dark.json` | app shell grain pattern | autonomous |
| `semantic.color.scrim` → `--scrim` | `add` | `rgba(43,40,37,.3)` / dark `rgba(0,0,0,.42)` | `semantic.json`, `semantic.dark.json` | mobile drawer scrim | autonomous |
| `semantic.color.focus-ring` → `--focus-ring` | `add` | `#F2E8EB` / dark `#3a2128` | `semantic.json`, `semantic.dark.json` | focus outlines | autonomous |
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
| `semantic.dimension.drawer-width` → `--drawer-width` | `add` | `300px` / dark same | `semantic.json` | mobile drawer width | autonomous |
| `semantic.breakpoint.sidebar-collapse` → `--sidebar-collapse` | `add` | `860px` / dark same | `semantic.json` | mobile shell breakpoint | autonomous |

### Foundation Setup Checklist

- [ ] Scaffold `ui/` as Vue 3 + TypeScript + Vite.
- [ ] Do not install Chakra or any Chakra peer dependencies.
- [ ] Add `style-dictionary` and a `build:tokens` script equivalent to the prototype's token build.
- [ ] Copy/adopt `primitives.json`, `semantic.json`, `semantic.dark.json`, and `build.mjs` into `ui/src/design-system/tokens/`.
- [ ] Emit generated CSS to `ui/src/design-system/tokens.css`; never hand-edit generated CSS.
- [ ] Load `tokens.css` and base design-system CSS at app bootstrap.
- [ ] Configure fonts: Playfair Display, Inter, JetBrains Mono.
- [ ] Implement DS icons and primitives above.
- [ ] Verify project tokens cover the design's color/spacing/radius/shadow needs.
- [ ] Add supplemental tokens ONLY for design values with no project equivalent. **DTCG:** edit the DTCG JSON in `ui/src/design-system/tokens/` and run `npm run build:tokens`; generated artifacts are read-only.

## Acceptance Criteria

- [ ] `ui/` exists as a Vue 3 + TypeScript + Vite app.
- [ ] No Chakra dependency or Chakra import exists in `ui/`.
- [ ] Generated token CSS resolves the base and `[data-theme="dark"]` values from the mock.
- [ ] DS icon components render exact SVG geometry from the mock.
- [ ] `DsToolButton`, `DsSegment`, and `DsMenu` match the mock dimensions and states using tokens.
- [ ] Components render matching design layout.
- [ ] Library components used wherever mapped (see Component-to-Library Map)
- [ ] Interactive states work (hover, active, focus, disabled)
- [ ] Accessible: semantic HTML, keyboard navigation, ARIA where needed
- [ ] Co-located test files exist with smoke tests
- [ ] `cd ui && npm run lint` passes
- [ ] `cd ui && npm run test` passes
- [ ] (DTCG token systems) Token-conformance passes: no primitive-tier variable consumption in new code, no hand-edits to generated token artifacts, no hardcoded values duplicating tokens

## Implementation Notes

- Follow the V2 stack decision in this ticket, not the current `ui/` React/Chakra implementation.
- Use custom Vue components only for the design system.
- All styling must reference project theme tokens — use project token variables/classes in custom styles. Never hardcode hex colors, px spacing, or px radii that duplicate project token values. For a tiered (DTCG) system, consume the **semantic tier only** — primitives are deny-listed for new code, and any needed-but-missing token is in this ticket's Token Changes section.
- Design uses inline styles — implementation must use Vue SFCs plus tokenized CSS.
- Design uses hardcoded mock data — later tickets use local mock fixtures.
- Design uses client-side `useState` navigation — implementation uses Vue state and Vue Router only when route-level navigation is needed.

## Files to Create

- `ui/package.json`
- `ui/index.html`
- `ui/vite.config.ts`
- `ui/tsconfig.json`
- `ui/src/main.ts`
- `ui/src/App.vue`
- `ui/src/design-system/tokens/primitives.json`
- `ui/src/design-system/tokens/semantic.json`
- `ui/src/design-system/tokens/semantic.dark.json`
- `ui/src/design-system/tokens/build.mjs`
- `ui/src/design-system/tokens.css`
- `ui/src/design-system/base.css`
- `ui/src/design-system/icons/index.ts`
- `ui/src/design-system/components/DsToolButton.vue`
- `ui/src/design-system/components/DsSegment.vue`
- `ui/src/design-system/components/DsMenu.vue`
- `ui/src/design-system/components/__tests__/DsToolButton.test.ts`
- `ui/src/design-system/components/__tests__/DsSegment.test.ts`
- `ui/src/design-system/components/__tests__/DsMenu.test.ts`

## Verification

```bash
cd ui && npm run build:tokens
cd ui && npm run lint
cd ui && npm run test
cd ui && npm run build
```
