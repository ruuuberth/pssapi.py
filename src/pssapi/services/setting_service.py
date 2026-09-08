import datetime as _datetime
from typing import List as _List

import pssapi.services.service_base as _service_base

from .. import utils as _utils
from ..entities import NewsDesign as _NewsDesign
from ..entities import Setting as _Setting
from ..parsing import parse_entity_list as _parse_entity_list


class SettingService(_service_base.CacheableServiceBase):
    async def get_latest_version(self, device_type: str) -> _Setting:
        response = await self.client.raw.call(
            "SettingService",
            "GetLatestVersion4",
            params={
                "deviceType": device_type,
                "languageKey": str(self.language_key),
            },
            use_cache=False,
        )
        parsed = _parse_entity_list(response, "Setting", _Setting)
        if not parsed:
            raise _utils.exceptions.PssApiError("SettingService/GetLatestVersion4 returned no Setting")
        return parsed[0]

    @_service_base.cache_endpoint("NewsDesignVersion")
    async def list_all_news_designs(
        self,
        client_date_time: _datetime.datetime = None,
        design_version: int = None,
    ) -> _List[_NewsDesign]:
        params = {
            "clientDateTime": _utils.datetime.convert_to_pss_timestamp(client_date_time),
            "languageKey": str(self.language_key),
        }
        if design_version is not None:
            params["designVersion"] = design_version

        response = await self.client.raw.call(
            "SettingService",
            "ListAllNewsDesigns",
            params=params,
            use_cache=False,
        )
        return _parse_entity_list(response, "NewsDesigns", _NewsDesign)
