# ParchMark

ParchMark is a modern, minimalist markdown note-taking application inspired by ancient papyrus and modern markdown. It provides a clean, distraction-free interface for creating, editing, and organizing your notes with markdown formatting.

## Features

- 📝 Create, edit, and delete notes
- 🔄 Switch between edit and preview modes
- 🌙 Dark/light mode toggle
- 📱 Responsive layout with collapsible sidebar
- 🎨 Elegant styling with refined color scheme
- 📊 Beautiful markdown rendering
- 🔒 User authentication with protected routes
- 🔄 Data persistence across sessions

## Technologies Used

- React with TypeScript
- Vite for build system
- Chakra UI for component library
- React Markdown with RemarkGFM for markdown rendering
- Font Awesome for icons
- ESLint and Prettier for code quality
- Zustand for state management
- React Router for routing
- Jest and React Testing Library for testing
- Docker for containerization

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

#### Local Development

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/parchmark.git
   cd parchmark
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to http://localhost:5173

#### Docker Deployment

1. Build and run using Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Access the application at http://localhost:8080

## Usage

- Log in with your credentials to access your notes
- Create a new note by clicking the "+" button in the sidebar
- Select notes from the sidebar
- Edit a note by clicking the "Edit" button
- Save your changes with the "Save" button
- Delete a note by clicking the trash icon in the sidebar
- Toggle dark/light mode with the sun/moon icon in the header
- Hide/show the sidebar with the hamburger menu icon
- Log out when you're done to protect your notes

## Implementation Details

ParchMark uses Zustand for state management and React Router for navigation. The application follows a feature-based architecture with clean separation of concerns. Authentication is implemented with protected routes to secure user content. Styling is handled by Chakra UI with custom theme configuration.

The project is containerized with Docker for easy deployment and consistent environment across different platforms.

For more detailed information, see:
- [MVP Document](./docs/MVP_DOCUMENT.md) - Detailed feature specifications
- [Implementation Plan](./docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [UI Regression Tests](./tests/UI_REGRESSION_TESTS.md) - Comprehensive UI testing plan

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## Future Enhancements

- Enhanced markdown editor with toolbar
- Search functionality
- Tags and categories
- Mobile-optimized experience
- Collaborative editing
- Note sharing capabilities
- Additional authentication methods (OAuth, SSO)
- End-to-end encryption

## License

This project is licensed under the MIT License.

## Acknowledgements

- [React](https://reactjs.org/)
- [Chakra UI](https://chakra-ui.com/)
- [React Markdown](https://github.com/remarkjs/react-markdown)
- [Font Awesome](https://fontawesome.com/)
- [Playfair Display Font](https://fonts.google.com/specimen/Playfair+Display)
- [Zustand](https://github.com/pmndrs/zustand)
- [React Router](https://reactrouter.com/)
- [Jest](https://jestjs.io/)
- [Docker](https://www.docker.com/)