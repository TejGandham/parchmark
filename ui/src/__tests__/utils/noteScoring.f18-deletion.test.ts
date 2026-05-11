// @vitest-environment node
/**
 * F18 — Static-grep oracle assertions.
 *
 * NOTE on `@vitest-environment node`: this file uses Node fs to verify
 * source-level deletion. Do NOT copy this pattern for behavioral tests —
 * use the default jsdom environment for anything that exercises React
 * component behavior. This is a deletion-shaped oracle, not a general
 * testing pattern.
 *
 * These tests FAIL until the implementer deletes noteScoring.ts (and its
 * test file) and removes orphaned symbols from services/api.ts,
 * config/api.ts, and types/index.ts.
 *
 * Oracle pointers (feature_pointer_base = /features/6):
 *   /features/6/oracle/assertions/0 — noteScoring.ts and noteScoring.test.ts must not exist
 *   /features/6/oracle/assertions/1 — trackNoteAccess, getSimilarNotes absent from services/api.ts
 *   /features/6/oracle/assertions/2 — ACCESS, SIMILAR absent as endpoint-constant declarations in config/api.ts
 *   /features/6/oracle/assertions/3 — SimilarNote, accessCount, lastAccessedAt absent from types/index.ts
 *   /features/6/oracle/assertions/4 — tsc --noEmit: delegated to the build gate (see Decisions)
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const repoRoot = path.resolve(__dirname, '../../../..');

const noteScoringUtil = path.join(repoRoot, 'ui/src/utils/noteScoring.ts');
const noteScoringTest = path.join(
  repoRoot,
  'ui/src/__tests__/utils/noteScoring.test.ts'
);
const apiTs = path.join(repoRoot, 'ui/src/services/api.ts');
const configApiTs = path.join(repoRoot, 'ui/src/config/api.ts');
const typesIndex = path.join(repoRoot, 'ui/src/types/index.ts');

// /features/6/oracle/assertions/0
describe('F18 deletion: noteScoring files must not exist', () => {
  it('ui/src/utils/noteScoring.ts does not exist', () => {
    expect(
      fs.existsSync(noteScoringUtil),
      'ui/src/utils/noteScoring.ts must be deleted — it is an orphaned For You util with no remaining call sites'
    ).toBe(false);
  });

  it('ui/src/__tests__/utils/noteScoring.test.ts does not exist', () => {
    expect(
      fs.existsSync(noteScoringTest),
      'ui/src/__tests__/utils/noteScoring.test.ts must be deleted — it tests the deleted noteScoring.ts module'
    ).toBe(false);
  });
});

// /features/6/oracle/assertions/1
describe('F18 deletion: services/api.ts symbol assertions', () => {
  it('services/api.ts contains no trackNoteAccess reference', () => {
    const src = fs.readFileSync(apiTs, 'utf-8');
    expect(
      src,
      'trackNoteAccess must be removed from services/api.ts — delete the function definition and the default export entry'
    ).not.toMatch(/trackNoteAccess/);
  });

  it('services/api.ts contains no getSimilarNotes reference', () => {
    const src = fs.readFileSync(apiTs, 'utf-8');
    expect(
      src,
      'getSimilarNotes must be removed from services/api.ts — delete the function definition and the default export entry'
    ).not.toMatch(/getSimilarNotes/);
  });
});

// /features/6/oracle/assertions/2
describe('F18 deletion: config/api.ts endpoint-constant assertions', () => {
  it('config/api.ts NOTES block contains no ACCESS endpoint-constant declaration', () => {
    const src = fs.readFileSync(configApiTs, 'utf-8');
    // Match "ACCESS:" as an object key (with optional whitespace), not merely the word in a comment.
    // This regex targets `ACCESS:` followed by a space or function paren — i.e. a declaration, not prose.
    expect(
      src,
      'ACCESS: endpoint constant must be removed from API_ENDPOINTS.NOTES in config/api.ts'
    ).not.toMatch(/\bACCESS\s*:/);
  });

  it('config/api.ts NOTES block contains no SIMILAR endpoint-constant declaration', () => {
    const src = fs.readFileSync(configApiTs, 'utf-8');
    expect(
      src,
      'SIMILAR: endpoint constant must be removed from API_ENDPOINTS.NOTES in config/api.ts'
    ).not.toMatch(/\bSIMILAR\s*:/);
  });
});

// /features/6/oracle/assertions/3
describe('F18 deletion: types/index.ts type assertions', () => {
  it('types/index.ts contains no SimilarNote reference', () => {
    const src = fs.readFileSync(typesIndex, 'utf-8');
    expect(
      src,
      'SimilarNote interface must be removed from types/index.ts'
    ).not.toMatch(/SimilarNote/);
  });

  it('types/index.ts contains no accessCount reference', () => {
    const src = fs.readFileSync(typesIndex, 'utf-8');
    expect(
      src,
      'accessCount field must be removed from the Note interface in types/index.ts'
    ).not.toMatch(/accessCount/);
  });

  it('types/index.ts contains no lastAccessedAt reference', () => {
    const src = fs.readFileSync(typesIndex, 'utf-8');
    expect(
      src,
      'lastAccessedAt field must be removed from the Note interface in types/index.ts'
    ).not.toMatch(/lastAccessedAt/);
  });
});
