# Publishing to the MCP Registry

`server.json` describes the Aidoo server for the [official MCP Registry](https://registry.modelcontextprotocol.io).
The registry stores metadata only, and the entry is what makes Aidoo discoverable from
the clients and directories that read the registry.

The name `ai.aidoo/aidoo` is a domain namespace, so publishing requires proving control
of `aidoo.ai` with a DNS TXT record. Keep `key.pem` out of the repository and in the
password manager: it signs every future publication.

## One time: create the signing key and the DNS record

```bash
openssl genpkey -algorithm Ed25519 -out key.pem
PUBLIC_KEY="$(openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | base64)"
echo "aidoo.ai. IN TXT \"v=MCPv1; k=ed25519; p=${PUBLIC_KEY}\""
```

On macOS the system `openssl` is LibreSSL and cannot generate Ed25519 keys. Use
`/opt/homebrew/opt/openssl@3/bin/openssl` instead.

Add the printed value as a TXT record on the **apex** of `aidoo.ai` in Cloudflare, not
under a selector such as `_mcp-auth`. Wait for propagation, then check it:

```bash
dig +short TXT aidoo.ai | grep MCPv1
```

## Every release

```bash
mcp-publisher validate
mcp-publisher login dns --domain aidoo.ai --private-key "$(openssl pkey -in key.pem -noout -text | grep -A3 priv | tail -n +2 | tr -d ' :\n')"
mcp-publisher publish
```

Bump `version` in `server.json` before each publication: the registry rejects a version
that already exists.

## Adding the PyPI package

Once `aidoo-mcp` is on PyPI, add a `packages` block so clients can install the bridge
from the registry entry. PyPI ownership is proven by shipping the server name in the
package metadata, so `pyproject.toml` needs this before the release that follows:

```toml
[project]
keywords = ["mcp-name:ai.aidoo/aidoo"]
```

Then add to `server.json`:

```json
"packages": [
  {
    "registryType": "pypi",
    "identifier": "aidoo-mcp",
    "version": "0.1.0",
    "transport": { "type": "stdio" },
    "environmentVariables": [
      {
        "name": "AIDOO_API_KEY",
        "description": "Aidoo API key, prefixed aid_live_",
        "isRequired": true,
        "isSecret": true,
        "format": "string"
      }
    ]
  }
]
```
