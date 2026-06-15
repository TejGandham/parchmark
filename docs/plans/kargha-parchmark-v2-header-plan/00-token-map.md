# ParchMark V2 Token Map

Design source:
- `/mnt/agent-storage/vader/src/parchmark-ux-redesign/tokens/primitives.json`
- `/mnt/agent-storage/vader/src/parchmark-ux-redesign/tokens/semantic.json`
- `/mnt/agent-storage/vader/src/parchmark-ux-redesign/tokens/semantic.dark.json`
- Generated reference: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/tokens.css`

Project token system decision:
- V2 adopts this DTCG token system as the project token source.
- Editable source directory in the target app: `ui/src/design-system/tokens/`
- Generated artifact in the target app: `ui/src/design-system/tokens.css`
- Build command in the target app: `npm run build:tokens`
- Theme context selector: `[data-theme="dark"]`
- Name-resolution rule: `$extensions["com.parchmark.cssName"]` where present; otherwise path-derived CSS variable names.
- Consumption rule: component CSS consumes semantic/project tokens only. Do not consume primitive ramp variables (`--p*`, `--n*`) in new component CSS.

## Direct Token Matches

| Design Token | Project Token (tier) | Value | Dark Value | Usage |
| --- | --- | --- | --- | --- |
| `--canvas` | `semantic.color.canvas` (semantic) | `#f6f4ef` | `#1b1917` | app background |
| `--surface` | `semantic.color.surface` (semantic) | `#ffffff` | `#252220` | panels, buttons, menu |
| `--surface-2` | `semantic.color.surface-2` (semantic) | `#fbfaf7` | `#211e1c` | sidebar, raised subtle surfaces |
| `--line` | `semantic.color.line` (semantic) | `#ece8e1` | `#322e29` | topbar border, separators |
| `--line-2` | `semantic.color.line-2` (semantic) | `#e2ddd4` | `#3b362f` | stronger borders |
| `--accent` | `semantic.color.accent` (semantic) | `#580c24` | `#8a1a38` | primary burgundy text/fill |
| `--accent-600` | `semantic.color.accent-600` (semantic) | `#742E45` | `#d28fa0` | quiet accent text |
| `--text` | `semantic.color.text` (semantic) | `#1A1816` | `#f1ece4` | primary text |
| `--text-2` | `semantic.color.text-2` (semantic) | `#5F5851` | `#bdb4a8` | secondary text |
| `--muted` | `semantic.color.muted` (semantic) | `#7F7770` | `#8f867b` | muted labels/breadcrumb |
| `--shadow-sm` | `semantic.shadow.sm` (semantic) | `0 1px 2px ...` | `0 1px 2px ...` | active segment, note cards |
| `--shadow` | `semantic.shadow.md` (semantic) | `0 6px 24px -10px ...` | `0 8px 28px -12px ...` | medium elevation |
| `--shadow-lg` | `semantic.shadow.lg` (semantic) | `0 24px 60px -24px ...` | `0 28px 70px -28px ...` | drawer/menu elevation |
| `--serif` | `font.family.serif` (primitive allowed through DS font token export) | `Playfair Display, Georgia, serif` | same | wordmark |
| `--sans` | `font.family.sans` (primitive allowed through DS font token export) | `Inter, system-ui, sans-serif` | same | app body |
| `--mono` | `font.family.mono` (primitive allowed through DS font token export) | `JetBrains Mono, ui-monospace, Menlo, monospace` | same | future editor/code |
| `--r` | `radius.base` (primitive wrapped by DS radius token) | `12px` | same | baseline radius reference |
| `--sidebar-w` | `layout.sidebar-width` (primitive wrapped by DS layout token) | `312px` | same | desktop app shell |

## Component Token Additions

These are additive semantic/project tokens for values the mock currently expresses as raw CSS literals. Add them before building the header and shell so implementation does not hardcode those literals in component CSS.

| Token (path → var) | Op | Value — base / dark | Source file(s) | Covers | Auth |
| --- | --- | --- | --- | --- | --- |
| `semantic.color.topbar-bg` → `--topbar-bg` | `add` | `rgba(246,244,239,.85)` / `rgba(27,25,23,.82)` | `semantic.json`, `semantic.dark.json` | topbar translucent backdrop | autonomous |
| `semantic.color.paper-grain` → `--paper-grain` | `add` | `rgba(88,12,36,.025)` / `rgba(255,255,255,.022)` | `semantic.json`, `semantic.dark.json` | app shell grain pattern | autonomous |
| `semantic.color.scrim` → `--scrim` | `add` | `rgba(43,40,37,.3)` / `rgba(0,0,0,.42)` | `semantic.json`, `semantic.dark.json` | mobile drawer scrim | autonomous |
| `semantic.color.focus-ring` → `--focus-ring` | `add` | `#F2E8EB` / `#3a2128` | `semantic.json`, `semantic.dark.json` | focus outlines matching mock burgundy tint | autonomous |
| `semantic.color.danger` → `--danger` | `add` | `#b3261e` / `#f08a80` | `semantic.json`, `semantic.dark.json` | overflow delete action | autonomous |
| `semantic.color.danger-surface` → `--danger-surface` | `add` | `#fdecea` / `#3a1f1d` | `semantic.json`, `semantic.dark.json` | danger hover background | autonomous |
| `semantic.dimension.topbar-padding-x` → `--topbar-padding-x` | `add` | `28px` / same | `semantic.json` | desktop topbar horizontal padding | autonomous |
| `semantic.dimension.topbar-padding-y` → `--topbar-padding-y` | `add` | `12px` / same | `semantic.json` | desktop topbar vertical padding | autonomous |
| `semantic.dimension.topbar-gap` → `--topbar-gap` | `add` | `14px` / same | `semantic.json` | topbar flex gap | autonomous |
| `semantic.dimension.tool-size` → `--tool-size` | `add` | `34px` / same | `semantic.json` | square icon buttons | autonomous |
| `semantic.dimension.tool-radius` → `--tool-radius` | `add` | `9px` / same | `semantic.json` | icon button radius | autonomous |
| `semantic.dimension.segment-radius` → `--segment-radius` | `add` | `9px` / same | `semantic.json` | read/edit segment container | autonomous |
| `semantic.dimension.segment-item-radius` → `--segment-item-radius` | `add` | `7px` / same | `semantic.json` | read/edit segment buttons | autonomous |
| `semantic.dimension.menu-radius` → `--menu-radius` | `add` | `12px` / same | `semantic.json` | overflow menu radius | autonomous |
| `semantic.dimension.drawer-width` → `--drawer-width` | `add` | `300px` / same | `semantic.json` | mobile drawer width | autonomous |
| `semantic.breakpoint.sidebar-collapse` → `--sidebar-collapse` | `add` | `860px` / same | `semantic.json` | mobile shell breakpoint | autonomous |

## Prototype Primitive Debt To Avoid

The prototype CSS still uses primitive ramp variables like `--p300` and `--n100` in component rules. V2 should replace those usages with semantic/project tokens or the component token additions above. Do not copy primitive usages into V2 component CSS.

