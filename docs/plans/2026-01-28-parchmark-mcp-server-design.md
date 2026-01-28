# ParchMark MCP Server Design

## Overview

MCP server enabling Claude Code/Desktop to manage ParchMark notes via CRUD operations.

**Use case:** Personal AI assistant - single user managing their own notes through LLM conversations.

## Architecture

```
┌─────────────────┐     stdio      ┌──────────────────┐     HTTPS     ┌─────────────────┐
│  Claude Code/   │◄──────────────►│  parchmark-mcp   │◄─────────────►│  ParchMark API  │
│  Desktop        │                │  (local process) │               │  (remote)       │
└─────────────────┘                └──────────────────┘               └─────────────────┘
```

- **Transport:** stdio (local subprocess)
- **Auth:** Environment variables with credentials; MCP server handles JWT token lifecycle
- **API:** Connects to existing ParchMark REST API (no direct database access)

## Distribution

**Separate GitHub repo:** `TejGandham/parchmark-mcp`

```bash
# Run directly (latest)
uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp

# Pin to version
uvx --from git+https://github.com/TejGandham/parchmark-mcp@v1.0.0 parchmark-mcp
```

## Configuration

**Environment variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `PARCHMARK_URL` | API base URL | `https://parchmark.example.com/api` |
| `PARCHMARK_USERNAME` | Account username | `myuser` |
| `PARCHMARK_PASSWORD` | Account password | `mypassword` |

**Claude Code config** (`.mcp.json`):

```json
{
  "mcpServers": {
    "parchmark": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/TejGandham/parchmark-mcp", "parchmark-mcp"],
      "env": {
        "PARCHMARK_URL": "https://parchmark.example.com/api",
        "PARCHMARK_USERNAME": "your-username",
        "PARCHMARK_PASSWORD": "your-password"
      }
    }
  }
}
```

## MCP Tools

| Tool | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `list_notes` | None | `NotesListResponse` | List all notes (without content) |
| `get_note` | `note_id: str` | `Note` | Get single note with full content |
| `create_note` | `content: str` | `Note` | Create note from markdown |
| `update_note` | `note_id: str, content: str` | `Note` | Update note content |
| `delete_note` | `note_id: str` | `DeleteResponse` | Delete note |

## Data Models

```python
from pydantic import BaseModel
from datetime import datetime

class NoteSummary(BaseModel):
    id: str
    title: str
    createdAt: datetime
    updatedAt: datetime

class Note(NoteSummary):
    content: str

class NotesListResponse(BaseModel):
    notes: list[NoteSummary]
    count: int

class DeleteResponse(BaseModel):
    success: bool
    message: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
```

## Implementation

### Package Structure

```
parchmark-mcp/
├── pyproject.toml
├── README.md
└── src/
    └── parchmark_mcp/
        ├── __init__.py
        ├── server.py       # FastMCP server, tool definitions
        ├── client.py       # ParchMark API client with auth
        └── models.py       # Pydantic models
```

### Server (`server.py`)

```python
import os
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from parchmark_mcp.client import ParchMarkClient
from parchmark_mcp.models import Note, NotesListResponse, DeleteResponse

mcp = FastMCP("parchmark")

_client: ParchMarkClient | None = None

def get_client() -> ParchMarkClient:
    """Singleton client to reuse authentication tokens."""
    global _client
    if _client is None:
        _client = ParchMarkClient(
            base_url=os.environ["PARCHMARK_URL"],
            username=os.environ["PARCHMARK_USERNAME"],
            password=os.environ["PARCHMARK_PASSWORD"],
        )
    return _client

@mcp.tool()
async def list_notes() -> NotesListResponse:
    """List all notes for the authenticated user."""
    client = get_client()
    notes = await client.list_notes()
    return NotesListResponse(notes=notes, count=len(notes))

@mcp.tool()
async def get_note(note_id: str) -> Note:
    """Get a specific note by ID with full content."""
    client = get_client()
    return await client.get_note(note_id)

@mcp.tool()
async def create_note(content: str) -> Note:
    """Create a new note with markdown content."""
    client = get_client()
    return await client.create_note(content)

@mcp.tool()
async def update_note(note_id: str, content: str) -> Note:
    """Update an existing note's content."""
    client = get_client()
    return await client.update_note(note_id, content)

@mcp.tool()
async def delete_note(note_id: str) -> DeleteResponse:
    """Delete a note by ID."""
    client = get_client()
    return await client.delete_note(note_id)
```

### Client (`client.py`)

