---
id: 01-render-markdown-read-pane
title: Render markdown in the V2 read pane
type: task
parent: kargha-parchmark-v2-read-notes-plan
depends_on: []
estimate: M
---

## Context

Implement the Read Notes slice from the V2 mock: the selected note's body should render as structured markdown instead of a flattened preview paragraph. This keeps the existing V2 shell, selected-note metadata, and tag interactions while making the user's writing the primary interface.

**Parent / group:** `kargha-parchmark-v2-read-notes-plan`
**Depends on:** none

## Design Reference

- **Design file:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- **View:** `read-note` — initial app view with `Morning Pages` selected
- **Components in scope:** `ReadView`, `renderMarkdown`, `.prose`, `MarkdownProse`, read-pane body integration

## Component-to-Library Map

| Design Component | Library Mapping | Notes |
| --- | --- | --- |
| `ReadView` | **Custom** — existing `AppShell` read-pane section + new `MarkdownProse` | Domain-specific reader layout |
| `renderMarkdown` | **Custom utility** — use proven markdown renderer + sanitizer | Prefer `marked` to match prototype behavior; sanitize before `v-html` |
| `.prose` markdown styles | **Custom** — co-located Vue component styles using project tokens | Maps prototype prose rules onto V2 token system |
| Metadata row | Existing custom markup in `AppShell.vue` | Preserve title, reading time, word count, edited time, and tags |
| Tag chips | Existing `.mini-tag-button` buttons | Preserve click-to-filter behavior |

## Component Plan

### MarkdownProse (custom)

- **File:** `ui/src/features/notes/MarkdownProse.vue`
- **Type:** presentational
- **Props:**
    ```typescript
    interface MarkdownProseProps {
      markdown: string;
    }
    ```
- **Styles:** scoped `.prose` styles mapped from the prototype's rendered markdown CSS, using project tokens from `ui/src/design-system/tokens.css`
- **Library components used:** none
- **Key behaviors:** renders title-stripped markdown as safe HTML; preserves headings, paragraphs, emphasis, lists, blockquotes, tables, code, horizontal rules, and task-list checkboxes
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx` `ReadView` and `renderMarkdown`; `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/styles.css` `.prose`

### markdownRender (custom)

- **File:** `ui/src/features/notes/markdownRender.ts`
- **Type:** presentational utility
- **Props:**
    ```typescript
    export function renderMarkdownBody(markdown: string): string;
    ```
- **Styles:** none
- **Library components used:** none
- **Key behaviors:** calls existing `stripTitle(markdown)`, parses markdown with a proven renderer, sanitizes the generated HTML, and returns safe HTML for `MarkdownProse`
- **Design reference:** `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/components.jsx` `renderMarkdown`

## Route / Layout

- **Route:** existing V2 app root route rendered by `ui/src/App.vue`
- **Served URL:** `/`
- **Layout changes:** replace `<p class="note-body">{{ bodyPreview }}</p>` with `<MarkdownProse :markdown="activeNote.content" />`; keep existing `.measure`, title, metadata, rule, and tag chip layout
- **Navigation:** app loads with `Morning Pages` selected; selecting notes in the sidebar should update the rendered markdown body

## Data Layer

- **Operation:** local mock data only, from `ui/src/features/notes/mockNotes.ts`
- **Fetch policy / caching:** none
- **Schema gaps:** none for this slice
- **Mock handlers:** none

## Design Token Map

Full map: `docs/plans/kargha-parchmark-v2-read-notes-plan/00-token-map.md`

The project's token/theme system is the **source of truth** for all design tokens. Do NOT copy the design's tokens stylesheet into the app; use project tokens via CSS variables.

| Design Token | Project Token (tier) | Usage |
| --- | --- | --- |
| Prose heading color | `--text` (semantic) | Markdown headings |
| Prose body color | `--text` / `--text-2` (semantic) | Paragraphs and secondary text |
| Divider and table lines | `--line` / `--line-2` (semantic) | Heading underlines, tables, horizontal rules |
| Accent/list/link color | `--accent` (semantic) | Links and optional list marker color |
| Subtle surfaces | `--surface-2` (semantic) | Inline code, tables, code/diagram surfaces |
| Serif heading family | `--serif` | Markdown headings |
| Monospace family | `--mono` | Inline code and code blocks |

**Tokens with no consumable-tier match:** none.

## Acceptance Criteria

- [ ] `Morning Pages` read view renders `What it's for` and `Today` as headings below the document title.
- [ ] The rendered body does not duplicate the first H1 title.
- [ ] The Morning Pages blockquote renders as a `blockquote`, not a flattened paragraph.
- [ ] The Morning Pages bullet rules render as list items.
- [ ] `Reading list` renders its markdown table as a table with `Title`, `Author`, and `Why` header cells.
- [ ] `Standup notes` renders task-list markdown as disabled checkboxes with checked state preserved for `[x]`.
- [ ] Sanitizer coverage proves script/event-handler HTML does not survive rendering.
- [ ] Existing note search, tag filtering, note selection, title extraction, word count, and reading time behavior remains green.
- [ ] Co-located tests cover the renderer utility and rendered component.
- [ ] `cd ui && npm run lint` passes
- [ ] `cd ui && npm run test` passes
- [ ] Design validation passes with zero critical and zero major discrepancies for read-pane content structure.

