/**
 * ParchMark token build — DTCG JSON → src/design-system/tokens.css
 *
 * Two passes (light = :root, dark = [data-theme="dark"]) concatenated into a
 * single stylesheet. Dark emits only the tokens overridden in semantic.dark.json.
 * Run: npm run build:tokens
 */
import StyleDictionary from 'style-dictionary';
import { readFile, writeFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const buildDir = path.join(here, 'build');

// Emit the legacy CSS variable names the prototype already consumes
// (--p600, --surface, --shadow-sm…) instead of full token paths.
StyleDictionary.registerTransform({
  name: 'name/parchmark-css',
  type: 'name',
  transform: (token) =>
    token.$extensions?.['com.parchmark.cssName'] ?? token.path.join('-'),
});

StyleDictionary.registerTransformGroup({
  name: 'parchmark/css',
  transforms: ['name/parchmark-css', 'fontFamily/css', 'shadow/css/shorthand'],
});

StyleDictionary.registerFileHeader({
  name: 'parchmark/header',
  fileHeader: () => [
    'ParchMark design tokens — GENERATED, do not edit by hand.',
    'Source of truth: tokens/*.json (W3C DTCG format). Rebuild: npm run build:tokens',
  ],
});

const platform = (file, selector, filter) => ({
  transformGroup: 'parchmark/css',
  buildPath: buildDir + path.sep,
  files: [{
    destination: file,
    format: 'css/variables',
    filter,
    options: { selector, outputReferences: true, fileHeader: 'parchmark/header' },
  }],
});

const light = new StyleDictionary({
  source: [path.join(here, 'primitives.json'), path.join(here, 'semantic.json')],
  platforms: { css: platform('light.css', ':root') },
});

// Dark sources alone — merging with the light sources would deep-merge
// multi-layer shadow arrays per-index instead of replacing them.
const dark = new StyleDictionary({
  source: [path.join(here, 'semantic.dark.json')],
  platforms: { css: platform('dark.css', '[data-theme="dark"]') },
});

await light.buildAllPlatforms();
await dark.buildAllPlatforms();

const out = [
  await readFile(path.join(buildDir, 'light.css'), 'utf8'),
  await readFile(path.join(buildDir, 'dark.css'), 'utf8'),
].join('\n');

const dest = path.join(here, '..', 'tokens.css');
await writeFile(dest, out);
await rm(buildDir, { recursive: true, force: true });
console.log('Wrote', dest);
