from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache import Cache, MemoryCache, make_cache_key
from .raw_client import RawApiClient, RawResponse
from .transport import AsyncTransport, TransportConfig


@dataclass(frozen=True, slots=True)
class PssClientConfig:
    production_server: str = "api.pixelstarships.com"
    device_type: str = "Android"
    language_key: str = "English"
    cache_ttl: float | None = 300.0


class PSSClient:
    """Modern async Pixel Starships API client.

    This layer is intentionally independent from generated service wrappers. It
    provides a pooled transport, caching, and a raw escape hatch so newly found
    endpoints can be consumed before typed wrappers are generated.
    """

    def __init__(
        self,
        *,
        config: PssClientConfig | None = None,
        transport: AsyncTransport | None = None,
        cache: Cache | None = None,
        transport_config: TransportConfig | None = None,
    ) -> None:
        self.config = config or PssClientConfig()
        self.transport = transport or AsyncTransport(transport_config)
        self.cache = cache or MemoryCache()
        self.raw = RawApiClient(self.transport, self.config.production_server)

    async def call(
        self,
        service: str,
        method: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        content: bytes | str | None = None,
        http_method: str = "GET",
        use_cache: bool = False,
        ttl: float | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> RawResponse:
        key = make_cache_key(service, method, http_method, params or {}, json, content, headers or {})
        if use_cache:
            cached = await self.cache.get(key)
            if isinstance(cached, RawResponse):
                return cached

        response = await self.raw.call(
            service,
            method,
            params=params,
            json=json,
            content=content,
            http_method=http_method,
            headers=headers,
        )
        if use_cache and response.status_code < 400:
            await self.cache.set(key, response, self.config.cache_ttl if ttl is None else ttl)
        return response

    async def aclose(self) -> None:
        await self.transport.aclose()

    async def __aenter__(self) -> PSSClient:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()
