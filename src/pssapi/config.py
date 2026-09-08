from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class PssApiConfig:
    """Runtime configuration for the modern PSS API transport.

    Values can be supplied explicitly or loaded from ``PSSAPI_*`` environment
    variables. Explicit arguments always win over environment variables.
    """

    production_server: str | None = None
    timeout: float = 30.0
    connect_timeout: float = 10.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    retries: int = 2
    retry_backoff: float = 0.25
    cache_ttl: float | None = 60.0
    user_agent: str = "pssapi/modern"

    @classmethod
    def from_env(cls) -> "PssApiConfig":
        def number(name: str, default: str, cast):
            value = os.getenv(name, default)
            try:
                return cast(value)
            except ValueError as exc:
                raise ValueError(f"Invalid PSSAPI_{name}: {value!r}") from exc

        cache_raw = os.getenv("PSSAPI_CACHE_TTL", "60").strip().lower()
        cache_ttl = None if cache_raw in {"", "none", "null", "off"} else number("CACHE_TTL", "60", float)

        return cls(
            production_server=os.getenv("PSSAPI_PRODUCTION_SERVER") or None,
            timeout=number("TIMEOUT", "30", float),
            connect_timeout=number("CONNECT_TIMEOUT", "10", float),
            max_connections=number("MAX_CONNECTIONS", "100", int),
            max_keepalive_connections=number("MAX_KEEPALIVE_CONNECTIONS", "20", int),
            retries=number("RETRIES", "2", int),
            retry_backoff=number("RETRY_BACKOFF", "0.25", float),
            cache_ttl=cache_ttl,
            user_agent=os.getenv("PSSAPI_USER_AGENT", "pssapi/modern"),
        )
