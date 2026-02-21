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


def _cache_key(query: str, max_results: int, daily_only: bool) -> str:
    """
    Cache key includes:
    - query (normalized)
    - max_results
    - duration=long
    - range=1y or 24h (daily_only)
    - order=date
    """
    q = (query or "").strip().lower()
    range_tag = "24h" if daily_only else "1y"
    return f"yt:{q}:max={max_results}:dur=long:range={range_tag}:order=date"


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


def _to_rfc3339(dt: datetime) -> str:
    """
    Convert aware UTC datetime to RFC3339 string (YYYY-MM-DDTHH:MM:SSZ).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_published_at(value: str) -> datetime | None:
    """
    Parse YouTube ISO timestamp (e.g. '2025-01-03T12:34:56Z') to aware UTC datetime.
    """
    if not value:
        return None
    try:
        # Handle trailing 'Z'
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def search_youtube_videos(
    query: str,
    max_results: int = 30,
    daily_only: bool = False,
) -> list[dict]:
    """
    Quota-optimized YouTube search.

    - videoDuration=long (20min+)
    - default: last 1y
    - daily_only=True: strictly last 24 hours
    - returns: dicts with {title, url, duration_minutes(None), published_at}
    """
    if not query:
        return []
    if not YOUTUBE_API_KEY or not build:
        return []

    key = _cache_key(query, max_results, daily_only)
    cached = _cache_get(key)
    if cached is not None:
        return cached[:max_results]

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    now_utc = datetime.now(timezone.utc)
    if daily_only:
        base_dt = now_utc - timedelta(hours=24)
    else:
        base_dt = now_utc - timedelta(days=365)

    published_after = _to_rfc3339(base_dt)

    results: list[dict[str, Any]] = []
    next_page_token: str | None = None

    # search.list cost is the main driver, so keep pages minimal.
    # Start with 20; only paginate if you truly need up to max_results.
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
                published_at_raw = snippet.get("publishedAt") or ""
                results.append(
                    {
                        "title": snippet.get("title") or "",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "duration_minutes": None,
                        "published_at": published_at_raw,
                    }
                )
                if len(results) >= max_results:
                    break

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break

        # 추가 안전장치: daily_only=True일 때는 응답에서도 다시 24시간 컷
        if daily_only:
            cutoff = now_utc - timedelta(hours=24)
            filtered: list[dict[str, Any]] = []
            for item in results:
                dt = _parse_published_at(item.get("published_at") or "")
                if dt is None:
                    # publishedAt 파싱 실패한 것은 보수적으로 포함하지 않는다.
                    continue
                if dt >= cutoff:
                    filtered.append(item)
            results = filtered

        # cache successful results
        trimmed = results[:max_results]
        _cache_set(key, trimmed)
        return trimmed

    except Exception as e:
        # If quota exceeded, serve cached data if any exists (even stale one is better than hard fail)
        if _is_quota_exceeded(e):
            stale = _cache.get(key)
            if stale:
                return stale[1][:max_results]
            return []
        # other errors: don't poison cache
        return []
