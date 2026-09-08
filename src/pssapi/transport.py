from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import aiohttp

from .config import PssApiConfig


_RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class PssApiHttpError(RuntimeError):
    """HTTP error raised by the modern transport."""

    def __init__(self, status: int, url: str, body: str = "") -> None:
        self.status = status
        self.url = url
        self.body = body
        super().__init__(f"PSS API returned HTTP {status} for {url}")


class PssApiTransport:
    """Reusable aiohttp transport with connection pooling and bounded retries."""

    def __init__(self, config: PssApiConfig | None = None) -> None:
        self.config = config or PssApiConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> "PssApiTransport":
        if self._session is not None and not self._session.closed:
            return self
        timeout = aiohttp.ClientTimeout(total=self.config.timeout, connect=self.config.connect_timeout)
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections,
            keepalive_timeout=30,
        )
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": self.config.user_agent},
        )
        return self

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "PssApiTransport":
        return await self.start()

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> bytes:
        await self.start()
        assert self._session is not None

        for attempt in range(self.config.retries + 1):
            try:
                async with self._session.request(method.upper(), url, params=params, data=data, headers=headers) as response:
                    body = await response.read()
                    if response.status >= 400:
                        if response.status not in _RETRYABLE_STATUS or attempt >= self.config.retries:
                            raise PssApiHttpError(response.status, str(response.url), body.decode("utf-8", errors="replace"))
                    else:
                        return body
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt >= self.config.retries:
                    raise

            await asyncio.sleep(self.config.retry_backoff * (2**attempt))

        raise RuntimeError("unreachable")
