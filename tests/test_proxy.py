import anyio
import pytest

from aidoo_mcp.proxy import ProxyError, run_proxy


def channel():
    return anyio.create_memory_object_stream(max_buffer_size=8)


async def test_messages_flow_in_both_directions():
    client_send, client_source = channel()
    upstream_sink, upstream_received = channel()
    upstream_send, upstream_source = channel()
    client_sink, client_received = channel()

    await client_send.send({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    await upstream_send.send({"jsonrpc": "2.0", "id": 1, "result": {"tools": []}})
    await client_send.aclose()
    await upstream_send.aclose()

    await run_proxy((client_source, client_sink), (upstream_source, upstream_sink))

    assert await upstream_received.receive() == {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    assert await client_received.receive() == {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}


async def test_an_upstream_failure_stops_the_proxy():
    client_send, client_source = channel()
    upstream_sink, _ = channel()
    upstream_send, upstream_source = channel()
    client_sink, _ = channel()

    await upstream_send.send(ConnectionResetError("upstream closed"))

    with anyio.fail_after(2), pytest.raises(ProxyError, match="upstream closed"):
        await run_proxy((client_source, client_sink), (upstream_source, upstream_sink))

    await client_send.aclose()


async def test_a_closed_client_ends_the_session_cleanly():
    client_send, client_source = channel()
    upstream_sink, _ = channel()
    _, upstream_source = channel()
    client_sink, _ = channel()

    await client_send.aclose()

    with anyio.fail_after(2):
        await run_proxy((client_source, client_sink), (upstream_source, upstream_sink))
