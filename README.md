# aidoo-mcp

Connect any MCP client to your Odoo ERP through [Aidoo](https://aidoo.ai).

`aidoo-mcp` is a small stdio bridge. It takes an Aidoo API key, opens an authenticated
session against the hosted Aidoo MCP server, and relays the Model Context Protocol
messages in both directions. Your assistant then queries, creates and updates Odoo
records in plain language, under the permissions carried by the key.

[![PyPI](https://img.shields.io/pypi/v/aidoo-mcp.svg)](https://pypi.org/project/aidoo-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/aidoo-mcp.svg)](https://pypi.org/project/aidoo-mcp/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Why a bridge

The Aidoo MCP server is hosted at `https://mcp.aidoo.ai`, and clients that support
remote connectors with OAuth or custom headers can reach it directly, with nothing to
install. Many MCP clients still speak stdio only, or offer no way to set an
`Authorization` header. This bridge fills that gap: one command, no local server,
no Odoo credentials on your machine.

```
MCP client  <--stdio-->  aidoo-mcp  <--HTTPS-->  Aidoo  <--XML-RPC-->  Odoo
```

The bridge is transparent. It never rewrites payloads, so every tool your workspace
exposes is available the moment Aidoo ships it, with no update needed here.

## Requirements

- Python 3.10 or newer
- An [Aidoo account](https://app.aidoo.ai/register) with an Odoo connection
- An Aidoo API key, prefixed `aid_live_`, created from the API keys page of your workspace

## Install

Run it without installing anything, with [uv](https://docs.astral.sh/uv/):

```bash
uvx aidoo-mcp --check
```

Or install it:

```bash
pipx install aidoo-mcp
# or
pip install aidoo-mcp
```

## Check your setup

```bash
export AIDOO_API_KEY=aid_live_your_key_here
aidoo-mcp --check
```

The command verifies that the endpoint answers, performs the MCP handshake and prints
the tools your key grants:

```
[aidoo-mcp] https://mcp.aidoo.ai/health is reachable
[aidoo-mcp] authenticated with https://mcp.aidoo.ai/mcp (transport=http, key=aid_live_...cdef)
[aidoo-mcp] 8 tools available: aidoo_context, aidoo_create, aidoo_print, aidoo_query, ...
```

## Configure your client

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows:

```json
{
  "mcpServers": {
    "aidoo": {
      "command": "uvx",
      "args": ["aidoo-mcp"],
      "env": { "AIDOO_API_KEY": "aid_live_your_key_here" }
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "aidoo": {
      "command": "uvx",
      "args": ["aidoo-mcp"],
      "env": { "AIDOO_API_KEY": "aid_live_your_key_here" }
    }
  }
}
```

### Windsurf

`~/.codeium/windsurf/mcp_config.json`, same block as Cursor.

### VS Code

`.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "aidoo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["aidoo-mcp"],
      "env": { "AIDOO_API_KEY": "aid_live_your_key_here" }
    }
  }
}
```

### Any other stdio client

Point it at the `aidoo-mcp` executable and pass the key through the environment. If the
client cannot set environment variables, use the flag instead:

```bash
aidoo-mcp --api-key aid_live_your_key_here
```

Cursor, Windsurf and any client that does accept custom headers can also skip the
bridge entirely and target `https://mcp.aidoo.ai/sse` with an `Authorization` header.
See the [Aidoo documentation](https://aidoo.ai/docs).

## Usage

```
aidoo-mcp [--api-key KEY] [--url URL] [--transport {http,sse}]
          [--timeout SECONDS] [--retries N] [--check] [--quiet]
```

| Option | Environment variable | Default |
| --- | --- | --- |
| `--api-key` | `AIDOO_API_KEY` | required |
| `--url` | `AIDOO_MCP_URL` | `https://mcp.aidoo.ai/mcp` |
| `--transport` | `AIDOO_MCP_TRANSPORT` | inferred from the URL path |
| `--timeout` | `AIDOO_MCP_TIMEOUT` | `60` |
| `--retries` | | `3` |

Logs go to stderr, so they never interfere with the protocol stream on stdout. Exit
code `2` means a configuration problem, `1` a connection that could not be established.

## Ask your assistant

```
List the five quotations I sent last week that are still pending.
Create a contact for Martin Dupont at Dupont SA, martin@dupont.fr.
Generate the PDF of invoice INV/2026/0042.
```

## Security

- The key is read from the environment or the command line and sent as a bearer token
  over HTTPS. It is masked in every log line.
- Odoo credentials stay in Aidoo. The bridge never sees them, and never talks to Odoo.
- Each key carries its own permissions, and every call runs under the Odoo access
  rules of the linked user. Grant only what the assistant needs.
- Use one key per person, never a shared key, and revoke it from the dashboard if in doubt.
- Report a vulnerability privately: see [SECURITY.md](SECURITY.md).

## Troubleshooting

**`No API key found`** The `AIDOO_API_KEY` variable did not reach the process. Client
configuration files often ignore your shell profile, so set the key in the `env` block
shown above.

**Handshake fails with 401** The key was revoked, or its MCP permissions are disabled.
Check it on the API keys page of your workspace.

**The tool list is shorter than expected** Tools follow the permissions of the key.
Grant the missing ones, then restart your client.

**Nothing happens in the client** Restart the client completely after editing its
configuration, then look at its MCP logs. `aidoo-mcp --check` tells you within seconds
whether the problem is on your side or ours.

**A corporate network blocks the connection** The bridge needs outbound HTTPS on port
443 to `mcp.aidoo.ai`. Try `--transport sse` if an intermediate proxy mishandles
streamable HTTP.

## Development

```bash
uv venv
uv pip install -e ".[dev]"
uv run pytest
uv run ruff check .
```

## License

MIT. See [LICENSE](LICENSE).
