from types import SimpleNamespace

import pytest

from pssapi.raw_client import RawResponse
from pssapi.services.alliance_service import AllianceService


class FakeRawClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict, bool]] = []

    async def call(self, service: str, method: str, *, params: dict, use_cache: bool):
        self.calls.append((service, method, params, use_cache))
        return RawResponse(200, {}, b"<Response />", f"https://api.pixelstarships.com/{service}/{method}")


@pytest.fixture
def service() -> tuple[AllianceService, FakeRawClient]:
    raw = FakeRawClient()
    client = SimpleNamespace(raw=raw, language_key="English")
    return AllianceService(client), raw


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "args", "api_method", "params", "parser"),
    [
        ("get_alliance", ("token", 7), "GetAlliance", {"accessToken": "token", "allianceId": 7}, "single"),
        ("get_user", ("token", 8), "GetUser", {"accessToken": "token", "userId": 8}, "single"),
        (
            "list_alliances_by_championship_score_ranking",
            ("token", 1, 10),
            "ListAlliancesByChampionshipScoreRanking",
            {"accessToken": "token", "from": 1, "to": 10},
            "list",
        ),
        ("list_alliances_by_ranking", (1, 10), "ListAlliancesByRanking", {"skip": 1, "take": 10}, "list"),
        (
            "list_alliances_with_division",
            (12,),
            "ListAlliancesWithDivision",
            {"divisionDesignId": 12},
            "list",
        ),
        (
            "list_characters_given_in_alliance",
            ("token", 7, 0, 20),
            "ListCharactersGivenInAlliance",
            {"accessToken": "token", "allianceId": 7, "skip": 0, "take": 20},
            "list",
        ),
        (
            "search_alliances",
            ("token", "Test", 0, 20),
            "SearchAlliances",
            {"accessToken": "token", "name": "Test", "skip": 0, "take": 20},
            "list",
        ),
    ],
)
async def test_endpoints_use_modern_raw_client(
    service, monkeypatch, method_name, args, api_method, params, parser
) -> None:
    alliance_service, raw = service
    monkeypatch.setattr(
        "pssapi.services.alliance_service._parse_entity",
        lambda response, tag, entity_type: object(),
    )
    monkeypatch.setattr(
        "pssapi.services.alliance_service._parse_entity_list",
        lambda response, tag, entity_type: [],
    )

    result = await getattr(alliance_service, method_name)(*args)

    assert result is not None
    assert raw.calls == [("AllianceService", api_method, params, False)]


@pytest.mark.asyncio
async def test_list_users_uses_composite_parser(service, monkeypatch) -> None:
    alliance_service, raw = service
    expected = (object(), [object()])
    monkeypatch.setattr(
        "pssapi.services.alliance_service._parse_entity_bundle",
        lambda response, entities: expected,
    )

    result = await alliance_service.list_users("token", 7, 0, 20)

    assert result == expected
    assert raw.calls == [
        (
            "AllianceService",
            "ListUsers2",
            {"accessToken": "token", "allianceId": 7, "skip": 0, "take": 20},
            False,
        )
    ]
