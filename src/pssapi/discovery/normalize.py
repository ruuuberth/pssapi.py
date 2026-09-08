"""Normalization helpers for captured HTTP payloads."""

from __future__ import annotations

import base64
import json
import zlib
from typing import Any
from xml.etree import ElementTree


def decode_body(body: Any, *, encoding: str = "utf-8", gzipped: bool = False) -> Any:
    """Decode bytes/text and return JSON, XML metadata, or plain text.

    No values are discarded: undecodable or non-JSON/XML payloads are retained
    as text/bytes where possible.
    """
    if isinstance(body, bytes):
        raw = body
    elif isinstance(body, str):
        raw = body.encode(encoding, errors="replace")
    else:
        return body

    if gzipped:
        try:
            raw = zlib.decompress(base64.b64decode(raw), zlib.MAX_WBITS | 32)
        except (ValueError, zlib.error):
            pass

    text = raw.decode(encoding, errors="replace").strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return text
    return xml_to_data(root)


def xml_to_data(node: ElementTree.Element) -> dict[str, Any]:
    """Convert an XML node to a loss-minimizing JSON-like structure."""
    result: dict[str, Any] = dict(node.attrib)
    children: dict[str, list[Any]] = {}
    for child in node:
        children.setdefault(child.tag, []).append(xml_to_data(child))
    for tag, values in children.items():
        result[tag] = values[0] if len(values) == 1 else values
    text = (node.text or "").strip()
    if text and not children:
        result["_text"] = text
    return result


def normalize_endpoint(service: str | None, method: str | None, path: str | None = None) -> str:
    """Return a stable endpoint identifier."""
    if service and method:
        return f"{service.strip('/')}/{method.strip('/')}"
    return (path or "/").strip("/")
