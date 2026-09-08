import functools as _functools
from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import ParamSpec as _ParamSpec
from typing import Type as _Type
from typing import TypeVar as _TypeVar
from xml.etree import ElementTree as _ElementTree

import pssapi.client as _client
import pssapi.entities as _entities
import pssapi.enums as _enums
import pssapi.utils as _utils
from pssapi.raw_client import RawResponse as _RawResponse


T = _TypeVar("T")
P = _ParamSpec("P")


class ServiceBase(object):
    def __init__(self, client: _client.PssApiClient) -> None:
        if not client:
            raise ValueError("The parameter 'client' must not be None.")
        self.__client = client

    @property
    def client(self) -> _client.PssApiClient:
        return self.__client

    @property
    def language_key(self) -> _enums.LanguageKey:
        return self.client.language_key

    async def get_settings(self) -> "_entities.Setting":
        return await self.client.get_latest_version()

    async def get_production_server(self) -> str:
        return await self.client.get_production_server()


class CacheableServiceBase(ServiceBase):
    def __init__(self, client: _client.PssApiClient, enable_endpoint_cache: bool = True) -> None:
        super().__init__(client)
        self._SERVICE_CACHE: _Dict[str, _Dict[int, _Any]] = {}
        self._enable_endpoint_cache: bool = enable_endpoint_cache or False


def parse_entity_list(response: _RawResponse, parent_tag: str, entity_type: _Type[T]) -> list[T]:
    """Parse a PSS XML collection response into typed entities."""
    response.raise_for_status()
    raw_xml = response.text
    try:
        root = _ElementTree.fromstring(raw_xml)
    except _ElementTree.ParseError as exc:
        raise _utils.exceptions.PssXmlError(raw_xml, exc) from exc

    if root.tag.startswith("{http://www.w3.org/1999/xhtml}html"):
        raise _utils.exceptions.PssApiError(f"A server error occured: {raw_xml}")
    if "errorMessage" in root.attrib:
        raise _utils.exceptions.PssApiError(root.attrib["errorMessage"])

    parent_node = root if root.tag == parent_tag else root.find(f".//{parent_tag}")
    if parent_node is None:
        return []

    result: list[T] = []
    for node in parent_node:
        raw_entity = _raw_entity_xml(node)
        entity = entity_type(raw_entity)
        entity.node = node
        result.append(entity)
    return result


def _raw_entity_xml(node: _ElementTree.Element) -> dict[str, _Any]:
    result: dict[str, _Any] = dict(node.attrib)
    for child in node:
        result.setdefault(child.tag, []).append(_raw_entity_xml(child))
    return result


def cache_endpoint(version_property_name: str):
    def decorator_endpoint_cache(func: _Callable[P, T]) -> _Callable[P, T]:
        @_functools.wraps(func)
        async def wrapper_endpoint_cache(self, *args, **kwargs):
            if isinstance(self, CacheableServiceBase) and self._enable_endpoint_cache:
                endpoint_name = func.__name__
                service_cache = self._SERVICE_CACHE
                latest_version = await self.get_settings()
                endpoint_data_version = latest_version[version_property_name]

                endpoint_cache = service_cache.get(endpoint_name, {})
                data = endpoint_cache.get(endpoint_data_version)

                if data is None:
                    data = await func(self, *args, **kwargs)
                    if endpoint_cache:
                        service_cache[endpoint_name] = {}
                    service_cache.setdefault(endpoint_name, {})[endpoint_data_version] = data
                if isinstance(data, list):
                    return list(data)
                if isinstance(data, dict):
                    return dict(data)
                return data
            else:
                return await func(self, *args, **kwargs)

        return wrapper_endpoint_cache

    return decorator_endpoint_cache
