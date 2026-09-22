# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-22

### Added

- registry ownership marker in the package keywords, so the PyPI package can be
  attached to the `ai.aidoo/aidoo` entry of the MCP Registry

### Changed

- contact address in the package metadata is now the public support mailbox

## [0.1.0] - 2026-09-22

### Added

- stdio bridge to the hosted Aidoo MCP server, with bearer authentication
- streamable HTTP and SSE upstream transports, selected automatically from the URL
- `--check` command that verifies the endpoint, the handshake and the API key
- configuration through `AIDOO_API_KEY`, `AIDOO_MCP_URL`, `AIDOO_MCP_TRANSPORT`
  and `AIDOO_MCP_TIMEOUT`, each overridable on the command line
- retries with backoff while the session is being established
