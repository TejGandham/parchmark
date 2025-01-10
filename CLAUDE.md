# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

- **Dev server**: `npm run dev` - Starts Vite dev server (auto-opens browser, proxy to API on :8000)
- **Build**: `npm run build` - Runs TypeScript compiler and builds for production
- **Lint**: `npm run lint` - Runs ESLint on TypeScript/TSX files
- **Format**: `npm run format` - Formats code with Prettier
- **Test**: `npm test` - Runs Jest tests with coverage
- **Test coverage**: `npm run test:coverage` - Runs tests with detailed coverage report
- **Test watch**: `npm run test:watch` - Runs tests in watch mode for development
- **Test single file**: `npm test -- --testNamePattern="ComponentName"` or `npm test -- ComponentName.test.tsx`
- **Docker**: `docker-compose up -d` - Builds and runs the app in Docker

## Application Architecture

**ParchMark** is a markdown note-taking application with the following core architecture:

### Authentication & Security
- JWT-based authentication with Zustand persistence
- Protected routes using React Router v7
- User sessions persist across browser restarts via localStorage
- API proxy configuration: `/api` routes proxy to `localhost:8000`

### State Management Pattern
- **Zustand stores** with Immer middleware for immutable updates
- **Persistence middleware** for auth and UI state using localStorage
- **Feature-based stores**: `auth`, `notes`, `ui` each manage their specific domain
- Router sync hooks maintain URL/state consistency for notes navigation
- Store actions embedded in store object under `actions` key

### Component Architecture
- **Feature-based organization**: `features/{auth,notes,ui}/components/`
- **Chakra UI v2** component library with custom theme system and color tokens
- **React Router v7** for navigation and route protection
- **FontAwesome icons** for consistent iconography throughout app
- **React Markdown** with RemarkGFM for markdown rendering with GitHub flavored markdown

### Testing Infrastructure
- **Jest + jsdom** environment with comprehensive browser API mocks
- **React Testing Library** for component testing with custom render utilities
- **90% coverage threshold** enforced for branches, functions, lines, statements
- **Custom test utilities** with ChakraProvider wrapper in `test-utils/render.tsx`
- Test files mirror src structure in `src/__tests__/`
- **Form testing**: Use `fireEvent.submit(form)` for form submissions, not button clicks
- **Mocking**: Mock Zustand stores and Chakra UI hooks in component tests

## Code Style Guidelines

- **Typing**: Use strong TypeScript typing; avoid `any` type when possible
- **Imports**: Group imports by external libs, then internal modules
- **Components**: Use functional components with React hooks
- **State**: Use Zustand stores for global state, avoid prop drilling
- **Styling**: Use Chakra UI components and theme system, avoid inline styles
- **Icons**: Use FontAwesome React components consistently
- **Routing**: Use React Router with protected route patterns
- **Testing**: Write Jest tests mirroring src structure in `__tests__/`
- **Error Handling**: Use try/catch for async operations with user feedback

## Allowed URLs

- http://localhost:5173/ - Dev server (Vite)
- http://localhost:8080/ - Docker deployment
- http://localhost:8000/ - Backend API (proxied as `/api`)

## Key Implementation Patterns

### Component Structure
```
src/features/{domain}/
├── components/           # React components
├── store/               # Zustand store with actions
├── hooks/               # Custom hooks (e.g., router sync)
└── styles/              # Feature-specific CSS
```

### Store Pattern
- Use `create()` with `immer` and `persist` middleware
- Actions embedded in store object under `actions` key
- Type stores with clear interfaces for better development experience
- Persist auth and UI state, notes managed server-side

### Testing Pattern
- Tests in `src/__tests__/` mirroring source structure exactly
- Use custom render utility from `test-utils/render.tsx` with ChakraProvider wrapper
- Mock browser APIs in `jest.setup.js` for Chakra UI compatibility
- Test both authenticated and unauthenticated states for auth-related features
- Use React Testing Library queries and user-event for interactions
- Coverage targets: 90%+ for statements, branches, functions, and lines
- Mock `useAuthStore` and `useNotesStore` when testing components that use them directly

### Markdown Processing
- Central `markdownService.ts` handles title extraction and content formatting
- Custom CSS in `features/notes/styles/` for markdown rendering
- Mermaid component for diagram rendering support

## Docker Configuration

- Multi-stage build with Node.js 18
- Nginx reverse proxy for production
- Environment-specific nginx configs (HTTP/HTTPS)
- Health checks and proper container networking

** DO NOT ADD CLAUDE RELATED COMMIT INFORMATION TO THE COMMIT MESSAGE.**
** DO NOT ADD COMMENTS TO GENERATED CODE UNLESS THEY ARE ABSOLUTELY REQUIRED BECAUSE THEY POINT OUT AN IMPORTANT MESSAGE NOT APPARENT FROM THE CODE.**
** ASSUME NPM RUN DEV IS ALREADY RUNNING WHEN MAKING CHANGES.**
** THIS IS IMPORTANT Always add commit date for commits to be a few days after the last committed commit date. NO EXCEPTIONS.**
** DO NOT ADD CLAUDE RELATED COMMIT INFORMATION TO THE COMMIT MESSAGE.**
