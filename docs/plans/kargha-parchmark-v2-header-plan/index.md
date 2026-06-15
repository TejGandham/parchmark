# ParchMark V2 Header Kargha Plan

Output mode: plain Markdown files.

Design file: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
Screenshots: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/screenshots/`
Target frontend app: `ui/`
Target stack: Vue 3 + TypeScript + Vite + custom design system.

Explicit constraints:
- Do not use Chakra.
- Do not inherit React or Chakra decisions from the current `ui/` app.
- Use the provided mock and token sources as the V2 design system source.
- New component CSS consumes semantic/project tokens only, never primitive ramp variables.

## Ticket Order

| Order | ID | Title | Depends on | Estimate |
| --- | --- | --- | --- | --- |
| 00 | `00-token-map` | Full design token map | none | reference |
| 01 | `01-v2-custom-design-system-and-tokens` | Establish Vue V2 custom design system and tokens | none | M |
| 02 | `02-foundational-app-shell-with-mock-notes` | Implement foundational app shell with mock notes | `01-v2-custom-design-system-and-tokens` | M |
| 03 | `03-header-topbar-with-mock-note-state` | Implement header topbar with mock note state | `01-v2-custom-design-system-and-tokens`, `02-foundational-app-shell-with-mock-notes` | M |

## Dependency Chain

`01-v2-custom-design-system-and-tokens` → `02-foundational-app-shell-with-mock-notes` → `03-header-topbar-with-mock-note-state`

## Coverage

- Component library coverage: 0 library components, all in-scope UI is custom design-system work.
- Icon coverage: custom SVG source for all 12 in-scope icons from the mock.
- Token coverage: direct semantic matches for base color, typography, surface, line, shadow, radius, and sidebar-width tokens; additive semantic/component tokens proposed for header/shell raw literals.
- Data coverage: local mock notes only, based on the prototype's `SEED` shape. Backend work is not included in this slice.

