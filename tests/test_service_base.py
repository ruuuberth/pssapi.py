from types import SimpleNamespace

import pytest

from pssapi.services.service_base import CacheableServiceBase, cache_endpoint


class DummyService(CacheableServiceBase):
    def __init__(self, enable_endpoint_cache: bool = True):
        super().__init__(SimpleNamespace(), enable_endpoint_cache=enable_endpoint_cache)
        self.calls = 0
        self.version = 1

    async def get_settings(self):
        return {"Version": self.version}

    @cache_endpoint("Version")
    async def fetch(self):
        self.calls += 1
        return []


@pytest.mark.asyncio
async def test_cache_endpoint_caches_empty_list() -> None:
    service = DummyService()

    assert await service.fetch() == []
    assert await service.fetch() == []
    assert service.calls == 1


@pytest.mark.asyncio
async def test_cache_endpoint_disabled_forwards_self() -> None:
    service = DummyService(enable_endpoint_cache=False)

    assert await service.fetch() == []
    assert service.calls == 1
