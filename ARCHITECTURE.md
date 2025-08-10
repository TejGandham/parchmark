# ParchMark - Architecture Document

## System Architecture

ParchMark follows a modern client-server architecture with a clear separation between the frontend and backend components:

```
┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │
│  React Frontend   │◄────►│  Phoenix Backend  │
│  (UI Directory)   │      │  (API Directory)  │
│                   │      │                   │
└───────────────────┘      └───────────────────┘
         ▲                          ▲
         │                          │
         ▼                          ▼
┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │
│ Browser Storage   │      │    PostgreSQL     │
│  (localStorage)   │      │    Database       │
│                   │      │                   │
└───────────────────┘      └───────────────────┘
```

## Frontend Architecture (UI)

### Component Structure

ParchMark's UI implements a feature-based architecture with clear separation of concerns:

```
src/
├── features/
│   ├── auth/          - Authentication components and state
│   ├── notes/         - Note editing and management 
│   └── ui/            - Shared UI components
├── services/          - Cross-cutting concerns
├── store/             - Global state management
├── styles/            - Global styling
├── types/             - TypeScript type definitions
└── utils/             - Utility functions
```

### State Management

The application uses Zustand for global state management with the following stores:

1. **Notes Store** (`notes.ts`)
   - Manages the collection of notes
   - Handles CRUD operations for notes
   - Stores current note selection and editing state
   - Persists data to localStorage

2. **UI Store** (`ui.ts`)
   - Controls UI state like sidebar visibility
   - Manages theme preferences (dark/light mode)

3. **Auth Store** (`auth.ts`)
   - Handles user authentication state
   - Manages login/logout operations
   - Stores basic user information

### Data Flow

1. **Component Hierarchy**:
   - `App` - Root component with global providers
     - `NotesContainer` - Main layout component
       - `Header` - App navigation and controls
       - `Sidebar` - Note listing and management
       - `NoteContent` - Note editing and preview

2. **State Flow**:
   - UI interactions trigger store actions
   - Store updates trigger component re-renders
   - URL synchronization via custom hooks
   - Data persistence via localStorage

## Backend Architecture (API)

### Core Components

1. **Phoenix Framework**:
   - RESTful API endpoints
   - Controller-based request handling
   - Ecto for database interactions

2. **Context Organization**:
   - `Accounts` context for user and note management
   - Clean separation of business logic from web layer

3. **Data Models**:
   - `User` - Represents application users
   - `Note` - Represents markdown notes with user association

### API Design

The API follows RESTful principles with nested resources:

```
/api/users           - User management endpoints
/api/users/:id/notes - Notes management for a specific user
```

Supported operations include:
- `GET` for retrieving resources
- `POST` for creating resources
- `PUT/PATCH` for updating resources
- `DELETE` for removing resources

## Integration Points

1. **Frontend to Backend Communication**:
   - RESTful API calls from React to Phoenix
   - JSON payload format for data exchange
   - Token-based authentication (JWT)

2. **Data Synchronization**:
   - Frontend stores maintain local copies in localStorage
   - Backend provides persistent storage in PostgreSQL
   - Future: Real-time sync via WebSockets

## Security Architecture

1. **Authentication**:
   - Custom login system in the UI
   - Auth token management
   - Protected routes with React Router

2. **Data Protection**:
   - HTTPS for all communications
   - Secure storage of user credentials
   - Input sanitization in both frontend and backend

## Deployment Architecture

The application is containerized for easy deployment:

1. **UI Container**:
   - Nginx for static file serving
   - Built React application

2. **API Container**:
   - Phoenix runtime environment
   - Configuration via environment variables

3. **Database Container**:
   - PostgreSQL database
   - Volume mounts for data persistence

These containers are orchestrated with Docker Compose for development and can be deployed to various cloud environments.

## Future Architectural Considerations

1. **Scalability Enhancements**:
   - Load balancing for API servers
   - Database sharding for large datasets
   - Redis caching for frequently accessed data

2. **Feature Extensions**:
   - WebSocket integration for real-time collaboration
   - Background workers for asynchronous tasks
   - File storage service integration

3. **Advanced Security**:
   - OAuth integration for third-party login
   - Role-based access control
   - Audit logging for security events