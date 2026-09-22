# Contributing

Issues and pull requests are welcome.

## Getting started

```bash
git clone https://github.com/eantoniomota/aidoo-mcp.git
cd aidoo-mcp
uv sync
uv run pytest
uv run ruff check .
```

## Ground rules

- Keep the bridge transparent. It relays protocol messages and must not interpret,
  rewrite or cache them. Tool behaviour belongs to the Aidoo server.
- Every change that touches configuration or the relay comes with a test.
- Run `ruff check .` and `ruff format .` before opening a pull request.
- Never commit an API key, a log containing one, or a real Odoo hostname.

## Reporting a bug

Include your Python version, the output of `aidoo-mcp --check`, the name of your MCP
client, and the relevant lines from its MCP log. Redact your API key.

For anything related to the Aidoo platform itself rather than this bridge, use the
support channels at [aidoo.ai](https://aidoo.ai/contact).
