from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from .config import Config


class UpstreamError(RuntimeError):
    pass


def _load_http_client():
    try:
        from mcp.client.streamable_http import streamable_http_client

        return streamable_http_client, True
    except ImportError:
        pass
    try:
        from mcp.client.streamable_http import streamablehttp_client

        return streamablehttp_client, False
    except ImportError as exc:
        raise UpstreamError(
            "The installed 'mcp' package does not provide a streamable HTTP client. "
            "Upgrade it with: pip install --upgrade mcp"
        ) from exc


def _new_async_client(config: Config):
    try:
        import httpx2 as httpx
    except ImportError:
        import httpx

    return httpx.AsyncClient(
        headers=config.headers,
        timeout=httpx.Timeout(config.timeout, read=config.timeout, connect=15.0),
        follow_redirects=True,
    )


def _streams(value: Any) -> tuple[Any, Any]:
    read, write = value[0], value[1]
    return read, write


@asynccontextmanager
async def open_upstream(config: Config) -> AsyncIterator[tuple[Any, Any]]:
    if config.transport == "sse":
        from mcp.client.sse import sse_client

        async with sse_client(
            config.endpoint,
            headers=config.headers,
            timeout=config.timeout,
            sse_read_timeout=max(config.timeout, 300.0),
        ) as value:
            yield _streams(value)
        return

    client_factory, modern = _load_http_client()

    if modern:
        async with _new_async_client(config) as http_client:
            async with client_factory(config.endpoint, http_client=http_client) as value:
                yield _streams(value)
        return

    async with client_factory(
        config.endpoint,
        headers=config.headers,
        timeout=config.timeout,
        sse_read_timeout=max(config.timeout, 300.0),
    ) as value:
        yield _streams(value)


async def check_health(config: Config) -> tuple[bool, str]:
    try:
        import httpx2 as httpx
    except ImportError:
        import httpx

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            response = await client.get(config.health_url)
        except Exception as exc:
            return False, f"{config.health_url} is unreachable ({exc.__class__.__name__})"
        if response.status_code != 200:
            return False, f"{config.health_url} returned HTTP {response.status_code}"
        return True, f"{config.health_url} is reachable"
