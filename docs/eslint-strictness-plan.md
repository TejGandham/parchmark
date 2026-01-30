# Plan: Strengthen Frontend ESLint Configuration

## Current State

The frontend ESLint config (`ui/.eslintrc.cjs`) uses only "recommended" presets. While TypeScript is already strict (`strict: true`, `noUnusedLocals`, etc.), ESLint rules are **moderate**.

## Analysis (via Gemini + Codex)

### Gemini Assessment
- Missing **type-aware linting** (no `parserOptions.project`)
- Missing **eslint-plugin-react** (only has react-hooks)
- Missing **accessibility rules** entirely
- Recommends `strict-type-checked` preset

### Codex Assessment
- Missing **async/promise safety** rules (floating promises, misused promises)
- Missing **import hygiene** (no cycle detection, no ordering)
- Missing **React render stability** checks
- Missing **complexity guards**
- Recommends `recommended-requiring-type-checking`

### Agreement (Both Models)
1. **Enable type-checked rules** - Catches promise bugs, type misuse
2. **Add jsx-a11y** - Accessibility is completely missing
3. **Add import organization** - Prevents merge conflicts, cycle detection
4. **Add stricter TypeScript rules** - `no-floating-promises`, `no-explicit-any` as error

### Differences
| Topic | Gemini | Codex |
|-------|--------|-------|
| Preset | `strict-type-checked` | `recommended-requiring-type-checking` |
| Import plugin | `simple-import-sort` | `eslint-plugin-import` |
| Complexity | Not mentioned | `complexity`, `max-lines-per-function` |

### Recommendation
Use **Codex's approach** with `eslint-plugin-import` (more features: cycle detection, extraneous deps) but adopt **Gemini's stricter preset** (`strict-type-checked`). Skip complexity rules initially (can add later if needed).

---

## Implementation Plan

### 1. Install new ESLint plugins

```bash
npm install -D eslint-plugin-react eslint-plugin-import eslint-plugin-jsx-a11y eslint-import-resolver-typescript
```

### 2. Update `.eslintrc.cjs`

**New extends:**
```js
extends: [
  'eslint:recommended',
  'plugin:@typescript-eslint/strict-type-checked',
  'plugin:@typescript-eslint/stylistic-type-checked',
  'plugin:react/recommended',
  'plugin:react/jsx-runtime',
  'plugin:react-hooks/recommended',
  'plugin:import/recommended',
  'plugin:import/typescript',
  'plugin:jsx-a11y/recommended',
  'plugin:prettier/recommended', // Must be last
],
```

**Add parserOptions (required for type-checked rules):**
```js
parserOptions: {
  project: ['./tsconfig.app.json', './tsconfig.node.json'],
  tsconfigRootDir: __dirname,
},
```

**Add plugins:**
```js
plugins: ['react-refresh', 'import', 'jsx-a11y'],
```

**Add settings (for React version detection):**
```js
settings: {
  react: { version: 'detect' },
  'import/resolver': {
    typescript: true,
    node: true,
  },
},
```

**New rules:**
```js
rules: {
  // Async safety (HIGH VALUE)
  '@typescript-eslint/no-floating-promises': 'error',
  '@typescript-eslint/no-misused-promises': ['error', { checksVoidReturn: false }],

  // Type rigor
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/consistent-type-imports': ['warn', { prefer: 'type-imports' }],
  '@typescript-eslint/switch-exhaustiveness-check': 'error',

  // React stability
  'react/jsx-no-constructed-context-values': 'error',
  'react/no-unstable-nested-components': ['warn', { allowAsProps: true }],
  'react/self-closing-comp': 'warn',

  // Import hygiene
  'import/order': ['warn', {
    groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
    'newlines-between': 'always',
  }],
  'import/no-cycle': 'warn',

  // General
  'no-console': ['warn', { allow: ['warn', 'error'] }],
  'eqeqeq': ['error', 'always'],

  // Existing
  'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
}
```

### 3. Fix lint errors

After updating config, run `npm run lint` and fix any new errors. Type-checked rules may surface issues like:
- Unhandled promises (add `await` or `void`)
- Missing `key` props in lists
- Accessibility issues (missing `alt`, invalid ARIA)
- Import ordering (auto-fixable)

---

## Files to Modify

| File | Change |
|------|--------|
| `ui/.eslintrc.cjs` | Update extends, add parserOptions, plugins, settings, rules |
| `ui/package.json` | Add dev dependencies |
| `ui/src/**/*.{ts,tsx}` | Fix any new lint errors |

---

## Verification

1. `cd ui && npm install` - Install new plugins
2. `npm run lint` - Should pass (or show fixable errors)
3. `npm run lint -- --fix` - Auto-fix import ordering
4. `npm run build` - Verify TypeScript + Vite build still works
5. `make test-ui-all` - Full UI test suite passes

---

## Why These Rules Matter

| Rule | Prevents |
|------|----------|
| `no-floating-promises` | Silent async failures, unhandled rejections |
| `no-misused-promises` | Passing promises where void expected |
| `switch-exhaustiveness-check` | Missing cases in switch on union types |
| `jsx-a11y/*` | Inaccessible UI for screen reader users |
| `import/no-cycle` | Circular dependencies causing bundling issues |
| `import/order` | Merge conflicts, inconsistent imports |
| `jsx-no-constructed-context-values` | Unnecessary re-renders in React 18 |
