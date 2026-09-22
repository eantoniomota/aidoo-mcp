# Publishing to the MCP Registry

`server.json` describes the Aidoo server for the [official MCP Registry](https://registry.modelcontextprotocol.io).
The registry stores metadata only, and the entry is what makes Aidoo discoverable from
the clients and directories that read the registry.

The server is published as **`ai.aidoo/aidoo`**, the reverse DNS form of `aidoo.ai`.
That namespace is proven with a TXT record on the apex of the domain, signed by
`key.pem`. The key never leaves the machine and is excluded from the repository: keep
it in the password manager, because regenerating it means changing the DNS record.

## Every release

```bash
mcp-publisher validate
mcp-publisher login dns --domain aidoo.ai \
  --private-key "$(openssl pkey -in key.pem -noout -text | grep -A3 priv | tail -n +2 | tr -d ' :\n')"
mcp-publisher publish
```

Bump `version` in `server.json` first: the registry rejects a version that already
exists. On macOS the system `openssl` is LibreSSL and cannot read Ed25519 keys, so use
`/opt/homebrew/opt/openssl@3/bin/openssl`.

## The DNS record

```
aidoo.ai.  IN  TXT  "v=MCPv1; k=ed25519; p=<public key>"
```

It sits on the **apex**, next to the SPF and Google records, never under a selector such
as `_mcp-auth`. Regenerate the value with:

```bash
openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | base64
```

## Retiring an entry

A remote URL belongs to a single server entry, so republishing under a different name
fails with `remote URL ... is already used` until the previous entry is retired:

```bash
mcp-publisher login github
mcp-publisher status --status deleted --all-versions <old server name>
```

## Adding the PyPI package

Once `aidoo-mcp` is on PyPI, add a `packages` block so clients can install the bridge
from the registry entry. PyPI ownership is proven through the package metadata, so
`pyproject.toml` needs this before the release that follows:

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
