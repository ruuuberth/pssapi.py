from types import SimpleNamespace

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.setting_service import SettingService


class FakeRawClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict, bool]] = []

    async def call(self, service: str, method: str, *, params: dict, use_cache: bool):
        self.calls.append((service, method, params, use_cache))
        return RawResponse(200, {}, b"<Response />", f"https://api.pixelstarships.com/{service}/{method}")


@pytest.fixture
def service() -> tuple[SettingService, FakeRawClient]:
    raw = FakeRawClient()
    client = SimpleNamespace(raw=raw, language_key="English")
    return SettingService(client), raw


@pytest.mark.asyncio
async def test_get_latest_version_uses_modern_raw_client(service, monkeypatch) -> None:
    setting_service, raw = service
    monkeypatch.setattr(
        "pssapi.services.setting_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [object()],
    )

    result = await setting_service.get_latest_version("Android")

    assert result is not None
    assert raw.calls == [
        (
            "SettingService",
            "GetLatestVersion4",
            {"deviceType": "Android", "languageKey": "English"},
            False,
        )
    ]


@pytest.mark.asyncio
async def test_list_all_news_designs_uses_modern_raw_client(service, monkeypatch) -> None:
    setting_service, raw = service
    setting_service.get_settings = _settings("NewsDesignVersion", 42)
    monkeypatch.setattr(
        "pssapi.services.setting_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    result = await setting_service.list_all_news_designs(design_version=7)

    assert result == []
    assert raw.calls == [
        (
            "SettingService",
            "ListAllNewsDesigns",
            {"clientDateTime": None, "languageKey": "English", "designVersion": 7},
            False,
        )
    ]


def _settings(version_name: str, version: int):
    async def get_settings():
        return {version_name: version}

    return get_settings
