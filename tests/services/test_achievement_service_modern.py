from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.achievement_service import AchievementService


@pytest.mark.asyncio
async def test_list_achievement_designs_uses_modern_raw_client(monkeypatch) -> None:
    raw = SimpleNamespace(
        call=AsyncMock(
            return_value=RawResponse(
                status_code=200,
                headers={},
                content=b"<AchievementDesigns />",
                url="https://api.pixelstarships.com/AchievementService/ListAchievementDesigns2",
            )
        )
    )
    client = SimpleNamespace(raw=raw, language_key="English")
    service = AchievementService(client)
    service.get_settings = AsyncMock(return_value={"AchievementDesignVersion": 1})
    parser = AsyncMock(return_value=[])
    monkeypatch.setattr("pssapi.services.achievement_service._service_base.parse_entity_list", parser)

    result = await service.list_achievement_designs()

    assert result == []
    raw.call.assert_awaited_once_with(
        "AchievementService",
        "ListAchievementDesigns2",
        params={"languageKey": "English"},
        use_cache=False,
    )
    parser.assert_awaited_once()
