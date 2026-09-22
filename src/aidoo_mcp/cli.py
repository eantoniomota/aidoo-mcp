from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import anyio

from . import __version__
from .config import (
    DEFAULT_ENDPOINT,
    Config,
    ConfigError,
    load_config,
    looks_like_api_key,
)
from .proxy import ProxyError, run_proxy
from .transport import UpstreamError, check_health, open_upstream

RETRY_DELAYS = (1.0, 3.0, 8.0)
PROBE_TOOL = "aidoo_context"


def log(message: str) -> None:
    print(f"[aidoo-mcp] {message}", file=sys.stderr, flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aidoo-mcp",
        description=(
            "Bridge a local MCP client to the Aidoo MCP server, so any assistant that "
            "speaks stdio can reach your Odoo through Aidoo."
        ),
    )
    parser.add_argument("--api-key", help="Aidoo API key (defaults to $AIDOO_API_KEY)")
    parser.add_argument(
        "--url",
        dest="endpoint",
        help=f"Aidoo MCP endpoint (defaults to $AIDOO_MCP_URL, then {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--transport",
        choices=("http", "sse"),
        help="Upstream transport (defaults to the one matching the endpoint path)",
    )
    parser.add_argument("--timeout", help="Request timeout in seconds (default: 60)")
    parser.add_argument(
        "--retries",
        type=int,
        help="Connection attempts before giving up (default: 3)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the endpoint and the API key, then exit",
    )
    parser.add_argument("--quiet", action="store_true", help="Only report errors")
    parser.add_argument("--version", action="version", version=f"aidoo-mcp {__version__}")
    return parser


async def serve(config: Config, quiet: bool) -> int:
    from mcp.server.stdio import stdio_server

    last_error: Exception | None = None

    async with stdio_server() as local:
        for attempt in range(config.retries + 1):
            try:
                async with open_upstream(config) as upstream:
                    if not quiet:
                        log(f"connected to {config.describe()}")
                    await run_proxy(local, upstream)
                    return 0
            except (ProxyError, UpstreamError, OSError) as exc:
                last_error = exc
            except Exception as exc:
                last_error = exc

            if attempt < config.retries:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                log(f"connection failed ({last_error}), retrying in {delay:.0f}s")
                await anyio.sleep(delay)

    log(f"giving up after {config.retries + 1} attempts: {last_error}")
    return 1


async def probe(config: Config) -> int:
    reachable, detail = await check_health(config)
    log(detail)
    if not reachable:
        return 1

    from mcp import ClientSession

    try:
        async with open_upstream(config) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                identity = await session.call_tool(PROBE_TOOL, {})
    except Exception as exc:
        log(f"handshake failed: {exc}")
        return 1

    log(f"connected to {config.describe()}")

    detail = _first_text(identity)
    if getattr(identity, "isError", False) or getattr(identity, "is_error", False):
        log(f"the API key was rejected: {detail}")
        log("check that the key is active and that its MCP permissions are enabled")
        return 1

    names = sorted(tool.name for tool in tools.tools)
    log(f"API key accepted, {len(names)} tools available: {', '.join(names) if names else 'none'}")
    return 0


def _first_text(result: object) -> str:
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            return text.strip().splitlines()[0]
    return "no detail returned"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = load_config(
            api_key=args.api_key,
            endpoint=args.endpoint,
            transport=args.transport,
            timeout=args.timeout,
            retries=args.retries,
        )
    except ConfigError as exc:
        log(str(exc))
        return 2

    if not looks_like_api_key(config.api_key) and not args.quiet:
        log("warning: the key does not start with 'aid_live_', it may be rejected")

    try:
        if args.check:
            return anyio.run(probe, config)
        return anyio.run(serve, config, args.quiet)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
