# ParchMark - Project Overview

## What is ParchMark?

ParchMark is a modern, minimalist markdown note-taking application inspired by ancient papyrus and modern markdown. It offers a simple yet elegant interface for writing, managing, and previewing markdown notes with seamless data persistence and a refined user experience.

## Core Features

### Note Management
- Create, read, update, and delete markdown notes
- Automatic title extraction from markdown content
- Organized sidebar for quick note selection and management

### Markdown Editor and Viewer
- Full markdown editing with live preview
- Elegant styling of markdown elements (headings, lists, code blocks, etc.)
- Toggle between edit and preview modes

### User Interface
- Clean, distraction-free layout with customizable sidebar
- Dark/light theme support for different working environments
- Responsive design adapting to different screen sizes

### User Authentication
- Simple login system to protect your notes
- User-specific note collections

## Tech Stack

### Frontend (UI)
- **Framework**: React with TypeScript
- **Build System**: Vite
- **UI Library**: Chakra UI
- **State Management**: Zustand
- **Routing**: React Router
- **Markdown Rendering**: React Markdown with remarkGfm

### Backend (API)
- **Framework**: Phoenix/Elixir
- **Database**: PostgreSQL
- **Authentication**: Basic user authentication (extensible)
- **API**: RESTful endpoints for notes and users

## Project Structure

The project is organized into two main components:

1. **UI (Frontend)**: Located in `/ui` directory
   - Feature-based organization (auth, notes, ui)
   - Component-driven architecture
   - Zustand state management with localStorage persistence
   - Responsive design for desktop (mobile-optimized in roadmap)

2. **API (Backend)**: Located in `/api` directory
   - Phoenix framework with RESTful endpoints
   - PostgreSQL database for data persistence
   - User and Note models with relationships
   - Docker containerization for development and deployment

## Development Status and Roadmap

### Current Status
- Core note management functionality implemented
- Markdown editing and preview working
- Basic authentication in place
- Theme switching implemented
- Responsive UI framework established

### Upcoming Features
- Enhanced markdown editor with syntax highlighting
- Search functionality
- Tags and categories for better organization
- Mobile-optimized experience
- Cloud synchronization
- Sharing and collaboration features

## Getting Started

### Running the UI
- Development: `npm run dev` in the `/ui` directory
- Production build: `npm run build`
- Docker: `docker-compose up -d`

### Running the API
- Setup: `mix setup` in the `/api` directory
- Development: `mix phx.server`
- Docker: `docker-compose up -d`