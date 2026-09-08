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


def _find_node(root: ElementTree.Element, tag: str) -> ElementTree.Element | None:
    return root if root.tag == tag else root.find(f".//{tag}")


def parse_entity(
    response: RawResponse,
    parent_tag: str,
    entity_type: type[T],
) -> T:
    """Parse a PSS XML response containing one entity."""
    root = _parse_root(response)
    node = _find_node(root, parent_tag)
    if node is None:
        raise _utils.exceptions.PssApiError(f"Response did not contain {parent_tag}")

    entity = entity_type(_raw_entity_xml(node))
    entity.node = node
    return entity


def parse_entity_list(
    response: RawResponse,
    parent_tag: str,
    entity_type: type[T],
) -> list[T]:
    """Parse a PSS XML collection response into typed entities."""
    root = _parse_root(response)
    parent_node = _find_node(root, parent_tag)
    if parent_node is None:
        return []

    result: list[T] = []
    for node in parent_node:
        raw_entity = _raw_entity_xml(node)
        entity = entity_type(raw_entity)
        entity.node = node
        result.append(entity)
    return result


def parse_entity_bundle(
    response: RawResponse,
    entities: tuple[tuple[str, type[Any], bool], ...],
) -> tuple[Any, ...]:
    """Parse a response containing multiple named PSS entity sections.

    Each specification is ``(tag, entity_type, is_list)``. Missing sections
    raise ``PssApiError`` so malformed API responses are not silently accepted.
    """
    root = _parse_root(response)
    result: list[Any] = []

    for tag, entity_type, is_list in entities:
        node = _find_node(root, tag)
        if node is None:
            raise _utils.exceptions.PssApiError(f"Response did not contain {tag}")

        if is_list:
            values = []
            for child in node:
                entity = entity_type(_raw_entity_xml(child))
                entity.node = child
                values.append(entity)
            result.append(values)
        else:
            entity = entity_type(_raw_entity_xml(node))
            entity.node = node
            result.append(entity)

    return tuple(result)


def _raw_entity_xml(node: ElementTree.Element) -> dict[str, Any]:
    result: dict[str, Any] = dict(node.attrib)
    for child in node:
        result.setdefault(child.tag, []).append(_raw_entity_xml(child))
    return result
