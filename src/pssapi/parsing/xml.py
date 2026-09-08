"""XML response parsing helpers."""

from __future__ import annotations

from typing import Any, TypeVar
from xml.etree import ElementTree

import pssapi.utils as _utils
from pssapi.raw_client import RawResponse

T = TypeVar("T")


def parse_entity_list(
    response: RawResponse,
    parent_tag: str,
    entity_type: type[T],
) -> list[T]:
    """Parse a PSS XML collection response into typed entities."""
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


def _raw_entity_xml(node: ElementTree.Element) -> dict[str, Any]:
    result: dict[str, Any] = dict(node.attrib)
    for child in node:
        result.setdefault(child.tag, []).append(_raw_entity_xml(child))
    return result
