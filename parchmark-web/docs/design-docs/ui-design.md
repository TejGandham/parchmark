# UI Design

ParchMark v2 frontend is a **Vue 3 + Vite** SFC app styled by a **DTCG design-token
system**. Token JSON under `ui/src/design-system/tokens/` is compiled by
Style Dictionary (`npm run build:tokens` → `node src/design-system/tokens/build.mjs`)
into the generated `ui/src/design-system/tokens.css`, which exposes short CSS
custom-property names (`--accent`, `--surface`, `--shadow-sm`, …) consumed by
component SFCs and `ui/src/design-system/base.css`. Edit the JSON sources, never
the generated `tokens.css`.

## 1. Design Principles

The visual language is "Parchment" — a warm, paper-like writing surface with a
burgundy brand accent, generous whitespace, and a serif display face for titles.

- **Paper, not panel** — warm off-white canvas, hairline borders, soft shadows; the
  app should read like a sheet of paper rather than a dense dashboard.
- **Burgundy as the single brand signal** — one saturated accent (`--accent`),
  used sparingly for actions, brand, and focus; everything else is warm neutral.
- **Quiet chrome, loud content** — translucent topbar, subtle grain, and muted tool
  buttons keep the markdown content the focus.

## 2. Color System

Two themes ship: **Parchment** (light, default) in `semantic.json` and **Desk lamp**
(dark) in `semantic.dark.json`. Both reference primitive ramps (`primitives.json`:
`burgundy.50–900`, warm `neutral.50–900`). Semantic tokens below emit the listed CSS
var via the `com.parchmark.cssName` extension.

| Token (CSS var) | Light | Dark | Usage |
|-|-|-|-|
| `--accent` | `#580c24` (burgundy.800) | `#8a1a38` | Brand, primary actions, links |
| `--accent-600` | `#742E45` (burgundy.600) | `#d28fa0` | Accent hover / secondary accent |
| `--canvas` | `#f6f4ef` | `#1b1917` | App background (parchment) |
| `--surface` | `#ffffff` | `#252220` | Cards, panels, editor |
| `--surface-2` | `#fbfaf7` | `#211e1c` | Subtle raised surface |
| `--text` | `#1A1816` (neutral.900) | `#f1ece4` | Primary text |
| `--text-2` | `#5F5851` (neutral.600) | `#bdb4a8` | Secondary text |
| `--muted` | `#7F7770` (neutral.500) | `#8f867b` | Muted / placeholder text |
| `--line` | `#ece8e1` | `#322e29` | Hairline borders |
| `--line-2` | `#e2ddd4` | `#3b362f` | Stronger borders |
| `--danger` | `#b3261e` | `#f08a80` | Destructive action foreground |
| `--danger-surface` | `#fdecea` | `#3a1f1d` | Destructive hover surface |
| `--focus-ring` | `#F2E8EB` | `#3a2128` | Focus outline / selection |
| `--topbar-bg` | `rgba(246,244,239,.85)` | `rgba(27,25,23,.82)` | Translucent topbar backdrop |
| `--scrim` | `rgba(43,40,37,.3)` | `rgba(0,0,0,.42)` | Mobile drawer scrim |

> Transitional debt: the dark theme re-points a few **primitives** (`--p50…p300`,
> `--n100…n400`, `--n800/900`) because some component CSS still consumes primitive
> vars directly. Canonical tiering forbids this; migrate that CSS to semantic tokens
> and delete the dark primitive overrides.

## 3. Typography

Font families are primitives (`primitives.json` → `--serif`, `--sans`, `--mono`);
the Google Fonts import lives at the top of `base.css`.

- **Body:** `--sans` = `Inter, system-ui, sans-serif` (weights 400/500/600/700)
- **Headings / brand:** `--serif` = `Playfair Display, Georgia, serif` (display weights 500–800)
- **Monospace:** `--mono` = `JetBrains Mono, ui-monospace, Menlo, monospace` — for code fences and inline code in rendered markdown

`base.css` sets `font-feature-settings: "kern","liga"`, `text-rendering: optimizeLegibility`,
and antialiasing on `body`.

## 4. Spacing

Spacing is expressed via component-scoped dimension tokens rather than a single
global scale. Key values from `semantic.json` (`dimension` group):

- Base corner radius: `--r` = `12px` (`primitives.json` → `radius.base`)
- Topbar padding: `--topbar-padding-x` `28px` / `--topbar-padding-y` `12px`; `--topbar-gap` `14px`
- Sidebar width: `--sidebar-width` `312px` (`layout.sidebar-width`); mobile `--drawer-width` `300px`
- Tool button: `--tool-size` `34px`, `--tool-radius` `9px`

## 5. Components

The design system ships three generic, headless-ish SFC primitives in
`ui/src/design-system/components/`. Each owns its tokens and full keyboard a11y;
none pull from an external component library.

| Component | Role / a11y | Props | Used by |
|-|-|-|-|
| `DsToolButton.vue` | Square icon button; `aria-pressed` when `active` | `label`, `active?`, `disabled?`, `type?` | `AppTopbar`, `OverflowNoteMenu`, `ThemeToggleButton` |
| `DsMenu.vue` | `role="menu"` popover; arrow/Home/End/Escape nav, auto-focuses first item, danger items, separators | `open`, `items`, `labelledBy` | `OverflowNoteMenu` |
| `DsSegment.vue` | Generic `role="radiogroup"` segmented control; roving tabindex | `modelValue`, `options`, `ariaLabel` | **none** (only its own test) |

