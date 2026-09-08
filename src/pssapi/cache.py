from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol


class Cache(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: float | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...


@dataclass(slots=True)
class _Entry:
    value: Any
    expires_at: float | None


class MemoryCache:
    """Small process-local async cache suitable for versioned API catalogs."""

    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at <= time.monotonic():
            self._data.pop(key, None)
            return None
        return entry.value

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        expires_at = None if ttl is None else time.monotonic() + max(0.0, ttl)
        self._data[key] = _Entry(value, expires_at)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def clear(self) -> None:
        self._data.clear()


def make_cache_key(*parts: Any) -> str:
    """Create a stable, compact cache key from JSON-compatible values."""
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()
