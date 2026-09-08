import httpx
import pytest

from pssapi import AsyncTransport, MemoryCache, PSSClient, TransportConfig


@pytest.mark.asyncio
async def test_raw_client_uses_pooled_transport() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text="<Response />", request=request)

    transport = AsyncTransport(
        TransportConfig(retries=0),
        transport=httpx.MockTransport(handler),
    )
    async with PSSClient(transport=transport) as pss:
        response = await pss.raw.call(
            "CharacterService",
            "ListAllCharacterDesigns2",
            params={"languageKey": "English"},
        )

    assert response.status_code == 200
    assert response.text == "<Response />"
    assert str(seen[0].url) == "https://api.pixelstarships.com/CharacterService/ListAllCharacterDesigns2?languageKey=English"


@pytest.mark.asyncio
async def test_call_can_cache_successful_responses() -> None:
    count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        return httpx.Response(200, text=str(count), request=request)

    transport = AsyncTransport(TransportConfig(retries=0), transport=httpx.MockTransport(handler))
    cache = MemoryCache()
    async with PSSClient(transport=transport, cache=cache) as pss:
        first = await pss.call("SettingService", "GetLatestVersion3", use_cache=True)
        second = await pss.call("SettingService", "GetLatestVersion3", use_cache=True)

    assert first.text == "1"
    assert second.text == "1"
    assert count == 1
