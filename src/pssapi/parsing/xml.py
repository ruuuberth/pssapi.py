"""XML response parsing helpers."""

from __future__ import annotations

from typing import Any, TypeVar
from xml.etree import ElementTree

import pssapi.utils as _utils
from pssapi.raw_client import RawResponse

T = TypeVar("T")


def _parse_root(response: RawResponse) -> ElementTree.Element:
    response.raise_for_status()
    raw_xml = response.text
    try:
        root = ElementTree.fromstring(raw_xml)
    except ElementTree.ParseError as exc:
        raise _utils.exceptions.PssXmlError(raw_xml, exc) from exc

    if root.tag.startswith("{http://www.w3.org/1999/xhtml}html"):
        raise _utils.exceptions.PssApiError(f"A server error occured: {raw_xml}")
    if "errorMessage" in root.attrib:
        raise _utils.exceptions.PssApiError(root.attrib["errorMessage"])
    return root


def parse_entity_list(
    response: RawResponse,
    parent_tag: str,
    entity_type: type[T],
) -> list[T]:
    """Parse a PSS XML collection response into typed entities."""
    root = _parse_root(response)
    parent_node = root if root.tag == parent_tag else root.find(f".//{parent_tag}")
    if parent_node is None:
        return []

    return [_parse_entity(node, entity_type) for node in parent_node]


def parse_entity(
    response: RawResponse,
    tag: str,
    entity_type: type[T],
) -> T:
    """Parse a single PSS XML entity response."""
    root = _parse_root(response)
    node = root if root.tag == tag else root.find(f".//{tag}")
    if node is None:
        raise _utils.exceptions.PssApiError(f"Response did not contain expected {tag} entity")
    return _parse_entity(node, entity_type)


def parse_composite_entities(
    response: RawResponse,
    *specs: tuple[str, type[T], bool],
) -> tuple[Any, ...]:
    """Parse multiple typed entities from one XML response.

    Each spec is ``(tag, entity_type, is_list)``. For list specs, the matching
    node is treated as a collection and every child becomes an entity.
    """
    root = _parse_root(response)
    result: list[Any] = []

    for tag, entity_type, is_list in specs:
        node = root if root.tag == tag else root.find(f".//{tag}")
        if node is None:
            result.append([] if is_list else None)
            continue

        if is_list:
            result.append([_parse_entity(child, entity_type) for child in node])
        else:
            result.append(_parse_entity(node, entity_type))

    return tuple(result)


def _parse_entity(node: ElementTree.Element, entity_type: type[T]) -> T:
    raw_entity = _raw_entity_xml(node)
    entity = entity_type(raw_entity)
    entity.node = node
    return entity


def _raw_entity_xml(node: ElementTree.Element) -> dict[str, Any]:
    result: dict[str, Any] = dict(node.attrib)
    for child in node:
        result.setdefault(child.tag, []).append(_raw_entity_xml(child))
    return result
