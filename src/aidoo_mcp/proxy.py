from __future__ import annotations

import sys
from typing import Any

import anyio

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup


class ProxyError(RuntimeError):
    pass


def first_error(error: BaseException) -> BaseException:
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    return error


async def relay(source: Any, destination: Any, cancel_scope: anyio.CancelScope, label: str) -> None:
    try:
        async for message in source:
            if isinstance(message, Exception):
                raise ProxyError(f"{label} stream failed: {message}")
            await destination.send(message)
    except (anyio.ClosedResourceError, anyio.BrokenResourceError):
        pass
    finally:
        cancel_scope.cancel()


async def run_proxy(local: tuple[Any, Any], upstream: tuple[Any, Any]) -> None:
    local_read, local_write = local
    upstream_read, upstream_write = upstream

    try:
        async with anyio.create_task_group() as task_group:
            scope = task_group.cancel_scope
            task_group.start_soon(relay, local_read, upstream_write, scope, "client")
            task_group.start_soon(relay, upstream_read, local_write, scope, "server")
    except BaseExceptionGroup as group:
        raise first_error(group) from None
