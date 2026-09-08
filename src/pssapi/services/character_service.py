import datetime as _datetime
from typing import List as _List

import pssapi.services.service_base as _service_base

from .. import utils as _utils
from ..entities import CharacterDesign as _CharacterDesign
from ..entities import CharacterDesignAction as _CharacterDesignAction
from ..entities import DrawDesign as _DrawDesign
from ..entities import Prestige as _Prestige
from ..parsing import parse_entity_list as _parse_entity_list


class CharacterService(_service_base.CacheableServiceBase):
    async def to_character(
        self,
        character_name: str,
        client_date_time: _datetime.datetime = None,
        design_version: int = None,
    ) -> _List[_CharacterDesign]:
        characters = await self.list_all_character_designs(client_date_time, design_version)
        return [
            character
            for character in characters
            if character_name.lower() in character.character_design_name.lower()
        ]

    @_service_base.cache_endpoint("CharacterDesignActionVersion")
    async def list_all_character_design_actions(
        self,
        client_date_time: _datetime.datetime = None,
        design_version: int = None,
    ) -> _List[_CharacterDesignAction]:
        params = {
            "clientDateTime": _utils.datetime.convert_to_pss_timestamp(client_date_time),
        }
        if design_version is not None:
            params["designVersion"] = design_version

        response = await self.client.raw.call(
            "CharacterService",
            "ListAllCharacterDesignActions",
            params=params,
            use_cache=False,
        )
        return _parse_entity_list(response, "CharacterDesignActions", _CharacterDesignAction)

    @_service_base.cache_endpoint("CharacterDesignVersion")
    async def list_all_character_designs(
        self,
        client_date_time: _datetime.datetime = None,
        design_version: int = None,
    ) -> _List[_CharacterDesign]:
        params = {
            "clientDateTime": _utils.datetime.convert_to_pss_timestamp(client_date_time),
            "languageKey": str(self.language_key),
        }
        if design_version is not None:
            params["designVersion"] = design_version

        response = await self.client.raw.call(
            "CharacterService",
            "ListAllCharacterDesigns2",
            params=params,
            use_cache=False,
        )
        return _parse_entity_list(response, "CharacterDesigns", _CharacterDesign)

    @_service_base.cache_endpoint("DrawDesignVersion")
    async def list_all_draw_designs(
        self,
        client_date_time: _datetime.datetime = None,
        design_version: int = None,
    ) -> _List[_DrawDesign]:
        params = {
            "clientDateTime": _utils.datetime.convert_to_pss_timestamp(client_date_time),
            "languageKey": str(self.language_key),
        }
        if design_version is not None:
            params["designVersion"] = design_version

        response = await self.client.raw.call(
            "CharacterService",
            "ListAllDrawDesigns",
            params=params,
            use_cache=False,
        )
        return _parse_entity_list(response, "DrawDesigns", _DrawDesign)

    async def prestige_character_from(self, character_design_id: int) -> _List[_Prestige]:
        response = await self.client.raw.call(
            "CharacterService",
            "PrestigeCharacterFrom",
            params={"characterDesignId": character_design_id},
            use_cache=False,
        )
        return _parse_entity_list(response, "Prestiges", _Prestige)

    async def prestige_character_to(self, character_design_id: int) -> _List[_Prestige]:
        response = await self.client.raw.call(
            "CharacterService",
            "PrestigeCharacterTo",
            params={"characterDesignId": character_design_id},
            use_cache=False,
        )
        return _parse_entity_list(response, "Prestiges", _Prestige)
