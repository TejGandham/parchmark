# Installation Guide

This guide covers installing parchmark-mcp for Claude Code, Claude Desktop, and opencode.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A ParchMark account and a personal API token for it (see [Getting a token](#getting-a-token))

## Environment Variables

All installation methods require these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `PARCHMARK_URL` | Yes | API base URL (e.g., `https://notes.example.com/api`) |
| `PARCHMARK_TOKEN` | Yes | Personal API token, sent as `Authorization: Bearer` on every request |

`PARCHMARK_USERNAME` and `PARCHMARK_PASSWORD` are no longer read. If you are upgrading from a
username/password setup, replace them with `PARCHMARK_TOKEN` in your MCP client config.

### Getting a token

Create a personal API token with `POST /api/auth/tokens` while signed in. The response holds the
plaintext `token` once, so copy it then; ParchMark stores only a hash of it.

```bash
curl -s -X POST https://your-instance/api/auth/tokens \
  -H "Authorization: Bearer <your access token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "claude-code"}'
```

`GET /api/auth/tokens` lists your tokens (name and id, never the plaintext), and
`DELETE /api/auth/tokens/{token_id}` revokes one.

---

## Claude Code

### Option 1: CLI Command (Recommended)

Run this single command to add the MCP server:

```bash
claude mcp add parchmark -s user \
  -e "PARCHMARK_URL=https://your-instance/api" \
  -e "PARCHMARK_TOKEN=pmat_your-token" \
  -- uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp
```

**Flags explained:**
- `-s user` - Install at user scope (available in all projects)
- `-e` - Set environment variables

### Option 2: Manual Configuration

Edit `~/.claude/mcp.json` (user scope) or `.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "parchmark": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/TejGandham/parchmark-mcp",
        "parchmark-mcp"
      ],
      "env": {
        "PARCHMARK_URL": "https://your-instance/api",
        "PARCHMARK_TOKEN": "pmat_your-token"
      }
    }
  }
}
```

### Verify Installation

```bash
claude mcp list
```

You should see `parchmark` in the list of configured servers.

---

## Claude Desktop

Edit the Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the parchmark server:

```json
{
  "mcpServers": {
    "parchmark": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/TejGandham/parchmark-mcp",
        "parchmark-mcp"
      ],
      "env": {
        "PARCHMARK_URL": "https://your-instance/api",
        "PARCHMARK_TOKEN": "pmat_your-token"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

---

## opencode

[opencode](https://github.com/sst/opencode) supports MCP servers via its configuration file.

### Option 1: JSON Configuration

Edit `~/.config/opencode/config.json` or `opencode.json` in your project root:

```json
{
  "mcp": {
    "parchmark": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/TejGandham/parchmark-mcp",
        "parchmark-mcp"
      ],
      "env": {
        "PARCHMARK_URL": "https://your-instance/api",
        "PARCHMARK_TOKEN": "pmat_your-token"
      }
    }
  }
}
```

### Option 2: TOML Configuration

Edit `~/.config/opencode/config.toml` or `opencode.toml` in your project root:

```toml
[mcp.parchmark]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/TejGandham/parchmark-mcp",
  "parchmark-mcp"
]

[mcp.parchmark.env]
PARCHMARK_URL = "https://your-instance/api"
PARCHMARK_TOKEN = "pmat_your-token"
```

---

## Alternative: Local Installation

If you prefer to install the package locally instead of using `uvx`:

### Install with pip

```bash
pip install git+https://github.com/TejGandham/parchmark-mcp
```

### Install with uv

```bash
uv pip install git+https://github.com/TejGandham/parchmark-mcp
```

Then update your configuration to use the installed command directly:

```json
{
  "mcpServers": {
    "parchmark": {
      "command": "parchmark-mcp",
      "env": {
        "PARCHMARK_URL": "https://your-instance/api",
        "PARCHMARK_TOKEN": "pmat_your-token"
      }
    }
  }
}
```

---

## Upgrading

> **Caveat — `uvx` pins to a cached commit.** The recommended install uses an **unpinned** git URL
> (`uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp`). `uvx` resolves that to
> the default-branch HEAD **once**, caches the built environment, and reuses it on every launch. It
> does **not** re-pull newer commits automatically — so the server stays on whatever commit was first
> resolved until you explicitly refresh the cache.

To upgrade to the latest version:

```bash
# Re-fetch the default-branch HEAD and rebuild the cached environment
uvx --refresh --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp

# …or clear just this package's cache so the next launch re-resolves from scratch
uv cache clean parchmark-mcp
```

Then **restart your MCP client** (Claude Code, Claude Desktop, opencode). MCP servers are spawned
when the client starts, so a running client keeps using the old process until it relaunches the
server — the refresh alone does not hot-swap an already-running session.

**Pin to a specific version (optional).** To make upgrades explicit and reproducible instead of
tracking the moving default branch, pin a tag or commit in your config's `args`:

```jsonc
"args": ["--from", "git+https://github.com/TejGandham/parchmark-mcp@<tag-or-commit>", "parchmark-mcp"]
```

If you used the **Local Installation** method instead of `uvx`, upgrade with the same installer:

```bash
pip install --upgrade --force-reinstall git+https://github.com/TejGandham/parchmark-mcp
# or
uv pip install --upgrade git+https://github.com/TejGandham/parchmark-mcp
```

---

## Troubleshooting

### Changes or fixes not taking effect (stuck on an old version)

`uvx` is reusing a cached build of an older commit. Refresh the cache and restart your MCP client —
see [Upgrading](#upgrading) above:

```bash
uvx --refresh --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp
```

### Server not starting

1. Verify environment variables are set correctly
2. Test the server manually:
   ```bash
   PARCHMARK_URL=https://your-instance/api \
   PARCHMARK_TOKEN=pmat_your-token \
   uvx --from git+https://github.com/TejGandham/parchmark-mcp parchmark-mcp
   ```

### Authentication errors

- Check that `PARCHMARK_TOKEN` is set to the full token, including the `pmat_` prefix
- A revoked token returns 401; create a new one (see [Getting a token](#getting-a-token))
- Ensure the URL points to the API endpoint (usually ends with `/api`)

### uvx not found

Install uv first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Permission denied

Ensure the MCP server has permission to execute. On Unix systems:

```bash
chmod +x $(which parchmark-mcp)
```

---

## Available Tools

Once installed, you'll have access to these tools:

| Tool | Description |
|------|-------------|
| `list_notes` | List all notes (metadata only) |
| `get_note` | Get a specific note with full content |
| `create_note` | Create a new note from markdown |
| `update_note` | Update an existing note |
| `delete_note` | Delete a note |
