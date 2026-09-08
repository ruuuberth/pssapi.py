import pytest

from pssapi.cache import MemoryCache
from pssapi.config import PssApiConfig
from pssapi.raw.client import RawApiClient
from pssapi.transport import PssApiTransport


class FakeTransport:
    def __init__(self):
        self.calls = 0

    async def request(self, method, url, *, params=None, data=None, headers=None):
        self.calls += 1
        return b'{"ok": true, "value": 42}'


@pytest.mark.asyncio
async def test_raw_client_decodes_json_and_caches_gets():
    transport = FakeTransport()
    cache = MemoryCache(default_ttl=60)
    raw = RawApiClient(transport, production_server="example.invalid", cache=cache)

    first = await raw.call("CharacterService", "ListAllCharacterDesigns2", params={"limit": 10})
    second = await raw.call("CharacterService", "ListAllCharacterDesigns2", params={"limit": 10})

    assert first == {"ok": True, "value": 42}
    assert second == first
    assert transport.calls == 1


@pytest.mark.asyncio
async def test_raw_client_normalizes_datetime_params():
    from datetime import datetime, timezone

    transport = FakeTransport()
    raw = RawApiClient(transport, production_server="example.invalid", cache=None)
    await raw.call("SettingService", "GetLatestVersion3", params={"when": datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)})

    assert transport.calls == 1


def test_config_environment(monkeypatch):
    monkeypatch.setenv("PSSAPI_TIMEOUT", "12.5")
    monkeypatch.setenv("PSSAPI_RETRIES", "4")
    monkeypatch.setenv("PSSAPI_CACHE_TTL", "off")

    config = PssApiConfig.from_env()

    assert config.timeout == 12.5
    assert config.retries == 4
    assert config.cache_ttl is None


@pytest.mark.asyncio
async def test_transport_can_be_started_and_closed():
    transport = PssApiTransport(PssApiConfig(timeout=1))
    await transport.start()
    assert transport._session is not None
    await transport.close()
    assert transport._session.closed
