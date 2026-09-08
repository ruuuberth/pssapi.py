from types import SimpleNamespace

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.character_service import CharacterService


class FakeRawClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def call(self, service: str, method: str, *, params: dict, use_cache: bool):
        self.calls.append((service, method, params))
        return RawResponse(200, {}, b"<Response />", f"https://api.pixelstarships.com/{service}/{method}")


@pytest.fixture
def service() -> tuple[CharacterService, FakeRawClient]:
    raw = FakeRawClient()
    client = SimpleNamespace(raw=raw, language_key="English")
    service = CharacterService(client)
    service.get_settings = lambda: None
    return service, raw


@pytest.mark.asyncio
async def test_character_designs_use_modern_raw_client(service, monkeypatch) -> None:
    character_service, raw = service
    character_service.get_settings = _settings("CharacterDesignVersion", 42)
    monkeypatch.setattr(
        "pssapi.services.character_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    result = await character_service.list_all_character_designs(design_version=7)

    assert result == []
    assert raw.calls == [
        (
            "CharacterService",
            "ListAllCharacterDesigns2",
            {"clientDateTime": None, "languageKey": "English", "designVersion": 7},
        )
    ]


@pytest.mark.asyncio
async def test_character_actions_use_modern_raw_client(service, monkeypatch) -> None:
    character_service, raw = service
    character_service.get_settings = _settings("CharacterDesignActionVersion", 42)
    monkeypatch.setattr(
        "pssapi.services.character_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    await character_service.list_all_character_design_actions(design_version=9)

    assert raw.calls == [
        (
            "CharacterService",
            "ListAllCharacterDesignActions",
            {"clientDateTime": None, "designVersion": 9},
        )
    ]


@pytest.mark.asyncio
async def test_draw_designs_use_modern_raw_client(service, monkeypatch) -> None:
    character_service, raw = service
    character_service.get_settings = _settings("DrawDesignVersion", 42)
    monkeypatch.setattr(
        "pssapi.services.character_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    await character_service.list_all_draw_designs()

    assert raw.calls == [
        (
            "CharacterService",
            "ListAllDrawDesigns",
            {"clientDateTime": None, "languageKey": "English"},
        )
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["prestige_character_from", "prestige_character_to"])
async def test_prestige_endpoints_use_modern_raw_client(service, monkeypatch, method: str) -> None:
    character_service, raw = service
    monkeypatch.setattr(
        "pssapi.services.character_service._parse_entity_list",
        lambda response, parent_tag, entity_type: [],
    )

    await getattr(character_service, method)(19)

    expected_method = "PrestigeCharacterFrom" if method.endswith("from") else "PrestigeCharacterTo"
    assert raw.calls == [
        (
            "CharacterService",
            expected_method,
            {"characterDesignId": 19},
        )
    ]


def _settings(version_name: str, version: int):
    async def get_settings():
        return {version_name: version}

    return get_settings
