// @vitest-environment node
/**
 * F17 — Static-grep oracle assertions.
 *
 * NOTE on `@vitest-environment node`: this file uses Node fs to verify
 * source-level deletion. Do NOT copy this pattern for behavioral tests —
 * use the default jsdom environment for anything that exercises React
 * component behavior. This is a deletion-shaped oracle, not a general
 * testing pattern.
 *
 * These tests FAIL until the implementer removes the For-You section and its
 * associated symbols from NotesExplorer.tsx and semanticTokens.ts.
 *
 * Oracle pointers (feature_pointer_base = /features/5):
 *   /features/5/oracle/assertions/0 — forYouNotes, getBlendedForYouNotes, trackNoteAccess absent from NotesExplorer.tsx
 *   /features/5/oracle/assertions/2 — forYou absent from semanticTokens.ts
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const repoRoot = path.resolve(__dirname, '../../../../../..');
const explorerFile = path.join(
  repoRoot,
  'ui/src/features/notes/components/NotesExplorer.tsx'
);
const semanticTokensFile = path.join(
  repoRoot,
  'ui/src/styles/foundations/semanticTokens.ts'
);
const explorerTestFile = path.join(
  repoRoot,
  'ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx'
);

describe('F17 deletion: NotesExplorer.tsx source assertions (/features/5/oracle/assertions/0)', () => {
  it('NotesExplorer.tsx contains no forYouNotes reference', () => {
    const src = fs.readFileSync(explorerFile, 'utf-8');
    expect(
      src,
      'forYouNotes must be removed from NotesExplorer.tsx — delete the forYouNotes memo and all references'
    ).not.toMatch(/forYouNotes/);
  });

  it('NotesExplorer.tsx contains no getBlendedForYouNotes reference', () => {
    const src = fs.readFileSync(explorerFile, 'utf-8');
    expect(
      src,
      'getBlendedForYouNotes must be removed from NotesExplorer.tsx — delete the import and all call sites'
    ).not.toMatch(/getBlendedForYouNotes/);
  });

  it('NotesExplorer.tsx contains no trackNoteAccess reference', () => {
    const src = fs.readFileSync(explorerFile, 'utf-8');
    expect(
      src,
      'trackNoteAccess must be removed from NotesExplorer.tsx — delete the import and call in handleSelect'
    ).not.toMatch(/trackNoteAccess/);
  });
});

describe('F17 deletion: semanticTokens.ts source assertions (/features/5/oracle/assertions/2)', () => {
  it('semanticTokens.ts contains no forYou token', () => {
    const src = fs.readFileSync(semanticTokensFile, 'utf-8');
    expect(
      src,
      '"forYou" semantic token must be removed from semanticTokens.ts — delete the section.forYou entry'
    ).not.toMatch(/forYou/);
  });
});

describe('F17 deletion: NotesExplorer.test.tsx test-file assertions', () => {
  it('NotesExplorer.test.tsx does not mock trackNoteAccess in vi.mock override', () => {
    const src = fs.readFileSync(explorerTestFile, 'utf-8');
    expect(
      src,
      'trackNoteAccess vi.mock override must be removed from the test file'
    ).not.toMatch(/trackNoteAccess.*vi\.fn/);
  });

  it('NotesExplorer.test.tsx does not assert on for-you-header presence', () => {
    const src = fs.readFileSync(explorerTestFile, 'utf-8');
    // Must not assert getByTestId('for-you-header') — only queryByTestId (absence checks) are allowed
    expect(
      src,
      'getByTestId("for-you-header") presence assertion must be removed — use queryByTestId for absence checks only'
    ).not.toMatch(/getByTestId\(['"]for-you-header['"]\)/);
  });
});
