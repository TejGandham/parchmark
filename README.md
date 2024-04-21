# ParchMark: Modern Markdown Note-Taking

![ParchMark Logo](/public/favicon.svg)

## Overview

ParchMark is a clean, elegant note-taking application inspired by ancient papyrus scrolls and modern markdown technology. It combines a minimalist user interface with powerful markdown capabilities to create a distraction-free writing environment.

## Features

- **Markdown Support**: Full markdown rendering with proper styling
- **Clean UI**: Distraction-free writing environment
- **Automatic Title Extraction**: Titles are automatically extracted from H1 headings
- **Sidebar Organization**: Easy access to all your notes
- **Local Storage**: Notes are saved to local storage for persistence
- **Responsive Design**: Works on desktop and mobile devices

## Technologies Used

- React with TypeScript
- Vite for fast development and building
- Chakra UI for components and styling
- React Markdown for rendering markdown
- FontAwesome for icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/parchmark.git
cd parchmark

# Install dependencies
npm install

# Start the development server
npm run dev
```

## Usage

1. Create a new note using the + button in the sidebar
2. Write your note content using markdown syntax
3. The title is automatically extracted from the first H1 heading (# Title)
4. Save your note using the save button
5. Toggle between edit and preview mode using the edit/save buttons

## Development

```bash
# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── assets/           # Static assets
├── components/       # React components
│   ├── common/       # Shared components
│   ├── layout/       # Layout components
│   └── notes/        # Note-related components
├── features/         # Feature modules
│   └── notes/        # Notes feature
├── hooks/            # Custom React hooks
├── services/         # Service modules
├── styles/           # Global styles
├── types/            # TypeScript types
└── utils/            # Utility functions
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.