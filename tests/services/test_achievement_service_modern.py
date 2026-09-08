from types import SimpleNamespace

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.achievement_service import AchievementService


@pytest.mark.asyncio
async def test_list_achievement_designs_uses_modern_raw_client(monkeypatch) -> None:
    raw = SimpleNamespace(
        call=SimpleNamespace(
            __call__=None,
        )
    )
    calls: list[tuple[str, str, dict, bool]] = []

    async def call(service: str, method: str, *, params: dict, use_cache: bool):
        calls.append((service, method, params, use_cache))
        return RawResponse(
            status_code=200,
            headers={},
            content=b"<AchievementDesigns />",
            url="https://api.pixelstarships.com/AchievementService/ListAchievementDesigns2",
        )

    raw.call = call
    client = SimpleNamespace(raw=raw, language_key="English")
    service = AchievementService(client)
    service.get_settings = lambda: None
    monkeypatch.setattr(
        "pssapi.services.achievement_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    result = await service.list_achievement_designs(design_version=12)

    assert result == []
    assert calls == [
        (
            "AchievementService",
            "ListAchievementDesigns2",
            {"languageKey": "English", "designVersion": 12},
            False,
        )
    ]
