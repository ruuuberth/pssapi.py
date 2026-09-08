from __future__ import annotations

import base64
import json
import zlib
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from ..cache import MemoryCache
from ..config import PssApiConfig
from ..constants import DATETIME_FORMAT_ISO
from ..transport import PssApiTransport


class RawApiClient:
    """Low-level escape hatch for any reachable Pixel Starships endpoint.

    It intentionally returns decoded JSON/XML/text instead of forcing callers
    to wait for a generated typed service.
    """

    def __init__(
        self,
        transport: PssApiTransport,
        production_server: str | None = None,
        config: PssApiConfig | None = None,
        cache: MemoryCache | None = None,
    ) -> None:
        self.transport = transport
        self.production_server = production_server or (config.production_server if config else None) or "api.pixelstarships.com"
        self.cache = cache

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.strftime(DATETIME_FORMAT_ISO)
        return value

    @staticmethod
    def _cache_key(method: str, url: str, params: dict[str, Any] | None, body: str | bytes | None) -> str:
        normalized = sorted((key, str(value)) for key, value in (params or {}).items())
        body_text = body.decode() if isinstance(body, bytes) else body or ""
        return f"{method.upper()} {url}?{urlencode(normalized)}#{body_text}"

    async def call(
        self,
        service: str,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        body: str | bytes | None = None,
        response_gzipped: bool = False,
        http_method: str = "GET",
        cache_ttl: float | None = None,
    ) -> Any:
        path = f"{service.strip('/')}/{method.strip('/')}"
        url = f"https://{self.production_server}/{path}"
        normalized_params = {k: self._normalize(v) for k, v in (params or {}).items() if v is not None}
        key = self._cache_key(http_method, url, normalized_params, body)

        if self.cache is not None and http_method.upper() == "GET":
            cached = await self.cache.get(key)
            if cached is not None:
                return cached

        data = await self.transport.request(http_method, url, params=normalized_params, data=body)
        if response_gzipped:
            try:
                data = zlib.decompress(base64.b64decode(data), zlib.MAX_WBITS | 32)
            except Exception:
                pass

        text = data.decode("utf-8")
        result: Any = text
        stripped = text.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                pass

        if self.cache is not None and http_method.upper() == "GET":
            await self.cache.set(key, result, ttl=cache_ttl)
        return result
