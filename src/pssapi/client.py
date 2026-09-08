from __future__ import annotations

from . import client_base as _client_base
from . import entities as _entities
from . import enums as _enums
from . import utils as _utils
from .cache import MemoryCache
from .config import PssApiConfig
from .raw_client import RawApiClient
from .transport import AsyncTransport, TransportConfig


class PssApiClient(_client_base.PssApiClientBase):
    """Pixel Starships API client with legacy services and the modern transport."""

    def __init__(
        self,
        device_type: "_enums.DeviceType" = None,
        language_key: "_enums.LanguageKey" = None,
        production_server: str = None,
        *,
        config: PssApiConfig | None = None,
        cache: MemoryCache | None = None,
    ):
        super().__init__(device_type, language_key, production_server)
        self._modern_config = config or PssApiConfig.from_env()
        transport_config = TransportConfig(
            timeout=self._modern_config.timeout,
            max_connections=self._modern_config.max_connections,
            max_keepalive_connections=self._modern_config.max_keepalive_connections,
            retries=self._modern_config.retries,
            retry_backoff=self._modern_config.retry_backoff,
        )
        self._modern_transport = AsyncTransport(transport_config)
        self._modern_cache = cache if cache is not None else MemoryCache()
        self._raw_client = RawApiClient(
            self._modern_transport,
            production_server=production_server
            or self._modern_config.production_server
            or "api.pixelstarships.com",
            cache=self._modern_cache,
            cache_ttl=self._modern_config.cache_ttl,
        )

    @property
    def raw(self) -> RawApiClient:
        """Generic low-level client for endpoints without a typed wrapper yet."""
        return self._raw_client

    @property
    def transport(self) -> AsyncTransport:
        """Reusable pooled HTTP transport used by the modern raw client."""
        return self._modern_transport

    async def close(self) -> None:
        """Release pooled HTTP connections created by the modern transport."""
        await self._modern_transport.aclose()

    async def __aenter__(self) -> "PssApiClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _update_services(self):
        super()._update_services()

    async def device_login(self, device_key: str, checksum_key: str) -> _entities.UserLogin:
        """Shortcut to self.user_service.device_login(), calculating the required information."""
        client_date_time = _utils.get_utc_now()
        checksum = self.user_service.utils.create_device_login_checksum(
            device_key,
            self.device_type,
            client_date_time,
            checksum_key,
        )
        return await self.user_service.device_login(
            checksum,
            client_date_time,
            device_key,
            self.device_type,
        )