## Implementation Notes

- Follow `docs/design-docs/design-context.md`: content is king, speed over spectacle, reduce don't add.
- Use `marked` or an equivalent proven markdown renderer; do not hand-roll markdown parsing.
- Use `dompurify` or an equivalent sanitizer before using Vue `v-html`.
- Preserve existing helpers in `ui/src/features/notes/noteMockHelpers.ts`; use `stripTitle()` instead of reimplementing first-H1 removal.
- Keep Read Notes independent of edit-mode work and backend persistence.
- All styling must reference project theme tokens; avoid prototype primitive variables such as `--p300` and `--n800` in new code.

## Files to Create

- `ui/src/features/notes/MarkdownProse.vue`
- `ui/src/features/notes/markdownRender.ts`
- `ui/src/features/notes/__tests__/MarkdownProse.test.ts`
- `ui/src/features/notes/__tests__/markdownRender.test.ts`

## Files to Modify

- `ui/package.json`
- `ui/package-lock.json`
- `ui/src/features/shell/AppShell.vue`
- `ui/src/features/shell/__tests__/AppShell.test.ts`
- `ui/src/App.test.ts`

## Verification

```bash
cd ui && npm run lint
cd ui && npm run test
cd ui && npm run build
```

### Design Validation Loop (if available)

If the environment provides a design-validation tool/skill, run it to compare the running app against the design prototype. Treat it as a required loop, up to 3 rounds. Each round fixes `critical` then `major` discrepancies; the exit bar is zero critical and zero major.

1. **Round 1:** Validate with the design file, app route, and navigation. Fix critical, then major, discrepancies.
2. **Round 2:** Re-validate after fixes. Fix any remaining critical/major.
3. **Round 3:** Final pass. Exit when zero critical and zero major remain; document any minor/cosmetic residuals as follow-up.

**Validation parameters for this ticket:**

- Design file: `/mnt/agent-storage/vader/src/parchmark-ux-redesign/prototype/ParchMark.html`
- App route: `/`
- Design navigation: initial read view with `Morning Pages` selected; for table/task-list checks select `Reading list` and `Standup notes` from the sidebar
- App navigation: initial read view with `Morning Pages` selected; for table/task-list checks select `Reading list` and `Standup notes` from the sidebar
- Viewport: `1440x900`
- Theme context(s): `base + dark (smoke)`
- Focus areas: read-pane content structure, markdown prose typography, absence of raw markdown markers in rendered body
