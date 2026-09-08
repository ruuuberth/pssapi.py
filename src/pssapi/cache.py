from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class _Entry:
    value: Any
    expires_at: float | None


class MemoryCache:
    """Small async-safe in-memory cache used by the modern raw client."""

    def __init__(self, default_ttl: float | None = None) -> None:
        self.default_ttl = default_ttl
        self._items: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            if entry.expires_at is not None and entry.expires_at <= time.monotonic():
                self._items.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl = self.default_ttl if ttl is None else ttl
        expires_at = None if ttl is None else time.monotonic() + ttl
        async with self._lock:
            self._items[key] = _Entry(value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._items.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()

    async def __len__(self) -> int:
        async with self._lock:
            return len(self._items)