> `DsSegment.vue` is a reusable radiogroup control that is **not wired into the
> app**. The topbar's read/edit switch is the bespoke `ReadEditSegment.vue` in
> `features/shell/` — a single toggle button (Eye/Edit icon) that flips a `mode`
> prop between `"read"` and `"edit"`, styled to match `--segment-*` tokens. Do not
> conflate the two.

### Tokens for the shell chrome and Ds* primitives

### Tool button (`DsToolButton`)
- `--tool-size`: `34px`
- `--tool-radius`: `9px`
- Hover border: `--tool-hover-border` (burgundy.300)

### Segment (`DsSegment`)
- `--segment-radius`: `9px`
- `--segment-item-radius`: `7px`

`DsSegment.vue` is a **generic, reusable segmented control** — `role="radiogroup"`
of `role="radio"` buttons driven by `options` / `modelValue` props, with full
arrow/Home/End roving-tabindex keyboard support. It is **not imported anywhere in
the app**; only its own test (`__tests__/DsSegment.test.ts`) references it. The real
read/edit control in the topbar is `ReadEditSegment.vue` (see Components below), a
purpose-built single toggle button — not this component.

### Menu (`DsMenu`, overflow menus)
- `--menu-radius`: `12px`
- Item hover surface: `--menu-hover-surface` (neutral.100)

### Shadows
- `--shadow-sm`: layered 1px soft shadow (cards) — `0 1px 2px 0 rgba(43,40,37,.06), 0 1px 1px 0 rgba(43,40,37,.04)`
- `--shadow`: `0 6px 24px -10px rgba(43,40,37,.20)` — default elevation (DTCG `shadow.md`; legacy CSS name is plain `--shadow`)
- `--shadow-lg`: `0 24px 60px -24px rgba(43,40,37,.32)` — popovers/drawer

## 6. Icons

There is **no icon library**. Icons are hand-authored SVGs built by a small factory,
`createIcon()`, in `ui/src/design-system/icons/index.ts`. Each call defines a named
Vue component (24×24 `viewBox`, currentColor stroke/fill, `focusable="false"`) with
shared `strokeRound` / `strokeRoundJoin` attribute presets. Icons accept `class`,
`title`, and `ariaHidden`: when a `title` is set and not hidden, a `<title>` element
and `role="img"` are emitted; otherwise `aria-hidden="true"`.

There are **18 exported icons**: `PlusIcon`, `SearchIcon`, `GearIcon`, `MoreIcon`,
`EditIcon`, `EyeIcon`, `TrashIcon`, `DownloadIcon`, `CopyIcon`, `XIcon`, `MenuIcon`,
`SunIcon`, `MoonIcon`, `EyeOffIcon`, `AlertIcon`, `FeatherIcon`, `LockIcon`,
`LogOutIcon`. Intrinsic render sizes vary per icon (14–18px).

## 7. Motion

No animation library; motion is plain CSS `transition`. Durations are short and
consistent, in the **0.1s–0.25s** range with `ease` timing:

- Body theme cross-fade (`base.css`): `0.25s` on `background-color` / `color`.
- Menu item hover (`DsMenu`): `0.12s`.
- Tool button (`DsToolButton`): `0.14s` on border/shadow/color/transform; `:active`
  nudges `translateY(1px)`.
- Segment / read-edit switch hover and focus: `0.15s`.
- Sidebar drawer slide (`SidebarDrawer`): `0.22s`.

Focus is shown with a 3px `--focus-ring` box-shadow ring (with `:focus-visible`),
not an outline.

## 8. Theme

- **Default:** light (Parchment). Persisted choice read from `localStorage["pm_theme"]` on load.
- **Toggle:** `ThemeToggleButton.vue` in the topbar; `AppShell.vue` holds a local
  `theme` ref (`"light" | "dark"`) and `toggleTheme()` flips it.
- **CSS strategy:** `data-theme` attribute on `<html>`. An `AppShell` watcher writes
  `document.documentElement.dataset.theme = value` (and persists to `localStorage`).
  Generated `tokens.css` emits light values under `:root` and dark overrides under
  `[data-theme="dark"]`.

## 9. Responsive

There is no responsive CSS framework; layout is plain flex/grid in SFCs with a single
shell breakpoint.

- **Breakpoint:** the `--sidebar-collapse` token is `860px`. The actual media queries
  in `AppShell.vue`, `AppTopbar.vue`, and `SidebarDrawer.vue` are written as
  `@media (max-width: 53.75em)` (= 860px at a 16px root). At/below this the desktop
  sidebar collapses into a mobile drawer (`SidebarDrawer.vue`, toggled by the
  `navOpen` ref in `AppShell.vue`).
- **Desktop:** persistent sidebar (`--sidebar-width` `312px`) beside the read/edit pane.
- **Mobile:** off-canvas drawer (`--drawer-width` `300px`) over a `--scrim` backdrop.
- **Layout:** CSS flex/grid within SFCs (no grid library).
