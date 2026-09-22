from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

DEFAULT_ENDPOINT = "https://mcp.aidoo.ai/mcp"
HEALTH_PATH = "/health"
KEY_PREFIXES = ("aid_live_", "aid_test_")
TRANSPORTS = ("http", "sse")

ENV_API_KEY = "AIDOO_API_KEY"
ENV_ENDPOINT = "AIDOO_MCP_URL"
ENV_TRANSPORT = "AIDOO_MCP_TRANSPORT"
ENV_TIMEOUT = "AIDOO_MCP_TIMEOUT"

DEFAULT_TIMEOUT = 60.0
DEFAULT_RETRIES = 3


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    endpoint: str
    api_key: str
    transport: str
    timeout: float
    retries: int

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": user_agent(),
        }

    @property
    def health_url(self) -> str:
        parts = urlparse(self.endpoint)
        return urlunparse((parts.scheme, parts.netloc, HEALTH_PATH, "", "", ""))

    def describe(self) -> str:
        return f"{self.endpoint} (transport={self.transport}, key={mask_key(self.api_key)})"


def user_agent() -> str:
    from . import __version__

    return f"aidoo-mcp/{__version__}"


def mask_key(api_key: str) -> str:
    if not api_key:
        return "<empty>"
    if len(api_key) <= 12:
        return "*" * len(api_key)
    return f"{api_key[:9]}...{api_key[-4:]}"


def detect_transport(endpoint: str) -> str:
    return "sse" if urlparse(endpoint).path.rstrip("/").endswith("/sse") else "http"


def normalize_endpoint(endpoint: str, transport: str) -> str:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        raise ConfigError("The MCP endpoint is empty")

    if "://" not in endpoint:
        endpoint = f"https://{endpoint}"

    parts = urlparse(endpoint)
    if parts.scheme not in ("http", "https"):
        raise ConfigError(f"Unsupported scheme '{parts.scheme}://' for {endpoint}")
    if not parts.netloc:
        raise ConfigError(f"Missing host in endpoint '{endpoint}'")

    path = parts.path.rstrip("/")
    wanted = "/sse" if transport == "sse" else "/mcp"

    if path in ("", "/"):
        path = wanted
    elif path.endswith("/sse") and transport == "http":
        path = f"{path[: -len('/sse')]}/mcp"
    elif path.endswith("/mcp") and transport == "sse":
        path = f"{path[: -len('/mcp')]}/sse"

    return urlunparse((parts.scheme, parts.netloc, path, "", "", ""))


def resolve_timeout(raw: str | float | None) -> float:
    if raw in (None, ""):
        return DEFAULT_TIMEOUT
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid timeout '{raw}': expected a number of seconds") from exc
    if timeout <= 0:
        raise ConfigError("Timeout must be greater than zero")
    return timeout


def looks_like_api_key(api_key: str) -> bool:
    return api_key.startswith(KEY_PREFIXES)


def load_config(
    api_key: str | None = None,
    endpoint: str | None = None,
    transport: str | None = None,
    timeout: str | float | None = None,
    retries: int | None = None,
    env: dict[str, str] | None = None,
) -> Config:
    env = os.environ if env is None else env

    key = (api_key or env.get(ENV_API_KEY) or "").strip()
    if not key:
        raise ConfigError(
            "No API key found. Pass --api-key or set the AIDOO_API_KEY environment "
            "variable. Generate a key from the API keys page of your Aidoo workspace."
        )

    raw_endpoint = (endpoint or env.get(ENV_ENDPOINT) or DEFAULT_ENDPOINT).strip()
    chosen = (transport or env.get(ENV_TRANSPORT) or detect_transport(raw_endpoint)).strip().lower()
    if chosen not in TRANSPORTS:
        raise ConfigError(f"Unknown transport '{chosen}': expected one of {', '.join(TRANSPORTS)}")

    return Config(
        endpoint=normalize_endpoint(raw_endpoint, chosen),
        api_key=key,
        transport=chosen,
        timeout=resolve_timeout(timeout if timeout is not None else env.get(ENV_TIMEOUT)),
        retries=DEFAULT_RETRIES if retries is None else max(0, int(retries)),
    )
