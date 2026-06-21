import time
import threading
from typing import Dict, Tuple, Any, Optional

class Cache:
    """Thread-safe cache with time-to-live (TTL) support."""
    def __init__(self, default_ttl: float = 300.0):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            value, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        duration = ttl if ttl is not None else self._default_ttl
        expiry = time.time() + duration
        with self._lock:
            self._cache[key] = (value, expiry)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

# Global instances for DNS and other resources
dns_cache = Cache(default_ttl=3600.0)  # 1 hour for DNS
general_cache = Cache(default_ttl=60.0)  # 1 minute for general lookups (e.g. public IP)
