from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urljoin

import httpx

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
            raise httpx.HTTPStatusError(
                f"PSS API returned HTTP {self.status_code}",
                request=httpx.Request("GET", self.url),
                response=httpx.Response(self.status_code, headers=self.headers, content=self.content, request=httpx.Request("GET", self.url)),
            )


class RawApiClient:
    """Call arbitrary Pixel Starships API service methods directly."""

    def __init__(self, transport: AsyncTransport, production_server: str = "api.pixelstarships.com") -> None:
        self.transport = transport
        self.production_server = production_server

    def _url(self, service: str, method: str) -> str:
        service = service.strip("/")
        method = method.strip("/")
        if "/" in service:
            path = f"{service}/{method}"
        else:
            path = f"{service}/{method}"
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
    ) -> RawResponse:
        response = await self.transport.request(
            http_method,
            self._url(service, method),
            params=dict(params or {}),
            json=json,
            content=content,
            headers=dict(headers or {}),
        )
        return RawResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
        )
