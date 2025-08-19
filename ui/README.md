# ParchMark

A modern, fast, and intuitive markdown note-taking application built with React, TypeScript, and Vite. Inspired by ancient papyrus and modern markdown, ParchMark provides a clean, distraction-free interface for creating, editing, and organizing your notes.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Tests](https://img.shields.io/badge/tests-217%20passing-success)
![Coverage](https://img.shields.io/badge/coverage->90%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- 📝 **Full Markdown Support** - GitHub Flavored Markdown (GFM) with live preview
- 🔐 **Secure Authentication** - JWT-based auth with persistent sessions
- 💾 **Auto-Save** - Changes persist automatically to backend
- 🎨 **Beautiful UI** - Clean, responsive interface with Chakra UI
- 🌙 **Dark/Light Mode** - Toggle between themes for comfortable viewing
- 📊 **Mermaid Diagrams** - Built-in support for flowcharts and diagrams
- 🚀 **Lightning Fast** - Powered by Vite for instant HMR and optimized builds
- 📱 **Responsive Design** - Seamless experience on desktop and mobile
- 🧪 **Battle-Tested** - 217+ tests with >90% coverage
- 🔄 **Real-time Sync** - Notes sync across sessions and devices

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Chakra UI v2
- **State Management**: Zustand with Immer
- **Routing**: React Router v7
- **Markdown**: React Markdown + Remark GFM
- **Icons**: FontAwesome
- **Testing**: Jest + React Testing Library
- **Code Quality**: ESLint + Prettier
- **Containerization**: Docker + Nginx

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000 (for full functionality)
- Docker and Docker Compose (optional)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/parchmark.git
   cd parchmark/ui
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   The app will open automatically at `http://localhost:5173`

### Docker Deployment

```bash
docker-compose up -d
```

Access the application at `http://localhost:8080`

## 📜 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run lint` | Run ESLint checks |
| `npm run format` | Format code with Prettier |
| `npm test` | Run test suite |
| `npm run test:coverage` | Generate coverage report |
| `npm run test:watch` | Run tests in watch mode |

## 📁 Project Structure

```
src/
├── features/               # Feature-based modules
│   ├── auth/              # Authentication components & logic
│   │   ├── components/    # Login form, user status
│   │   ├── store/         # Auth state management
│   │   └── hooks/         # Auth-related hooks
│   ├── notes/             # Notes management
│   │   ├── components/    # Note editor, list, content
│   │   ├── store/         # Notes state management
│   │   ├── hooks/         # Router sync hooks
│   │   └── styles/        # Markdown styles
│   └── ui/                # Shared UI components
│       ├── components/    # Header, sidebar, theme
│       └── store/         # UI state (theme, sidebar)
├── services/              # API and utility services
│   ├── api.ts            # API client configuration
│   └── markdown.ts       # Markdown utilities
├── test-utils/           # Testing utilities
└── __tests__/            # Test files (mirrors src)
```

## 🏗️ Architecture

### State Management
- **Zustand stores** with Immer for immutable updates
- **Persistence** via localStorage for auth/UI state
- **Router sync** hooks maintain URL-state consistency

### Component Philosophy
- Feature-based organization for scalability
- Composition over inheritance
- Custom hooks for business logic
- Consistent Chakra UI theming

### Testing Strategy
- Unit & integration tests for all components
- Custom render utilities with providers
- Mock stores for isolated testing
- Enforced 90% coverage thresholds

## 🔌 API Integration

The frontend integrates with a RESTful backend API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User authentication |
| `/api/notes` | GET | Fetch all notes |
| `/api/notes` | POST | Create new note |
| `/api/notes/:id` | PUT | Update note |
| `/api/notes/:id` | DELETE | Delete note |

## 🧪 Testing

```bash
# Run all tests
npm test

# Generate coverage report
npm run test:coverage

# Watch mode for development
npm run test:watch

# Test specific file
npm test -- LoginForm.test.tsx
```

**Current Coverage:**
- Statements: >90%
- Branches: >90%
- Functions: >90%
- Lines: >90%

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- ✅ Follow existing code style (ESLint/Prettier)
- ✅ Write tests for new features
- ✅ Update documentation
- ✅ Ensure all tests pass
- ✅ Maintain >90% coverage

## 📊 Performance

- **Lighthouse Score**: 95+
- **First Contentful Paint**: <1s
- **Time to Interactive**: <2s
- **Bundle Size**: <500KB gzipped

## 🔒 Security

- JWT-based authentication
- Protected routes for authenticated content
- Secure API communication
- Input validation and sanitization
- XSS protection via React's built-in escaping

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [React](https://reactjs.org/) - UI library
- [Vite](https://vitejs.dev/) - Build tool
- [Chakra UI](https://chakra-ui.com/) - Component library
- [Zustand](https://github.com/pmndrs/zustand) - State management
- [React Router](https://reactrouter.com/) - Routing
- [React Markdown](https://github.com/remarkjs/react-markdown) - Markdown rendering
- [FontAwesome](https://fontawesome.com/) - Icons
- [Jest](https://jestjs.io/) - Testing framework

## 📬 Support

For bugs, questions, or feature requests, please [open an issue](https://github.com/yourusername/parchmark/issues).

---

**Version 1.0.0** - Production Ready 🎉
