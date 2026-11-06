"""Tests for the in-memory LRU cache."""
import pytest

from app.core.cache import LRUCache


def test_set_and_get():
    c = LRUCache(maxsize=3)
    c.set("a", 1); c.set("b", 2); c.set("c", 3)
    assert c.get("a") == 1
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_miss_returns_none():
    c = LRUCache(maxsize=3)
    assert c.get("missing") is None


def test_eviction_order():
    """Least recently used should be evicted first."""
    c = LRUCache(maxsize=2)
    c.set("a", 1); c.set("b", 2)
    assert c.get("a") == 1       # touch a to make b the LRU
    c.set("c", 3)                # should evict b
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_clear():
    c = LRUCache(maxsize=4)
    c.set("a", 1)
    c.clear()
    assert c.get("a") is None
    assert c.stats()["entries"] == 0


def test_stats_track_hits_and_misses():
    c = LRUCache(maxsize=4)
    c.set("x", 1)
    c.get("x"); c.get("x"); c.get("y")
    s = c.stats()
    assert s["hits"] == 2
    assert s["misses"] == 1
    assert 0 < s["hit_rate"] < 1


def test_invalid_maxsize():
    with pytest.raises(ValueError):
        LRUCache(maxsize=0)
    with pytest.raises(ValueError):
        LRUCache(maxsize=-1)


def test_overwrite_updates_recency():
    c = LRUCache(maxsize=2)
    c.set("a", 1); c.set("b", 2)
    c.set("a", 99)     # update, makes b the LRU
    c.set("c", 3)      # evicts b
    assert c.get("a") == 99
    assert c.get("b") is None
    assert c.get("c") == 3
