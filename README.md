# ParchMark

ParchMark is a modern, minimalist markdown note-taking application inspired by ancient papyrus and modern markdown. It provides a clean, distraction-free interface for creating, editing, and organizing your notes with markdown formatting.

## Features

- 📝 Create, edit, and delete notes
- 🔄 Switch between edit and preview modes
- 🌙 Dark/light mode toggle
- 📱 Responsive layout with collapsible sidebar
- 🎨 Elegant styling with refined color scheme
- 📊 Beautiful markdown rendering

## Technologies Used

- React with TypeScript
- Vite for build system
- Chakra UI for component library
- React Markdown with RemarkGFM for markdown rendering
- Font Awesome for icons
- ESLint and Prettier for code quality

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

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

## Usage

- Create a new note by clicking the "+" button in the sidebar
- Select notes from the sidebar
- Edit a note by clicking the "Edit" button
- Save your changes with the "Save" button
- Delete a note by clicking the trash icon in the sidebar
- Toggle dark/light mode with the sun/moon icon in the header
- Hide/show the sidebar with the hamburger menu icon

## Implementation Details

ParchMark uses React's state management to handle notes and UI state. The application follows a component-based architecture with a clean separation of concerns. Styling is handled by Chakra UI with custom theme configuration.

For more detailed information, see:
- [MVP Document](./docs/MVP_DOCUMENT.md) - Detailed feature specifications
- [Implementation Plan](./docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [UI Regression Tests](./docs/UI_REGRESSION_TESTS.md) - Comprehensive UI testing plan

## Future Enhancements

- Data persistence with localStorage
- Enhanced markdown editor with toolbar
- Search functionality
- Tags and categories
- Mobile-optimized experience

## License

This project is licensed under the MIT License.

## Acknowledgements

- [React](https://reactjs.org/)
- [Chakra UI](https://chakra-ui.com/)
- [React Markdown](https://github.com/remarkjs/react-markdown)
- [Font Awesome](https://fontawesome.com/)
- [Inter Font](https://fonts.google.com/specimen/Inter)