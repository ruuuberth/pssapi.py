from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class TransportConfig:
    timeout: float = 30.0
    max_connections: int = 20
    max_keepalive_connections: int = 10
    keepalive_expiry: float = 30.0
    retries: int = 2
    retry_backoff: float = 0.5
    retry_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})
    verify: bool = True


class AsyncTransport:
    """Reusable HTTP transport with connection pooling and bounded retries."""

    def __init__(self, config: TransportConfig | None = None, **client_kwargs: Any) -> None:
        self.config = config or TransportConfig()
        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
            keepalive_expiry=self.config.keepalive_expiry,
        )
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            limits=limits,
            verify=self.config.verify,
            **client_kwargs,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        method = method.upper()
        retryable_method = method in {"GET", "HEAD", "OPTIONS"}
        attempts = self.config.retries + 1 if retryable_method else 1

        for attempt in range(attempts):
            try:
                response = await self._client.request(method, url, **kwargs)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteError):
                if attempt + 1 >= attempts:
                    raise
                await self._sleep(attempt)
                continue

            if response.status_code not in self.config.retry_statuses or attempt + 1 >= attempts:
                return response

            retry_after = response.headers.get("Retry-After")
            await self._sleep(attempt, retry_after)

        raise RuntimeError("HTTP retry loop terminated unexpectedly")

    async def _sleep(self, attempt: int, retry_after: str | None = None) -> None:
        if retry_after:
            try:
                delay = max(0.0, float(retry_after))
            except ValueError:
                delay = self.config.retry_backoff * (2**attempt)
        else:
            delay = self.config.retry_backoff * (2**attempt)
        await asyncio.sleep(delay)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()