```python
from datetime import datetime, UTC
import httpx
from fastmcp.exceptions import ToolError
from parchmark_mcp.models import Note, NoteSummary, TokenPair

class ParchMarkClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expiry: datetime | None = None
        self._http = httpx.AsyncClient()

    async def _login(self) -> None:
        """Authenticate and store tokens."""
        response = await self._http.post(
            f"{self.base_url}/auth/login",
            data={"username": self.username, "password": self.password},
        )
        if response.status_code != 200:
            raise ToolError("Authentication failed - check credentials")

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        # Token expires in 30 min, refresh at 25 min
        self.token_expiry = datetime.now(UTC).replace(
            minute=datetime.now(UTC).minute + 25
        )

    async def _refresh(self) -> None:
        """Refresh access token using refresh token."""
        response = await self._http.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        if response.status_code != 200:
            # Refresh failed, re-login
            await self._login()
            return

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.token_expiry = datetime.now(UTC).replace(
            minute=datetime.now(UTC).minute + 25
        )

    async def _ensure_authenticated(self) -> None:
        """Login or refresh token as needed."""
        if self.access_token is None:
            await self._login()
        elif self.token_expiry and datetime.now(UTC) >= self.token_expiry:
            await self._refresh()

    async def _request(
        self, method: str, path: str, **kwargs: dict
    ) -> dict[str, str | int | list[dict[str, str]]]:
        """Make authenticated request with error handling."""
        await self._ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self._http.request(
            method, f"{self.base_url}{path}", headers=headers, **kwargs
        )

        if response.status_code == 401:
            raise ToolError("Authentication failed - session expired")
        if response.status_code == 404:
            raise ToolError("Note not found")
        if response.status_code >= 400:
            raise ToolError(f"API error: {response.status_code}")

        return response.json()

    async def list_notes(self) -> list[NoteSummary]:
        """Get all notes (without content)."""
        data = await self._request("GET", "/notes/")
        return [NoteSummary.model_validate(note) for note in data]

    async def get_note(self, note_id: str) -> Note:
        """Get a specific note with content."""
        data = await self._request("GET", f"/notes/{note_id}")
        return Note.model_validate(data)

    async def create_note(self, content: str) -> Note:
        """Create a new note."""
        # Backend requires title field but extracts from H1 anyway
        data = await self._request(
            "POST", "/notes/", json={"title": "placeholder", "content": content}
        )
        return Note.model_validate(data)

    async def update_note(self, note_id: str, content: str) -> Note:
        """Update a note's content."""
        data = await self._request(
            "PUT", f"/notes/{note_id}", json={"content": content}
        )
        return Note.model_validate(data)

    async def delete_note(self, note_id: str) -> dict[str, bool | str]:
        """Delete a note."""
        await self._request("DELETE", f"/notes/{note_id}")
        return {"success": True, "message": f"Note {note_id} deleted"}
```

### Package Config (`pyproject.toml`)

```toml
[project]
name = "parchmark-mcp"
version = "1.0.0"
description = "MCP server for ParchMark notes"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0,<3",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.scripts]
parchmark-mcp = "parchmark_mcp.server:mcp.run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   MCP Tool  │     │   Client    │     │ ParchMark   │
│   Called    │     │  Singleton  │     │    API      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ get_client()      │                   │
       │──────────────────►│                   │
       │                   │                   │
       │                   │ _ensure_authenticated()
       │                   │───────┐           │
       │                   │       │ check     │
       │                   │◄──────┘ expiry    │
       │                   │                   │
       │                   │ POST /auth/login  │
       │                   │──────────────────►│ (if no token)
       │                   │   tokens          │
       │                   │◄──────────────────│
       │                   │                   │
       │                   │ POST /auth/refresh│
       │                   │──────────────────►│ (if expired)
       │                   │   new token       │
       │                   │◄──────────────────│
       │                   │                   │
       │                   │ GET/POST/etc      │
       │                   │──────────────────►│
       │   result          │   response        │
       │◄──────────────────│◄──────────────────│
       │                   │                   │
```

## Known Limitations

1. **`list_notes` payload overhead** - Backend returns full content; client strips to summary. Future: add `?summary=true` backend param.
2. **No pagination** - `GET /notes` returns all notes. Future: add limit/offset to backend and MCP tool.
3. **Title field workaround** - Backend schema requires `title` but ignores it. Sending placeholder until schema is relaxed.

## Future Enhancements

- Add `search_notes(query: str)` tool with backend full-text search
- Add pagination to `list_notes`
- Add `?summary=true` backend endpoint for efficient listing
- Consider making backend `NoteCreate.title` optional

## Validation

Design reviewed by:
- Gemini (codereviewer role) - confirmed critical issues
- Codex (codereviewer role) - confirmed and added pagination observation
- FastMCP documentation - confirmed error handling patterns

## References

- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
