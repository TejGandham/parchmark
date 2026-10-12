# AGENTS.md

Guidance for AI assistants working with the parchmark-mcp codebase.

## Project Overview

**parchmark-mcp** - MCP server enabling Claude Code/Desktop to manage ParchMark notes.

| Layer | Stack |
|-------|-------|
| Server | FastMCP 2.x, Python 3.11+ |
| HTTP | httpx (async) |
| Models | Pydantic 2.x (strict typing) |
| Quality | ruff, pyright (strict), pytest |

## Directory Structure

```
parchmark-mcp/
├── src/parchmark_mcp/
│   ├── __init__.py      # Package version
│   ├── server.py        # FastMCP server, MCP tools, singleton client
│   ├── client.py        # ParchMarkClient with JWT auth
│   └── models.py        # Pydantic models (Note, NoteSummary, etc.)
├── tests/
│   ├── test_models.py   # Model validation tests
│   ├── test_client.py   # Client tests with respx mocking
│   └── test_server.py   # Server/tool tests with mocked client
└── pyproject.toml       # Package config, ruff, pyright settings
```

## Commands

All commands run from project root.

```bash
# Development
uv sync --all-extras         # Install all dependencies
uv run parchmark-mcp         # Run MCP server (needs env vars)

# Testing
uv run pytest tests/ -v      # Run all tests
uv run pytest tests/test_client.py -v  # Run specific test file

# Quality
uv run ruff check src/ tests/         # Lint
uv run ruff check src/ tests/ --fix   # Lint with autofix
uv run ruff format src/ tests/        # Format
uv run pyright src/ tests/            # Type check (strict)

# Pre-commit
uv run pre-commit run --all-files     # Run all hooks manually
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PARCHMARK_URL` | Yes | API base URL (e.g., `https://notes.example.com/api`) |
| `PARCHMARK_USERNAME` | Yes | ParchMark username |
| `PARCHMARK_PASSWORD` | Yes | ParchMark password |

## Code Patterns

### Singleton Client

```python
# server.py - client is created once and reused
_client: ParchMarkClient | None = None

def get_client() -> ParchMarkClient:
    global _client
    if _client is None:
        # Initialize from env vars
        _client = ParchMarkClient(...)
    return _client
```

### FastMCP Tools

```python
@mcp.tool()
async def tool_name(param: str) -> ResponseModel:
    """Docstring becomes tool description."""
    client = get_client()
    return await client.method(param)
```

### Error Handling

Use `ToolError` from `fastmcp.exceptions` for all client-facing errors:

```python
from fastmcp.exceptions import ToolError

if response.status_code == 404:
    raise ToolError("Note not found")
```

### Type Annotations

Pyright strict mode - all functions need full type annotations:

```python
async def method(self, note_id: str) -> Note:  # Return type required
    ...
```

## Testing Patterns

### Mocking HTTP (respx)

```python
@pytest.fixture
def mock_login(respx_mock: respx.MockRouter) -> respx.Route:
    return respx_mock.post("https://api.example.com/auth/login").mock(
        return_value=Response(200, json={...})
    )
```

### Mocking Client in Server Tests

```python
@pytest.fixture
def mock_client() -> Generator[AsyncMock, None, None]:
    with patch.object(server_module, "_client", None):
        with patch.object(server_module, "ParchMarkClient") as mock:
            yield AsyncMock()
```

### Private Member Access in Tests

```python
# Use pyright ignore for intentional private access
await client._login()  # pyright: ignore[reportPrivateUsage]
server_module._client = None  # pyright: ignore[reportPrivateUsage]
```

## Gotchas

### Login Uses JSON, Not Form Data

```python
# Correct - ParchMark API expects JSON
response = await self._http.post(url, json={"username": ..., "password": ...})

# Wrong - will fail with 422
response = await self._http.post(url, data={"username": ..., "password": ...})
```

### Token Expiry

- Access tokens expire in 30 minutes
- Client refreshes at 25 minutes (5 min buffer)
- If refresh fails, re-login automatically

### Pyright Strict Mode

- All parameters and returns need type annotations
- Use `str | None` not `Optional[str]`
- Use `# pyright: ignore[reportXxx]` sparingly for intentional violations

### Pre-commit Hooks

Hooks run automatically on commit:
1. `ruff` - linting with autofix
2. `ruff-format` - formatting
3. `pyright` - type checking

If hooks fail, fix issues and re-commit.

## Adding New Tools

1. Add method to `ParchMarkClient` in `client.py`
2. Add tool wrapper in `server.py` with `@mcp.tool()` decorator
3. Add tests in `test_client.py` (with respx) and `test_server.py` (with mocked client)
4. Run `uv run pytest tests/ -v` and `uv run pyright src/ tests/`

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --ff-only   # if it fails (diverged), git merge origin/main — never rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
