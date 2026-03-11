---
name: parchmark-markdown-sync
description: Verify frontend (markdown.ts) and backend (markdown.py) markdown utils stay in sync
---

# ParchMark Markdown Sync

Use this skill after modifying any markdown processing logic in either `ui/src/utils/markdown.ts` or `backend/app/utils/markdown.py` — verifies both implementations stay in sync.

## Files

- **Frontend (core):** `ui/src/utils/markdown.ts` (MarkdownService class)
- **Frontend (wrapper):** `ui/src/services/markdownService.ts` (re-exports convenience functions)
- **Backend:** `backend/app/utils/markdown.py` (MarkdownService class)

## Steps

### 1. Extract function signatures

Read both files and list all public/exported functions:

**TypeScript** — look for `export function` or exported arrow functions:
```
grep -E 'export (function|const) \w+' ui/src/utils/markdown.ts
```

**Python** — look for top-level `def` (not prefixed with `_`):
```
grep -E '^def [^_]\w+' backend/app/utils/markdown.py
```

### 2. Compare function inventory

Map function names between languages (accounting for naming conventions):

| TypeScript (camelCase) | Python (snake_case) |
|-|-|
| `extractTitle` | `extract_title` |
| `removeH1` | `remove_h1` |
| ... | ... |

Flag any function that exists in one file but not the other.

### 3. Compare behavioral semantics

For each shared function pair, compare:

- **Regex patterns** — are they equivalent?
- **Edge case handling** — same behavior for empty input, no match, multiple matches?
- **Key invariants:**
  - `removeH1` / `remove_h1` — removes FIRST H1 only (not all)
  - `extractTitle` / `extract_title` — same regex for matching H1

Read both implementations side-by-side and verify logical equivalence.

### 4. Report

**If no drift found:**
> Markdown utils are in sync. Both files have matching function inventory and equivalent behavior.

**If drift found**, report each mismatch:

```
DRIFT DETECTED:

1. Missing function:
   - `formatPreview` exists in markdown.ts:42 but has no equivalent in markdown.py

2. Logic divergence:
   - extractTitle (markdown.ts:15): uses /^#\s+(.+)$/m
   - extract_title (markdown.py:8): uses r'^#\s+(.+)'
   - Difference: TypeScript uses multiline flag, Python does not
   - Recommendation: [which is correct, or flag for human decision]
```

### 5. Suggest fixes

For each drift item:
- If one side is clearly correct (e.g., matches documented behavior), recommend updating the other
- If unclear, flag for human decision with both implementations shown
- If a function is intentionally one-side-only (e.g., frontend-specific rendering), note it as acceptable asymmetry

## Failure Modes

| Situation | Action |
|-|-|
| New function in one file only | Flag as drift — may be intentional, ask user |
| Different regex with same behavior | Note as potential drift, verify edge cases |
| No drift found | Report "in sync" and exit |
| File not found | Error — these are core files, something is wrong |
