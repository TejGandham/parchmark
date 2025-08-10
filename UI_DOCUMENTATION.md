# ParchMark UI Documentation

## Overview

The ParchMark user interface is a modern React application built with TypeScript, Chakra UI, and Zustand for state management. It provides a clean, intuitive interface for creating, editing, and managing markdown notes.

## Project Structure

The UI project follows a feature-based organization:

```
src/
├── App.tsx                 # Main application component
├── features/               # Feature-based modules
│   ├── auth/               # Authentication
│   │   ├── components/     # Auth-related UI components
│   │   └── store/          # Auth state management
│   ├── notes/              # Notes functionality
│   │   ├── components/     # Note-related UI components
│   │   ├── hooks/          # Custom hooks for notes
│   │   └── store/          # Notes state management
│   └── ui/                 # Shared UI components
│       ├── components/     # Core UI elements
│       └── store/          # UI state management
├── services/               # Shared services
├── store/                  # Global store index
├── styles/                 # Global styles
├── types/                  # TypeScript type definitions
└── utils/                  # Utility functions and constants
```

## Core Components

### Layout Components

#### Header (`features/ui/components/Header.tsx`)

The top navigation bar containing:
- App title/logo
- Sidebar toggle button
- Theme toggle button (dark/light mode)

#### Sidebar (`features/ui/components/Sidebar.tsx`)

The left sidebar displaying:
- "Notes" header with note count
- Create new note button
- List of notes with titles and delete buttons
- Visual highlighting of the currently selected note

#### NotesContainer (`features/notes/components/NotesContainer.tsx`)

The main container orchestrating the notes feature:
- Manages layout between Header, Sidebar, and note content
- Coordinates state between components
- Handles responsive behavior

### Note Components

#### NoteContent (`features/notes/components/NoteContent.tsx`)

The primary note viewing/editing component:
- Displays note title and content
- Switches between edit and preview modes
- Renders markdown content with styling

#### NoteActions (`features/notes/components/NoteActions.tsx`)

The action buttons component:
- Edit/Save toggle button
- Additional note actions

#### NoteItem (`features/notes/components/NoteItem.tsx`)

Individual note list item component:
- Displays note title with truncation
- Delete button with confirmation
- Selection highlight when active

### Authentication Components

#### LoginForm (`features/auth/components/LoginForm.tsx`)

The authentication form:
- Username and password fields
- Login button with validation
- Error message handling

#### ProtectedRoute (`features/auth/components/ProtectedRoute.tsx`)

Route protection component:
- Redirects unauthenticated users to login
- Allows authenticated users to access protected routes

## State Management

ParchMark uses Zustand for state management with a sliced store approach:

### Notes Store (`features/notes/store/notes.ts`)

Manages the core note functionality:

**State:**
- `notes`: Array of Note objects
- `currentNoteId`: ID of currently selected note
- `editedContent`: Content being edited (null when not in edit mode)

**Actions:**
- `createNote()`: Creates a new note and selects it
- `updateNote(id, content)`: Updates note content and extracts title
- `deleteNote(id)`: Removes a note and updates selection
- `setCurrentNote(id)`: Selects a note
- `setEditedContent(content)`: Sets content being edited or null

### UI Store (`features/ui/store/ui.ts`)

Manages the UI state:

**State:**
- `isSidebarOpen`: Controls sidebar visibility
- `isDarkMode`: Controls theme (light/dark)

**Actions:**
- `toggleSidebar()`: Toggles sidebar visibility
- `toggleDarkMode()`: Switches between light and dark themes

### Auth Store (`features/auth/store/auth.ts`)

Manages authentication state:

**State:**
- `isAuthenticated`: Boolean indicating auth status
- `user`: User object or null
- `error`: Authentication error message or null

**Actions:**
- `login(username, password)`: Authenticates user
- `logout()`: Ends user session
- `clearError()`: Clears authentication errors

## Custom Hooks

### useStoreRouterSync (`features/notes/hooks/useStoreRouterSync.ts`)

Synchronizes URL parameters with store state:
- Updates store when URL changes
- Updates URL when store selection changes
- Provides clean URL sharing and browser history

## Styling

ParchMark uses a combination of Chakra UI theming and custom CSS:

### Theme Configuration (`styles/theme.ts`)

- Custom colors with primary burgundy (#580c24)
- Typography settings with 'Inter' font
- Component style overrides

### Token System (`styles/tokens.ts`)

- Consistent color variables
- Typography scales
- Spacing values

### Markdown Styling (`features/notes/styles/markdown.css`)

- Custom styling for markdown elements
- Elegant typography for headings, lists, blockquotes
- Code block styling with syntax highlighting
- Responsive table formatting

## Running the UI

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at http://localhost:5173

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker

```bash
# Start the UI in Docker
docker-compose up -d
```

The UI will be available at http://localhost:8080

## Testing

ParchMark has comprehensive Jest tests:

```bash
# Run all tests
npm test

# Run tests with coverage report
npm run test:coverage
```

Tests follow the same directory structure as the source code in the `__tests__` directory.

## State Management Integration with API

The UI is designed to work either:
1. Standalone with localStorage persistence
2. Connected to the Phoenix API backend

When using the API backend:
- API calls replace localStorage operations
- Authentication tokens are handled by the Auth store
- Real-time synchronization (future feature)

## UI Design Principles

### Focus on Content

- Clean, minimal interface
- Distraction-free writing environment
- Typography optimized for readability

### Responsive Design

- Adapts to different screen sizes
- Collapsible sidebar for space optimization
- Touch-friendly controls (in progress)

### Theme Support

- Light theme for daytime use
- Dark theme for night work
- Consistent styling across themes

### Elegant Markdown

- Refined styling of all markdown elements
- Proper spacing and visual hierarchy
- Accent colors for blockquotes and links