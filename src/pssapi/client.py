from . import client_base as _client_base
from . import entities as _entities
from . import enums as _enums
from . import utils as _utils
from .cache import MemoryCache
from .config import PssApiConfig
from .raw.client import RawApiClient
from .transport import PssApiTransport


class PssApiClient(_client_base.PssApiClientBase):
    """Pixel Starships API client with legacy services and a modern raw transport."""

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
        self._modern_transport = PssApiTransport(self._modern_config)
        self._modern_cache = cache
        self._raw_client = RawApiClient(
            self._modern_transport,
            production_server=production_server,
            config=self._modern_config,
            cache=cache,
        )

    @property
    def raw(self) -> RawApiClient:
        """Generic low-level client for endpoints without a typed wrapper yet."""
        return self._raw_client

    @property
    def transport(self) -> PssApiTransport:
        """Reusable pooled HTTP transport used by the modern raw client."""
        return self._modern_transport

    async def close(self) -> None:
        """Release pooled HTTP connections created by the modern transport."""
        await self._modern_transport.close()

    async def __aenter__(self) -> "PssApiClient":
        await self._modern_transport.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _update_services(self):
        super()._update_services()

    async def device_login(self, device_key: str, checksum_key: str) -> _entities.UserLogin:
        """Shortcut to self.user_service.device_login(), calculating the required information.

        Args:
            device_key (str): A UUID representing a "device".
            checksum_key (str): A secret required to generate a checksum for the login.

        Returns:
            _entities.UserLogin: An object containing information on the last user logged on the device with the provided `device_key` and an access token for that user.
        """
        client_date_time = _utils.get_utc_now()
        checksum = self.user_service.utils.create_device_login_checksum(device_key, self.device_type, client_date_time, checksum_key)
        return await self.user_service.device_login(checksum, client_date_time, device_key, self.device_type)
