from types import SimpleNamespace

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.alliance_service import AllianceService


class FakeRawClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def call(self, service: str, method: str, *, params: dict, use_cache: bool):
        self.calls.append((service, method, params))
        return RawResponse(200, {}, b"<Response />", f"https://api.pixelstarships.com/{service}/{method}")


@pytest.fixture
def service() -> tuple[AllianceService, FakeRawClient]:
    raw = FakeRawClient()
    client = SimpleNamespace(raw=raw, language_key="English")
    return AllianceService(client), raw


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "api_method", "params"),
    [
        ("get_alliance", "GetAlliance", {"accessToken": "token", "allianceId": 7}),
        ("get_user", "GetUser", {"accessToken": "token", "userId": 8}),
        (
            "list_alliances_by_championship_score_ranking",
            "ListAlliancesByChampionshipScoreRanking",
            {"accessToken": "token", "from": 1, "to": 10},
        ),
        ("list_alliances_by_ranking", "ListAlliancesByRanking", {"skip": 1, "take": 10}),
        (
            "list_alliances_with_division",
            "ListAlliancesWithDivision",
            {"divisionDesignId": 12},
        ),
        (
            "list_characters_given_in_alliance",
            "ListCharactersGivenInAlliance",
            {"accessToken": "token", "allianceId": 7, "skip": 0, "take": 20},
        ),
        (
            "search_alliances",
            "SearchAlliances",
            {"accessToken": "token", "name": "Test", "skip": 0, "take": 20},
        ),
    ],
)
async def test_endpoints_use_modern_raw_client(
    service, monkeypatch, method_name, api_method, params
) -> None:
    alliance_service, raw = service
    monkeypatch.setattr(
        f"pssapi.services.alliance_service._parse_entity",
        lambda response, tag, entity_type: object(),
    )
    monkeypatch.setattr(
        f"pssapi.services.alliance_service._parse_entity_list",
        lambda response, tag, entity_type: [],
    )

    if method_name == "get_alliance":
        result = await alliance_service.get_alliance("token", 7)
    elif method_name == "get_user":
        result = await alliance_service.get_user("token", 8)
    elif method_name == "list_alliances_by_championship_score_ranking":
        result = await alliance_service.list_alliances_by_championship_score_ranking("token", 1, 10)
    elif method_name == "list_alliances_by_ranking":
        result = await alliance_service.list_alliances_by_ranking(1, 10)
    elif method_name == "list_alliances_with_division":
        result = await alliance_service.list_alliances_with_division(12)
    elif method_name == "list_characters_given_in_alliance":
        result = await alliance_service.list_characters_given_in_alliance("token", 7, 0, 20)
    else:
        result = await alliance_service.search_alliances("token", "Test", 0, 20)

    assert result is not None
    assert raw.calls == [("AllianceService", api_method, params)]


@pytest.mark.asyncio
async def test_list_users_uses_composite_parser(service, monkeypatch) -> None:
    alliance_service, raw = service
    expected = (object(), [object()])
    parser = lambda response, *specs: expected
    monkeypatch.setattr("pssapi.services.alliance_service._parse_composite_entities", parser)

    result = await alliance_service.list_users("token", 7, 0, 20)

    assert result == expected
    assert raw.calls == [
        (
            "AllianceService",
            "ListUsers2",
            {"accessToken": "token", "allianceId": 7, "skip": 0, "take": 20},
        )
    ]
