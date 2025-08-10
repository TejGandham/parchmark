# ParchMark Database Schema

## Overview

ParchMark uses PostgreSQL as its database system. The schema is designed to support the core functionality of user management and note storage with relationships between users and their notes.

## Database Tables

### users

The `users` table stores information about registered users in the application.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  inserted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

**Fields:**
- `id`: UUID primary key (binary_id in Ecto)
- `name`: User's display name
- `email`: User's email address for identification
- `inserted_at`: Timestamp of record creation
- `updated_at`: Timestamp of last record update

**Indexes:**
- Primary key on `id`

### notes

The `notes` table stores the markdown notes that belong to users.

```sql
CREATE TABLE notes (
  id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  user_id UUID REFERENCES users(id),
  inserted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX notes_user_id_index ON notes(user_id);
```

**Fields:**
- `id`: UUID primary key (binary_id in Ecto)
- `title`: Title of the note
- `body`: Markdown content of the note
- `user_id`: Foreign key reference to the owner in the users table
- `inserted_at`: Timestamp of record creation
- `updated_at`: Timestamp of last record update

**Indexes:**
- Primary key on `id`
- Index on `user_id` for efficient lookups of a user's notes

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│   users     │       │    notes    │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ name        │       │ title       │
│ email       │       │ body        │
│ inserted_at │       │ user_id (FK)│
│ updated_at  │       │ inserted_at │
└─────────────┘       │ updated_at  │
       │              └─────────────┘
       │                     ▲
       │                     │
       └─────────────────────┘
          1                n
```

## Relationships

- One user can have many notes (one-to-many relationship)
- Each note belongs to exactly one user

## Data Types

- **UUID (binary_id)**: Used for all primary and foreign keys to ensure global uniqueness
- **VARCHAR**: Used for string fields like name, email, and title
- **TEXT**: Used for note body content to accommodate variable-length markdown text
- **TIMESTAMP WITH TIME ZONE**: Used for all timestamp fields to ensure proper time tracking across time zones

## Constraints

- Primary key constraints on `id` fields
- Foreign key constraint on `notes.user_id` referencing `users.id`
- Non-nullable constraints on essential fields
- Index on `notes.user_id` for query performance

## Migration Files

The database schema is created and maintained through Ecto migrations:

1. **Create Users Migration (`20250511022944_create_users.exs`)**
   - Creates the users table with id, name, and email fields
   - Adds timestamp fields

2. **Create Notes Migration (`20250511023012_create_notes.exs`)**
   - Creates the notes table with id, title, body, and user_id fields
   - Sets up foreign key reference to users table
   - Creates index on user_id field
   - Adds timestamp fields

## Database Initialization and Migration

```bash
# Create and initialize the database
mix ecto.create

# Run all migrations
mix ecto.migrate

# Reset database (drop, create, migrate)
mix ecto.reset

# Run specific migration
mix ecto.migrate --step 1
```

## Schema Models

The database tables are represented by Ecto schema models:

### User Schema (`lib/api/accounts/user.ex`)

```elixir
defmodule Api.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset

  @primary_key {:id, :binary_id, autogenerate: true}
  @foreign_key_type :binary_id
  schema "users" do
    field :name, :string
    field :email, :string

    timestamps(type: :utc_datetime)
  end

  def changeset(user, attrs) do
    user
    |> cast(attrs, [:name, :email])
    |> validate_required([:name, :email])
  end
end
```

### Note Schema (`lib/api/accounts/note.ex`)

```elixir
defmodule Api.Accounts.Note do
  use Ecto.Schema
  import Ecto.Changeset

  @primary_key {:id, :binary_id, autogenerate: true}
  @foreign_key_type :binary_id
  schema "notes" do
    field :title, :string
    field :body, :string
    field :user_id, :binary_id

    timestamps(type: :utc_datetime)
  end

  def changeset(note, attrs) do
    note
    |> cast(attrs, [:title, :body])
    |> validate_required([:title, :body])
  end
end
```

## Future Schema Extensions

Planned additions to the schema include:

1. **Tags Table**
   - Allow notes to be categorized with tags
   - Many-to-many relationship with notes

2. **Sharing Table**
   - Enable note sharing between users
   - Track access permissions

3. **Version History**
   - Track changes to notes over time
   - Allow reverting to previous versions