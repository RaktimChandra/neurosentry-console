"""Tiny in-memory LRU cache for per-patient/per-window inferences.

Scrubbing the timeline back and forth repeatedly hits the same windows. A naive
cache gives free latency wins for that common interaction pattern without adding
any dependency.
"""
from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from typing import Any


class LRUCache:
    """Thread-safe LRU cache with a max-entry cap."""

    def __init__(self, maxsize: int = 512) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self._maxsize = maxsize
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None
            self._store.move_to_end(key)
            self._hits += 1
            return self._store[key]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, int | float]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "entries": len(self._store),
                "maxsize": self._maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total else 0.0,
            }


# Shared singleton for inference results
inference_cache = LRUCache(maxsize=1024)
