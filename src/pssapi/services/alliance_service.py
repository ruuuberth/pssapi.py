from typing import List as _List
from typing import Tuple as _Tuple

import pssapi.services.service_base as _service_base

from ..entities import Alliance as _Alliance
from ..entities import Character as _Character
from ..entities import Message as _Message
from ..entities import User as _User
from ..parsing.xml import parse_composite_entities as _parse_composite_entities
from ..parsing.xml import parse_entity as _parse_entity
from ..parsing.xml import parse_entity_list as _parse_entity_list


class AllianceService(_service_base.ServiceBase):
    async def get_alliance(self, access_token: str, alliance_id: int) -> _Alliance:
        response = await self.client.raw.call(
            "AllianceService",
            "GetAlliance",
            params={"accessToken": access_token, "allianceId": alliance_id},
            use_cache=False,
        )
        return _parse_entity(response, "Alliance", _Alliance)

    async def get_user(self, access_token: str, user_id: int) -> _User:
        response = await self.client.raw.call(
            "AllianceService",
            "GetUser",
            params={"accessToken": access_token, "userId": user_id},
            use_cache=False,
        )
        return _parse_entity(response, "User", _User)

    async def list_alliances_by_championship_score_ranking(
        self, access_token: str, from_: int, to: int
    ) -> _List[_Alliance]:
        response = await self.client.raw.call(
            "AllianceService",
            "ListAlliancesByChampionshipScoreRanking",
            params={"accessToken": access_token, "from": from_, "to": to},
            use_cache=False,
        )
        return _parse_entity_list(response, "Alliances", _Alliance)

    async def list_alliances_by_ranking(self, skip: int, take: int) -> _List[_Alliance]:
        response = await self.client.raw.call(
            "AllianceService",
            "ListAlliancesByRanking",
            params={"skip": skip, "take": take},
            use_cache=False,
        )
        return _parse_entity_list(response, "Alliances", _Alliance)

    async def list_alliances_with_division(self, division_design_id: int) -> _List[_Alliance]:
        response = await self.client.raw.call(
            "AllianceService",
            "ListAlliancesWithDivision",
            params={"divisionDesignId": division_design_id},
            use_cache=False,
        )
        return _parse_entity_list(response, "Alliances", _Alliance)

    async def list_characters_given_in_alliance(
        self, access_token: str, alliance_id: int, skip: int, take: int
    ) -> _List[_Character]:
        response = await self.client.raw.call(
            "AllianceService",
            "ListCharactersGivenInAlliance",
            params={
                "accessToken": access_token,
                "allianceId": alliance_id,
                "skip": skip,
                "take": take,
            },
            use_cache=False,
        )
        return _parse_entity_list(response, "Characters", _Character)

    async def list_users(
        self, access_token: str, alliance_id: int, skip: int, take: int
    ) -> _Tuple[_List[_Message], _List[_User]]:
        response = await self.client.raw.call(
            "AllianceService",
            "ListUsers2",
            params={
                "accessToken": access_token,
                "allianceId": alliance_id,
                "skip": skip,
                "take": take,
            },
            use_cache=False,
        )
        alliance, users = _parse_composite_entities(
            response,
            ("Alliance", _Alliance, False),
            ("Users", _User, True),
        )
        return alliance, users

    async def search_alliances(
        self, access_token: str, name: str, skip: int, take: int
    ) -> _List[_Alliance]:
        response = await self.client.raw.call(
            "AllianceService",
            "SearchAlliances",
            params={
                "accessToken": access_token,
                "name": name,
                "skip": skip,
                "take": take,
            },
            use_cache=False,
        )
        return _parse_entity_list(response, "Alliances", _Alliance)
