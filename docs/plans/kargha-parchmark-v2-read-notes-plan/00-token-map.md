# Read Notes Design Token Map

The project's token/theme system is the source of truth. The design prototype's prose CSS is the intended visual target, but implementation must consume the project tokens emitted from `ui/src/design-system/tokens/*.json`.

## Project Token System

- Source files: `ui/src/design-system/tokens/primitives.json`, `ui/src/design-system/tokens/semantic.json`, `ui/src/design-system/tokens/semantic.dark.json`
- Generated artifact: `ui/src/design-system/tokens.css`
- Build command: `cd ui && npm run build:tokens`
- Consumable tier for new CSS: semantic/component variables from `tokens.css`
- Primitive ramp variables such as `--p300` and `--n800` are transitional debt and must not be consumed by new Read Notes CSS.

## Read Notes Token Subset

| Design Token / Literal | Project Token (tier) | Usage |
| --- | --- | --- |
| Prose body text `#2B2825` / dark equivalent | `--text` or `--text-2` (semantic) | Markdown paragraph text; choose `--text-2` only for secondary prose surfaces such as blockquotes |
| Heading text | `--text` (semantic) | Markdown `h2`, `h3`, `h4` |
| Serif heading family | `--serif` (primitive font family emitted for global typography) | Markdown headings |
| Accent burgundy | `--accent` (semantic) | Links, list markers where needed, inline code foreground if used |
| Subtle accent surface | `--focus-ring` or `--surface-2` (semantic) | Inline code background; prefer `--surface-2` unless the final visual needs a warmer accent wash |
| Hairline divider | `--line` / `--line-2` (semantic) | Markdown heading underline, table borders, horizontal rules |
| Raised/sunken prose surface | `--surface-2` (semantic) | Tables, code blocks, mermaid fallback surfaces |
| Code/pre shadow | `--shadow-sm` (semantic shadow) | Code block elevation if used |
| Radius `12px` | `--menu-radius` or `--r` (component/primitive radius) | Code block and table wrapper radius; prefer existing component radius variable that matches local context |
| Monospace family | `--mono` (primitive font family emitted for global typography) | Inline code and code blocks |
| Danger/destructive colors | not in scope | Read Notes has no destructive UI |

## Tokens With No Consumable-Tier Match

None. Do not add tokens for this slice unless design validation proves a critical/major mismatch that cannot be expressed with existing semantic/component tokens.

