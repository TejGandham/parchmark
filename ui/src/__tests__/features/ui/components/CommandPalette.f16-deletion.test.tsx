// @vitest-environment node
/**
 * F16 — Static-grep oracle assertions.
 *
 * NOTE on `@vitest-environment node`: this file uses Node fs to verify
 * source-level deletion. Do NOT copy this pattern for behavioral tests —
 * use the default jsdom environment for anything that exercises React
 * component behavior. This is a deletion-shaped oracle, not a general
 * testing pattern.
 *
 * These tests FAIL until the implementer removes the For-You section and its
 * associated symbols from CommandPalette.tsx and CommandPalette.test.tsx.
 *
 * Oracle pointers (feature_pointer_base = /features/4):
 *   /features/4/oracle/assertions/0 — "For You" absent from CommandPalette.tsx
 *   /features/4/oracle/assertions/1 — symbols absent from CommandPalette.tsx
 *   /features/4/oracle/assertions/2 — deleted tests absent from CommandPalette.test.tsx
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const repoRoot = path.resolve(__dirname, '../../../../../..');
const srcFile = path.join(
  repoRoot,
  'ui/src/features/ui/components/CommandPalette.tsx'
);
const testFile = path.join(
  repoRoot,
  'ui/src/__tests__/features/ui/components/CommandPalette.test.tsx'
);

describe('F16 deletion: CommandPalette.tsx source assertions', () => {
  // /features/4/oracle/assertions/0
  // Uses case-insensitive match: source has "FOR YOU" (header text) and "forYou*" (identifiers)
  it('CommandPalette.tsx contains no "for you" text (case-insensitive)', () => {
    const src = fs.readFileSync(srcFile, 'utf-8');
    const matches = src.match(/for.?you/gi);
    expect(
      matches,
      '"For You" / "FOR YOU" / "forYou" must not appear in CommandPalette.tsx — remove the render block and forYouNotes references'
    ).toBeNull();
  });

  // /features/4/oracle/assertions/1
  it('CommandPalette.tsx contains no getBlendedForYouNotes reference', () => {
    const src = fs.readFileSync(srcFile, 'utf-8');
    expect(
      src,
      'getBlendedForYouNotes must be removed from CommandPalette.tsx'
    ).not.toMatch(/getBlendedForYouNotes/);
  });

  it('CommandPalette.tsx contains no getSimilarNotes reference', () => {
    const src = fs.readFileSync(srcFile, 'utf-8');
    expect(
      src,
      'getSimilarNotes must be removed from CommandPalette.tsx'
    ).not.toMatch(/getSimilarNotes/);
  });

  it('CommandPalette.tsx contains no trackNoteAccess reference', () => {
    const src = fs.readFileSync(srcFile, 'utf-8');
    expect(
      src,
      'trackNoteAccess must be removed from CommandPalette.tsx'
    ).not.toMatch(/trackNoteAccess/);
  });

  it('CommandPalette.tsx contains no SimilarNote reference', () => {
    const src = fs.readFileSync(srcFile, 'utf-8');
    expect(
      src,
      'SimilarNote import must be removed from CommandPalette.tsx'
    ).not.toMatch(/SimilarNote/);
  });
});

describe('F16 deletion: CommandPalette.test.tsx test-file assertions', () => {
  // /features/4/oracle/assertions/2
  it('CommandPalette.test.tsx does not contain "Similar notes integration" describe block', () => {
    const src = fs.readFileSync(testFile, 'utf-8');
    expect(
      src,
      '"Similar notes integration" describe block must be removed from the test file'
    ).not.toMatch(/Similar notes integration/);
  });

  it('CommandPalette.test.tsx does not contain "calls trackNoteAccess" test', () => {
    const src = fs.readFileSync(testFile, 'utf-8');
    expect(
      src,
      '"calls trackNoteAccess" test must be removed from the test file'
    ).not.toMatch(/calls trackNoteAccess/);
  });

  it('CommandPalette.test.tsx does not mock getSimilarNotes in vi.mock override', () => {
    const src = fs.readFileSync(testFile, 'utf-8');
    expect(
      src,
      'getSimilarNotes vi.mock override must be removed from the test file'
    ).not.toMatch(/getSimilarNotes/);
  });

  it('CommandPalette.test.tsx does not mock trackNoteAccess in vi.mock override', () => {
    const src = fs.readFileSync(testFile, 'utf-8');
    expect(
      src,
      'trackNoteAccess vi.mock override must be removed from the test file'
    ).not.toMatch(/trackNoteAccess/);
  });
});
