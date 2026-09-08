"""Portable .psscap capture container support.

The format deliberately stores raw request/response data. Interpretation belongs
in the discovery layer so captures remain useful as the API evolves.
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


FORMAT_VERSION = 1


def _jsonl_record(record: Mapping[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"


class CaptureWriter:
    """Write a portable PSS capture archive."""

    def __init__(self, path: str | Path, *, metadata: Mapping[str, Any] | None = None) -> None:
        self.path = Path(path)
        self.metadata = dict(metadata or {})
        self._requests: list[Mapping[str, Any]] = []
        self._responses: list[Mapping[str, Any]] = []

    def add_request(self, record: Mapping[str, Any]) -> None:
        self._requests.append(dict(record))

    def add_response(self, record: Mapping[str, Any]) -> None:
        self._responses.append(dict(record))

    def write(self) -> Path:
        manifest = {
            "format": "psscap",
            "version": FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **self.metadata,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            archive.writestr("requests.jsonl", "".join(_jsonl_record(r) for r in self._requests))
            archive.writestr("responses.jsonl", "".join(_jsonl_record(r) for r in self._responses))
        return self.path


class CaptureReader:
    """Read records from a .psscap archive."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read_json(self, archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
        return json.loads(archive.read(name).decode("utf-8"))

    def _read_jsonl(self, archive: zipfile.ZipFile, name: str) -> Iterable[dict[str, Any]]:
        for line in archive.read(name).decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)

    def manifest(self) -> dict[str, Any]:
        with zipfile.ZipFile(self.path) as archive:
            return self._read_json(archive, "manifest.json")

    def requests(self) -> Iterable[dict[str, Any]]:
        with zipfile.ZipFile(self.path) as archive:
            yield from self._read_jsonl(archive, "requests.jsonl")

    def responses(self) -> Iterable[dict[str, Any]]:
        with zipfile.ZipFile(self.path) as archive:
            yield from self._read_jsonl(archive, "responses.jsonl")
