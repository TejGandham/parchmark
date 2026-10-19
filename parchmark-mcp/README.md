# parchmark-mcp

MCP server for managing ParchMark notes and publishing artifacts via Claude Code/Desktop.

## Installation

```bash
# Run directly
uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp

# Or install
pip install git+https://github.com/TejGandham/parchmark-mcp
```

## Upgrading

> **Caveat:** the `uvx --from git+…` install above is **unpinned**, but `uvx` caches the resolved
> git commit and reuses it — it does **not** re-pull new commits on its own. New releases will not
> appear until you bust the cache:
>
> ```bash
> # Re-fetch the default-branch HEAD and rebuild the cached environment
> uvx --refresh --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp
> # …or just clear this package's cache so the next launch re-resolves
> uv cache clean parchmark-mcp
> ```
>
> Then **restart your MCP client** (Claude Code/Desktop, opencode) so it relaunches the server — a
> running client keeps the old process until restarted. See [docs/INSTALL.md](docs/INSTALL.md#upgrading)
> for details and the `pip`/`uv pip` equivalents.

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PARCHMARK_URL` | API base URL | `https://parchmark.example.com/api` |
| `PARCHMARK_TOKEN` | Personal API token, sent as `Authorization: Bearer` | `pmat_...` |

The server never sees your password. `PARCHMARK_USERNAME` and `PARCHMARK_PASSWORD` are no longer read.

### Getting a token

Create a personal API token with `POST /api/auth/tokens` while signed in. The response holds the
plaintext `token` once, so copy it then:

```bash
curl -s -X POST https://parchmark.example.com/api/auth/tokens \
  -H "Authorization: Bearer <your access token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "claude-code"}'
```

Revoke a token with `DELETE /api/auth/tokens/{token_id}`; the server then gets a 401 and reports
an authentication error.

### Claude Code Setup

```bash
claude mcp add parchmark -s user \
  -e "PARCHMARK_URL=https://your-instance/api" \
  -e "PARCHMARK_TOKEN=pmat_your-token" \
  -- uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp
```

Or manually add to `.mcp.json`:

```json
{
  "mcpServers": {
    "parchmark": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/TejGandham/parchmark-mcp", "parchmark-mcp"],
      "env": {
        "PARCHMARK_URL": "https://parchmark.example.com/api",
        "PARCHMARK_TOKEN": "pmat_your-token"
      }
    }
  }
}
```

## Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_notes` | None | List all notes (metadata only) |
| `get_note` | `note_id` | Get a specific note with full content |
| `create_note` | `content` | Create a new note from markdown |
| `update_note` | `note_id`, `content` | Update an existing note |
| `delete_note` | `note_id` | Delete a note |
| `publish_artifact` | `title`, `content`, `content_type` | Publish an HTML, Markdown or SVG document as a new private artifact (version 1) |
| `update_artifact` | `artifact_id`, `content`, `content_type` | Publish a new version of an artifact and make it current |
| `list_artifacts` | None | List your artifacts, newest first |
| `get_artifact` | `artifact_id` | Get one artifact |
| `set_artifact_visibility` | `artifact_id`, `visibility` | Set `private` (only you) or `unlisted` (anyone with the link); no other value is accepted |

`content_type` is one of `html`, `markdown` or `svg`. Every artifact tool returns the artifact
`id`, `title`, current `version` number, `content_type`, `visibility` and `url`. The `url` is the
share link the API returns, of the form `<content origin>/a/<slug>`; the server passes it through
unchanged. A new artifact is private and still has a `url`, but the link opens for others only after
`set_artifact_visibility` makes it `unlisted`.

## Architecture

```
parchmark-mcp/
├── src/parchmark_mcp/
│   ├── __init__.py      # Package version
│   ├── server.py        # FastMCP server & tools
│   ├── client.py        # ParchMark API client
│   └── models.py        # Pydantic models
├── tests/
│   ├── test_models.py   # Model tests
│   ├── test_client.py   # Client tests (mocked)
│   └── test_server.py   # Server tests (mocked)
└── pyproject.toml       # Package config
```

## Development

```bash
# Clone and install
git clone https://github.com/TejGandham/parchmark-mcp
cd parchmark-mcp
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Lint & format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run pyright src/ tests/
```

## Quality Gates

Pre-commit hooks enforce:
- `ruff` - Linting with autofix
- `ruff-format` - Code formatting
- `pyright --strict` - Type checking

## Tech Stack

- **FastMCP** - Python MCP framework
- **httpx** - Async HTTP client
- **Pydantic** - Data validation & models
- **pyright** - Static type checking (strict mode)
- **ruff** - Linting & formatting
- **pytest** - Testing with async support

## License

MIT
