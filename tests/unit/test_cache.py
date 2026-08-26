"""
Unit tests for netcheck.utils.cache
"""
import time
import pytest
from netcheck.utils.cache import Cache


class TestCacheTTL:
    def test_get_before_expiry(self):
        cache = Cache(default_ttl=10)
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_get_after_expiry(self):
        cache = Cache(default_ttl=0.05)
        cache.set("k", "v")
        time.sleep(0.1)
        assert cache.get("k") is None

    def test_overwrite_resets_ttl(self):
        cache = Cache(default_ttl=0.05)
        cache.set("k", "first")
        time.sleep(0.03)
        cache.set("k", "second")   # reset TTL
        time.sleep(0.03)
        assert cache.get("k") == "second"   # should still be live

    def test_miss_returns_none(self):
        cache = Cache(default_ttl=10)
        assert cache.get("nonexistent") is None


class TestCacheEviction:
    def test_max_size_evicts_oldest(self):
        cache = Cache(default_ttl=60, max_size=3)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")
        # k1 is oldest, adding k4 should evict k1
        cache.set("k4", "v4")
        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"
        assert cache.get("k4") == "v4"

    def test_max_size_one(self):
        cache = Cache(default_ttl=60, max_size=1)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
