"""In-memory cache with TTL (10 minutes). Thread-safe for single process."""
import time
from typing import Any

TTL_SECONDS = 600  # 10 minutes

_cache: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    """Return value if key exists and not expired; else None."""
    if key not in _cache:
        return None
    val, expires = _cache[key]
    if time.monotonic() > expires:
        del _cache[key]
        return None
    return val


def set_(key: str, value: Any, ttl_seconds: int = TTL_SECONDS) -> None:
    """Store value with TTL."""
    _cache[key] = (value, time.monotonic() + ttl_seconds)


def delete(key: str) -> None:
    """Remove key."""
    _cache.pop(key, None)
