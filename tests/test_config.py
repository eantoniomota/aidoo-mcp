import pytest

from aidoo_mcp.config import (
    DEFAULT_ENDPOINT,
    ConfigError,
    detect_transport,
    load_config,
    looks_like_api_key,
    mask_key,
    normalize_endpoint,
    resolve_timeout,
)

KEY = "aid_live_1234567890abcdef"


def test_defaults_to_the_hosted_endpoint():
    config = load_config(env={"AIDOO_API_KEY": KEY})
    assert config.endpoint == DEFAULT_ENDPOINT
    assert config.transport == "http"
    assert config.headers["Authorization"] == f"Bearer {KEY}"


def test_reads_the_endpoint_from_the_environment():
    config = load_config(env={"AIDOO_API_KEY": KEY, "AIDOO_MCP_URL": "https://mcp.example.com/sse"})
    assert config.transport == "sse"
    assert config.endpoint == "https://mcp.example.com/sse"


def test_missing_key_is_reported():
    with pytest.raises(ConfigError, match="No API key"):
        load_config(env={})


def test_unknown_transport_is_rejected():
    with pytest.raises(ConfigError, match="Unknown transport"):
        load_config(transport="grpc", env={"AIDOO_API_KEY": KEY})


@pytest.mark.parametrize(
    ("endpoint", "transport", "expected"),
    [
        ("https://mcp.aidoo.ai", "http", "https://mcp.aidoo.ai/mcp"),
        ("https://mcp.aidoo.ai/", "sse", "https://mcp.aidoo.ai/sse"),
        ("mcp.aidoo.ai", "http", "https://mcp.aidoo.ai/mcp"),
        ("https://mcp.aidoo.ai/sse", "http", "https://mcp.aidoo.ai/mcp"),
        ("https://mcp.aidoo.ai/mcp", "sse", "https://mcp.aidoo.ai/sse"),
        ("https://mcp.aidoo.ai/mcp-2", "http", "https://mcp.aidoo.ai/mcp-2"),
        ("http://localhost:8000/mcp", "http", "http://localhost:8000/mcp"),
    ],
)
def test_endpoint_normalization(endpoint, transport, expected):
    assert normalize_endpoint(endpoint, transport) == expected


@pytest.mark.parametrize("endpoint", ["", "ftp://mcp.aidoo.ai", "https:///mcp"])
def test_invalid_endpoints_are_rejected(endpoint):
    with pytest.raises(ConfigError):
        normalize_endpoint(endpoint, "http")


def test_transport_detection():
    assert detect_transport("https://mcp.aidoo.ai/sse") == "sse"
    assert detect_transport("https://mcp.aidoo.ai/mcp") == "http"
    assert detect_transport("https://mcp.aidoo.ai") == "http"


def test_health_url_ignores_the_endpoint_path():
    config = load_config(endpoint="https://mcp.aidoo.ai/mcp-3", env={"AIDOO_API_KEY": KEY})
    assert config.health_url == "https://mcp.aidoo.ai/health"


def test_key_masking_never_leaks_the_secret():
    masked = mask_key(KEY)
    assert KEY not in masked
    assert masked.startswith("aid_live_")
    assert masked.endswith(KEY[-4:])
    assert mask_key("short") == "*****"
    assert mask_key("") == "<empty>"


def test_describe_masks_the_key():
    config = load_config(env={"AIDOO_API_KEY": KEY})
    assert KEY not in config.describe()


def test_key_prefix_detection():
    assert looks_like_api_key(KEY)
    assert not looks_like_api_key("sk-somethingelse")


@pytest.mark.parametrize(("raw", "expected"), [(None, 60.0), ("", 60.0), ("15", 15.0), (2.5, 2.5)])
def test_timeout_resolution(raw, expected):
    assert resolve_timeout(raw) == expected


@pytest.mark.parametrize("raw", ["abc", "0", "-4"])
def test_invalid_timeouts_are_rejected(raw):
    with pytest.raises(ConfigError):
        resolve_timeout(raw)


def test_explicit_arguments_win_over_the_environment():
    config = load_config(
        api_key="aid_live_explicit_key_value",
        endpoint="https://self.hosted/mcp",
        retries=0,
        env={"AIDOO_API_KEY": KEY, "AIDOO_MCP_URL": "https://mcp.aidoo.ai/mcp"},
    )
    assert config.api_key == "aid_live_explicit_key_value"
    assert config.endpoint == "https://self.hosted/mcp"
    assert config.retries == 0
