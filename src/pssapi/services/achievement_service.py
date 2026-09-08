from typing import List as _List

import pssapi.services.service_base as _service_base

from ..entities import AchievementDesign as _AchievementDesign


class AchievementService(_service_base.CacheableServiceBase):
    @_service_base.cache_endpoint("AchievementDesignVersion")
    async def list_achievement_designs(self, design_version: int = None) -> _List[_AchievementDesign]:
        params = {"languageKey": str(self.language_key)}
        if design_version is not None:
            params["designVersion"] = design_version

        response = await self.client.raw.call(
            "AchievementService",
            "ListAchievementDesigns2",
            params=params,
            use_cache=False,
        )
        return _service_base.parse_entity_list(response, "AchievementDesigns", _AchievementDesign)
