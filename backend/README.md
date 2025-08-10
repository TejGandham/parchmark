# ParchMark Backend API

A FastAPI-based backend for the ParchMark note-taking application, providing JWT authentication and note management capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation & Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env` file and update the `SECRET_KEY` for production use
   - The default configuration works for development

4. **Start the server:**
   ```bash
   python run.py
   ```

The server will start at `http://localhost:8000` with the following endpoints available:
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT utilities and password hashing
│   │   └── dependencies.py  # Authentication dependencies
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py      # SQLAlchemy configuration
│   │   ├── init_db.py       # Database initialization
│   │   └── seed.py          # Database seeding utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy models (User, Note)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints
│   │   └── notes.py         # Notes CRUD endpoints
│   └── schemas/
│       ├── __init__.py
│       └── schemas.py       # Pydantic schemas
├── .env                     # Environment configuration
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── run.py                   # Server startup script
└── README.md               # This file
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for stateless authentication:

- **Token Expiration:** 30 minutes (configurable)
- **Algorithm:** HS256
- **Password Hashing:** bcrypt

### Default Test User

For development and testing purposes, a default user is automatically created:
- **Username:** `user`
- **Password:** `password`

## 📚 API Endpoints

### Authentication Endpoints

#### POST `/auth/login`
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

#### POST `/auth/logout`
Client-side logout endpoint (token invalidation handled by frontend).

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

#### GET `/auth/me`
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

### Notes Endpoints

All notes endpoints require authentication via JWT token in the Authorization header.

#### GET `/notes`
Get all notes for the authenticated user.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
[
  {
    "id": "1",
    "title": "Welcome to ParchMark",
    "content": "# Welcome to ParchMark\n\nThis is a simple yet powerful...",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

#### POST `/notes`
Create a new note.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Request Body:**
```json
{
  "title": "My New Note",
  "content": "# My New Note\n\nThis is the content of my note..."
}
```

**Response:**
```json
{
  "id": "generated-uuid",
  "title": "My New Note",
  "content": "# My New Note\n\nThis is the content of my note...",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### PUT `/notes/{note_id}`
Update an existing note.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Request Body:**
```json
{
  "title": "Updated Note Title",
  "content": "# Updated Content\n\nThis is the updated content..."
}
```

**Response:**
```json
{
  "id": "note-id",
  "title": "Updated Note Title",
  "content": "# Updated Content\n\nThis is the updated content...",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T01:00:00"
}
```

#### DELETE `/notes/{note_id}`
Delete a note.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "message": "Note deleted successfully"
}
```

### Utility Endpoints

#### GET `/health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "ParchMark API",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### GET `/`
Root endpoint with API information and navigation links.

**Response:**
```json
{
  "message": "Welcome to ParchMark API",
  "version": "1.0.0",
  "documentation": "/docs",
  "alternative_docs": "/redoc",
  "health_check": "/health"
}
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings in `.env`:

```env
# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-32-chars-minimum-for-security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration
DATABASE_URL=sqlite:///./parchmark.db

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

## 🌐 Frontend Integration

### CORS Configuration

The API is configured to accept requests from common frontend development servers:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite)
- `http://localhost:8080` (Docker/other)

### Authentication Flow

1. **Login:** POST to `/auth/login` with username/password
2. **Store Token:** Save the `access_token` from the response
3. **Authenticated Requests:** Include `Authorization: Bearer <token>` header
4. **Token Refresh:** Tokens expire after 30 minutes, re-authenticate as needed

### Frontend Store Integration

The API endpoints are designed to match the existing frontend store operations:

**Auth Store (`src/features/auth/store/auth.ts`):**
- `login()` → POST `/auth/login`
- `logout()` → POST `/auth/logout` + client-side token removal
- `getCurrentUser()` → GET `/auth/me`

**Notes Store (`src/features/notes/store/notes.ts`):**
- `fetchNotes()` → GET `/notes`
- `createNote()` → POST `/notes`
- `updateNote()` → PUT `/notes/{id}`
- `deleteNote()` → DELETE `/notes/{id}`

### Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 🗄️ Database

### Models

**User Model:**
- `id`: Integer (Primary Key)
- `username`: String (Unique)
- `password_hash`: String
- `created_at`: DateTime

**Note Model:**
- `id`: String (Primary Key, UUID)
- `user_id`: Integer (Foreign Key to User)
- `title`: String
- `content`: Text
- `created_at`: DateTime
- `updated_at`: DateTime

### Database Operations

**Initialize Database:**
```python
from app.database.init_db import init_database
init_database()
```

**Seed with Default Data:**
```python
from app.database.seed import seed_database
seed_database()
```

**Reset and Seed (Development):**
```bash
python -c "from app.database.seed import reset_and_seed_database; reset_and_seed_database()"
```

## 🧪 Development

### Running in Development Mode

```bash
python run.py
```

This starts the server with:
- Auto-reload enabled
- Debug logging
- CORS configured for local development
- Database auto-initialization

### Testing the API

1. **Using the Interactive Docs:**
   - Visit http://localhost:8000/docs
   - Use the "Try it out" feature for each endpoint

2. **Using curl:**
   ```bash
   # Login
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "user", "password": "password"}'
   
   # Get notes (replace TOKEN with actual token)
   curl -X GET "http://localhost:8000/notes" \
        -H "Authorization: Bearer TOKEN"
   ```

3. **Using the Frontend:**
   - Start the frontend development server
   - The existing UI should work with the backend API

## 🚀 Production Deployment

### Environment Configuration

1. **Generate a secure SECRET_KEY:**
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Update `.env` for production:**
   ```env
   SECRET_KEY=your-generated-secure-key
   DEBUG=false
   DATABASE_URL=your-production-database-url
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```

### Security Considerations

- Change the default `SECRET_KEY` in production
- Use HTTPS in production
- Configure proper CORS origins
- Consider using a production database (PostgreSQL, MySQL)
- Implement rate limiting for production use
- Set up proper logging and monitoring

## 📝 Notes

- The API automatically creates database tables on startup
- Default test data is seeded automatically for development
- All timestamps are in ISO 8601 format
- Note titles are automatically extracted from markdown H1 headers
- User passwords are securely hashed using bcrypt
- JWT tokens are stateless and contain user information

## 🤝 Contributing

When making changes to the API:

1. Update the corresponding Pydantic schemas if changing data structures
2. Update this README if adding new endpoints or changing existing ones
3. Test with both the interactive docs and the frontend application
4. Ensure CORS settings accommodate your development environment

---

For questions or issues, please refer to the interactive API documentation at `/docs` when the server is running.
