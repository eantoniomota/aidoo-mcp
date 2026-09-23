# aidoo-mcp (npm)

Stdio bridge connecting any MCP client to your Odoo ERP through [Aidoo](https://aidoo.ai), packaged for Node so it runs with a single `npx` command, no Python required.

## Use it

```
npx aidoo-mcp --check
```

Add it to a client's MCP config (Claude Desktop, Cursor, Windsurf, VS Code, ...):

```json
{
  "mcpServers": {
    "aidoo": {
      "command": "npx",
      "args": ["-y", "aidoo-mcp"],
      "env": { "AIDOO_API_KEY": "aid_live_your_key_here" }
    }
  }
}
```

## Options

```
aidoo-mcp [--api-key KEY] [--url URL] [--transport {http,sse}]
          [--timeout SECONDS] [--retries N] [--check] [--quiet]
```

| Option | Environment variable | Default |
|---|---|---|
| `--api-key` | `AIDOO_API_KEY` | required |
| `--url` | `AIDOO_MCP_URL` | `https://mcp.aidoo.ai/mcp` |
| `--transport` | `AIDOO_MCP_TRANSPORT` | inferred from the URL path |
| `--timeout` | `AIDOO_MCP_TIMEOUT` | 60 |

Full documentation, security notes and troubleshooting: see the [project README](../README.md) and [aidoo.ai/docs](https://aidoo.ai/docs).

## Develop

```
npm install
npm run build
node dist/cli.js --check
```

## License

MIT. See [LICENSE](../LICENSE).
