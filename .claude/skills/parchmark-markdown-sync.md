---
name: parchmark-markdown-sync
description: Verify the frontend (markdownRender.ts / noteMockHelpers.ts) and backend (markdown.py) markdown title/strip semantics stay in sync
---

# ParchMark Markdown Sync

Use this skill after changing markdown title/strip logic in either the frontend (`ui/src/features/notes/noteMockHelpers.ts` or `ui/src/features/notes/markdownRender.ts`) or the backend (`backend/app/utils/markdown.py`). It verifies the shared title-extraction and first-H1-strip semantics stay equivalent.

> **v2 caveat — read first.** The v2 Vue frontend currently renders **mock** notes (`ui/src/features/notes/mockNotes.ts`) and is not yet wired to backend-served notes, so FE/BE markdown parity is **forward-looking**, not a live runtime coupling — it matters once the notes API is wired. The backend `markdown.py` docstring still says it "mirrors the frontend markdown service" (historical intent), and the two sides have already drifted slightly (e.g. the default title: FE `extractTitle` returns `"Untitled"`, BE `extract_title` returns `"Untitled Note"`).

## Files

- **Frontend — title/strip helpers:** `ui/src/features/notes/noteMockHelpers.ts` — `extractTitle()`, `stripTitle()`, `plainPreview()`
- **Frontend — renderer (FE-only):** `ui/src/features/notes/markdownRender.ts` — `renderMarkdownBody()` (marked + DOMPurify; strips the title via `stripTitle`, rewrites ` ```mermaid ` fences to `<div class="mermaid">`)
- **Backend:** `backend/app/utils/markdown.py` — `MarkdownService` (singleton `markdown_service`)

The old React-era `ui/src/utils/markdown.ts` and `ui/src/services/markdownService.ts` no longer exist.

## Steps

### 1. List the functions

```bash
# Frontend helpers
grep -nE 'export function \w+' ui/src/features/notes/noteMockHelpers.ts ui/src/features/notes/markdownRender.ts
# Backend methods (MarkdownService)
grep -nE '    def [a-z]' backend/app/utils/markdown.py
```

### 2. Compare the inventory

| Concern | Frontend | Backend |
|-|-|-|
| Extract title (first H1) | `extractTitle` (noteMockHelpers.ts) | `extract_title` |
| Strip the first H1 | `stripTitle` (noteMockHelpers.ts) | `remove_h1` |
| Render to HTML | `renderMarkdownBody` (markdownRender.ts) | — (FE-only) |
| Preview text | `plainPreview` (noteMockHelpers.ts) | — (FE-only) |
| Normalize content | — | `format_content` (BE-only) |
| Empty-note template | — | `create_empty_note` (BE-only) |

The shared pair to keep in sync is **title extraction** and **first-H1 strip**. Rendering, preview, formatting, and templates are intentionally one-sided.

### 3. Compare semantics of the shared pair

| Function | Frontend | Backend |
|-|-|-|
| extract title | `/^\s*#\s+(.+?)\s*$/m`, default `"Untitled"` | `^#\s+(.+)$` (MULTILINE), default `"Untitled Note"` |
| strip first H1 | `/^\s*#\s+.+?(\r?\n\|$)/` then trim leading ws | `^#\s+(.+)($\|\n)`, `count=1`, then `.strip()` |

Invariants both must hold:
- **Strip only the FIRST H1**, not all H1s.
- **"Title" = the first `# ` heading.**

Read both implementations and confirm equivalent behavior for: empty input, no H1, leading whitespace before `#`, multiple H1s, and the default-title string.

### 4. Report

**In sync:**
> Title/strip semantics match between `noteMockHelpers.ts` and `markdown.py`.

**Drift:**
```
DRIFT DETECTED:
1. Default title differs: extractTitle -> "Untitled" vs extract_title -> "Untitled Note"
2. extractTitle allows leading whitespace before '#' (^\s*#); extract_title does not (^#)
   Recommendation: [pick the canonical behavior, or flag for human decision]
```

### 5. Suggest fixes

- If one side matches the intended behavior, recommend updating the other.
- If unclear, flag for human decision with both implementations shown.
- One-sided helpers (render / preview / format / template) are acceptable asymmetry — do not flag.

## Failure Modes

| Situation | Action |
|-|-|
| A shared function exists on one side only | Flag as drift |
| Different regex, same behavior | Note as potential drift; verify the edge cases above |
| One-sided helper (render/preview/format/template) | Acceptable asymmetry — do not flag |
| Frontend file not found at the path above | The FE markdown moved during the v2 rewrite; re-locate under `ui/src/features/notes/` |
