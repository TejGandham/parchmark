# ParchMark V2 Read Notes Kargha Plan

Output mode: plain Markdown files.

Design file: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
Target frontend app: `ui/`
Target stack: Vue 3 + TypeScript + Vite + custom design system.

Explicit constraints:
- Keep artifacts in the repository under `docs/` as tracked repo artifacts.
- Use the V2 integration branch `feat/parchmark-v2` as the planning target.
- New code must use project semantic/component tokens; do not consume primitive ramp variables in new CSS.
- Read mode renders markdown; edit mode remains out of scope for this slice.

## Ticket Order

| Order | ID | Title | Depends on | Estimate |
| --- | --- | --- | --- | --- |
| 00 | `00-token-map` | Read Notes design token map | none | reference |
| 01 | `01-render-markdown-read-pane` | Render markdown in the V2 read pane | none | M |

## Dependency Chain

`01-render-markdown-read-pane`

## Coverage

- Component library coverage: no external component library use; `MarkdownProse` is custom and composes existing V2 shell/read-pane markup.
- Icon coverage: no icons in scope.
- Token coverage: all Read Notes prose styling maps to existing semantic/component tokens; no token additions proposed.
- Data coverage: local mock notes only, using the existing `NoteMock` shape and helper functions.
