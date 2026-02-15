"""YouTube Data API v3 search (quota-optimized). Uses YOUTUBE_API_KEY from env."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import YOUTUBE_API_KEY

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    build = None
    HttpError = Exception  # type: ignore


# 24h in-memory cache (per process)
_CACHE_TTL_SECONDS = 24 * 60 * 60
_cache: dict[str, tuple[float, list[dict]]] = {}


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _cache_key(query: str, max_results: int) -> str:
    q = (query or "").strip().lower()
    return f"yt:{q}:max={max_results}:dur=long:range=1y:order=date"


def _cache_get(key: str) -> list[dict] | None:
    item = _cache.get(key)
    if not item:
        return None
    ts, val = item
    if _now_ts() - ts > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return val


def _cache_set(key: str, val: list[dict]) -> None:
    _cache[key] = (_now_ts(), val)


def _is_quota_exceeded(err: Exception) -> bool:
    if not isinstance(err, HttpError):
        return False
    try:
        status = getattr(err.resp, "status", None)
        if status != 403:
            return False
        content = err.content.decode("utf-8", errors="ignore") if getattr(err, "content", None) else ""
        return "quotaExceeded" in content or "dailyLimitExceeded" in content
    except Exception:
        return False


def search_youtube_videos(query: str, max_results: int = 30) -> list[dict]:
    """
    Quota-optimized YouTube search.
    - 20min+ handled by videoDuration=long (search.list)
    - last 1y
    - returns title, url, duration_minutes(None), published_at
    """
    if not query:
        return []
    if not YOUTUBE_API_KEY or not build:
        return []

    key = _cache_key(query, max_results)
    cached = _cache_get(key)
    if cached is not None:
        return cached[:max_results]

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    published_after = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")

    results: list[dict[str, Any]] = []
    next_page_token: str | None = None

    # search.list cost is the main driver, so keep pages minimal.
    # Start with 20; only paginate if you truly need up to 30.
    per_page = 20 if max_results > 20 else max_results

    try:
        while len(results) < max_results:
            resp = (
                youtube.search()
                .list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="date",
                    publishedAfter=published_after,
                    videoDuration="long",
                    maxResults=per_page,
                    pageToken=next_page_token or "",
                )
                .execute()
            )

            items = resp.get("items", []) or []
            for item in items:
                vid = ((item.get("id") or {}).get("videoId") or "").strip()
                if not vid:
                    continue
                snippet = item.get("snippet") or {}
                results.append(
                    {
                        "title": snippet.get("title") or "",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "duration_minutes": None,
                        "published_at": snippet.get("publishedAt") or "",
                    }
                )
                if len(results) >= max_results:
                    break

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break

        # cache successful results
        _cache_set(key, results[:max_results])
        return results[:max_results]

    except Exception as e:
        # If quota exceeded, serve cached data if any exists (even stale one is better than hard fail)
        if _is_quota_exceeded(e):
            stale = _cache.get(key)
            if stale:
                return stale[1][:max_results]
            return []
        # other errors: don't poison cache
        return []
