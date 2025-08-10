# ParchMark API Documentation

## API Overview

The ParchMark API is built using the Phoenix framework in Elixir. It provides RESTful endpoints for managing users and their notes, forming the backend of the ParchMark note-taking application.

## Base URL

```
http://localhost:4000/api/
```

## Authentication

The API uses token-based authentication. Authentication tokens should be included in the `Authorization` header of requests:

```
Authorization: Bearer <token>
```

## Resource Endpoints

### Users

Users represent the accounts that can access the system and own notes.

#### User Model

```json
{
  "id": "uuid-string",
  "name": "User Name",
  "email": "user@example.com",
  "inserted_at": "2025-05-11T02:29:44Z",
  "updated_at": "2025-05-11T02:29:44Z"
}
```

#### GET /api/users

Retrieves a list of all users.

**Response:**
```json
{
  "data": [
    {
      "id": "uuid-string",
      "name": "User Name",
      "email": "user@example.com"
    },
    ...
  ]
}
```

#### GET /api/users/:id

Retrieves a specific user by ID.

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "name": "User Name",
    "email": "user@example.com"
  }
}
```

#### POST /api/users

Creates a new user.

**Request:**
```json
{
  "user": {
    "name": "New User",
    "email": "new.user@example.com"
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "name": "New User",
    "email": "new.user@example.com"
  }
}
```

#### PATCH/PUT /api/users/:id

Updates an existing user.

**Request:**
```json
{
  "user": {
    "name": "Updated Name"
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "name": "Updated Name",
    "email": "user@example.com"
  }
}
```

#### DELETE /api/users/:id

Deletes a user.

**Response:**
```
204 No Content
```

### Notes

Notes represent the markdown documents owned by users.

#### Note Model

```json
{
  "id": "uuid-string",
  "title": "Note Title",
  "body": "Markdown content of the note",
  "user_id": "uuid-string-of-owner",
  "inserted_at": "2025-05-11T02:30:12Z",
  "updated_at": "2025-05-11T02:30:12Z"
}
```

#### GET /api/users/:user_id/notes

Retrieves all notes for a specific user.

**Response:**
```json
{
  "data": [
    {
      "id": "uuid-string",
      "title": "Note Title",
      "body": "Markdown content of the note",
      "user_id": "uuid-string-of-owner"
    },
    ...
  ]
}
```

#### GET /api/users/:user_id/notes/:id

Retrieves a specific note.

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "title": "Note Title",
    "body": "Markdown content of the note",
    "user_id": "uuid-string-of-owner"
  }
}
```

#### POST /api/users/:user_id/notes

Creates a new note for a user.

**Request:**
```json
{
  "note": {
    "title": "New Note",
    "body": "# New Note\n\nThis is the content of the new note."
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "title": "New Note",
    "body": "# New Note\n\nThis is the content of the new note.",
    "user_id": "uuid-string-of-owner"
  }
}
```

#### PATCH/PUT /api/users/:user_id/notes/:id

Updates an existing note.

**Request:**
```json
{
  "note": {
    "title": "Updated Title",
    "body": "Updated content"
  }
}
```

**Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "title": "Updated Title",
    "body": "Updated content",
    "user_id": "uuid-string-of-owner"
  }
}
```

#### DELETE /api/users/:user_id/notes/:id

Deletes a note.

**Response:**
```
204 No Content
```

## Error Handling

The API returns standard HTTP status codes and JSON error messages:

### 400 Bad Request

Returned when the request is malformed or missing required fields.

```json
{
  "errors": {
    "detail": "Bad Request",
    "fields": {
      "field_name": ["error message"]
    }
  }
}
```

### 401 Unauthorized

Returned when authentication fails.

```json
{
  "errors": {
    "detail": "Unauthorized"
  }
}
```

### 403 Forbidden

Returned when the authenticated user doesn't have permission for the resource.

```json
{
  "errors": {
    "detail": "Forbidden"
  }
}
```

### 404 Not Found

Returned when the requested resource doesn't exist.

```json
{
  "errors": {
    "detail": "Resource not found"
  }
}
```

### 422 Unprocessable Entity

Returned when validation fails.

```json
{
  "errors": {
    "detail": "Unprocessable Entity",
    "fields": {
      "field_name": ["validation error message"]
    }
  }
}
```

### 500 Internal Server Error

Returned when an unexpected error occurs on the server.

```json
{
  "errors": {
    "detail": "Internal Server Error"
  }
}
```

## Development and Testing

### Running the API Server

```bash
# Navigate to the API directory
cd /api

# Install dependencies
mix deps.get

# Create and migrate the database
mix ecto.setup

# Start the Phoenix server
mix phx.server
```

The API will be available at http://localhost:4000/api.

### Using Docker

```bash
# Start the API with PostgreSQL using Docker
docker-compose up -d
```

### Testing

```bash
# Run tests
mix test
```

## Database Schema

The API uses PostgreSQL with the following schema:

- `users` - Stores user information
- `notes` - Stores note content with references to users

For detailed database schema, see the `DATABASE_SCHEMA.md` document.