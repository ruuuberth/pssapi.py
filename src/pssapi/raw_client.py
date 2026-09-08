from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urljoin

import httpx

from .cache import Cache, make_cache_key
from .transport import AsyncTransport


@dataclass(frozen=True, slots=True)
class RawResponse:
    """Lossless HTTP response wrapper for endpoints not yet modeled by pssapi."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes
    url: str

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", self.url)
            response = httpx.Response(
                self.status_code,
                headers=self.headers,
                content=self.content,
                request=request,
            )
            raise httpx.HTTPStatusError(
                f"PSS API returned HTTP {self.status_code}",
                request=request,
                response=response,
            )


class RawApiClient:
    """Call arbitrary Pixel Starships API service methods directly."""

    def __init__(
        self,
        transport: AsyncTransport,
        production_server: str = "api.pixelstarships.com",
        cache: Cache | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        self.transport = transport
        self.production_server = production_server
        self.cache = cache
        self.cache_ttl = cache_ttl

    def _url(self, service: str, method: str) -> str:
        path = f"{service.strip('/')}/{method.strip('/')}"
        return urljoin(f"https://{self.production_server}/", path)

    async def call(
        self,
        service: str,
        method: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        content: bytes | str | None = None,
        http_method: str = "GET",
        headers: Mapping[str, str] | None = None,
        use_cache: bool = False,
        ttl: float | None = None,
    ) -> RawResponse:
        normalized_method = http_method.upper()
        url = self._url(service, method)
        cache_key = make_cache_key(
            normalized_method,
            url,
            params or {},
            json,
            content,
            headers or {},
        )

        if use_cache and normalized_method == "GET" and self.cache is not None:
            cached = await self.cache.get(cache_key)
            if isinstance(cached, RawResponse):
                return cached

        response = await self.transport.request(
            normalized_method,
            url,
            params=dict(params or {}),
            json=json,
            content=content,
            headers=dict(headers or {}),
        )
        result = RawResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
        )

        if (
            use_cache
            and normalized_method == "GET"
            and self.cache is not None
            and result.status_code < 400
        ):
            await self.cache.set(
                cache_key,
                result,
                self.cache_ttl if ttl is None else ttl,
            )

        return result
