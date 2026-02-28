"""News search service — standalone (no app.config dependency).

지원 소스
- NewsAPI.org  (영문/비한글 쿼리 위주)
- NAVER 뉴스 검색 API (한글 쿼리 위주)

동작 원리
- 쿼리에 한글이 포함되어 있으면 네이버 뉴스 우선 사용
- 그 외에는 NewsAPI.org 사용
- 각각 URL 기준 중복 제거 + 최신순 정렬
- daily_only=True  이면 최근 24시간 이내 기사만 사용
- daily_only=False 이면 최근 30일 범위 사용
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

# 환경변수에서 직접 로드 (app.config 불필요)
NEWS_API_KEY: str = (os.getenv("NEWS_API_KEY") or "").strip()
NAVER_CLIENT_ID: str = (os.getenv("NAVER_CLIENT_ID") or "").strip()
NAVER_CLIENT_SECRET: str = (os.getenv("NAVER_CLIENT_SECRET") or "").strip()

# 1시간 메모리 캐시 (프로세스 단위)
_CACHE_TTL_SECONDS = 60 * 60
_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}


def _now_ts() -> float:
    return time.time()


def _has_hangul(text: str) -> bool:
    """쿼리에 한글이 하나라도 있으면 True."""
    for ch in text:
        if "\uac00" <= ch <= "\ud7a3":
            return True
    return False


def _canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if parsed.query:
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            filtered = [
                (k, v) for k, v in pairs
                if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid"}
            ]
            query = urlencode(filtered, doseq=True)
        else:
            query = ""
        cleaned = parsed._replace(netloc=netloc, query=query, fragment="")
        return urlunparse(cleaned)
    except Exception:
        return url.strip()


def _cache_key(provider: str, query: str, max_results: int, daily_only: bool) -> str:
    q = (query or "").strip().lower()
    d = "1d" if daily_only else "default"
    return f"news:{provider}:{q}:max={max_results}:range={d}"


def _cache_get(key: str) -> List[Dict[str, Any]] | None:
    item = _cache.get(key)
    if not item:
        return None
    ts, val = item
    if _now_ts() - ts > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return val


def _cache_set(key: str, val: List[Dict[str, Any]]) -> None:
    _cache[key] = (_now_ts(), val)


def _canonicalize_url(url: str) -> str:
    """URL 기반 중복 제거용 정규화."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if parsed.query:
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            filtered = []
            for k, v in pairs:
                kl = k.lower()
                if kl.startswith("utm_"):
                    continue
                if kl in {"gclid", "fbclid"}:
                    continue
                filtered.append((k, v))
            query = urlencode(filtered, doseq=True)
        else:
            query = ""
        cleaned = parsed._replace(netloc=netloc, query=query, fragment="")
        return urlunparse(cleaned)
    except Exception:
        return url.strip()


def _build_time_range_newsapi(daily_only: bool) -> Tuple[str | None, str | None]:
    now = datetime.now(timezone.utc)
    to_dt = now
    from_dt = now - timedelta(days=1) if daily_only else now - timedelta(days=30)
    return (
        from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _filter_by_timerange(
    items: List[Dict[str, Any]],
    key: str,
    daily_only: bool,
) -> List[Dict[str, Any]]:
    if not items:
        return []
    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=1) if daily_only else now - timedelta(days=30)
    filtered: List[Dict[str, Any]] = []
    for it in items:
        raw = (it.get(key) or "").strip()
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
        except Exception:
            filtered.append(it)
            continue
        if from_dt <= dt_utc <= now:
            filtered.append(it)
    return filtered


def _search_newsapi(
    query: str,
    max_results: int,
    daily_only: bool,
) -> List[Dict[str, Any]]:
    """NewsAPI.org 기반 뉴스 검색 (주로 영문)."""
    if not NEWS_API_KEY:
        return []

    provider = "newsapi"
    key = _cache_key(provider, query, max_results, daily_only)
    cached = _cache_get(key)
    if cached is not None:
        return cached[:max_results]

    from_dt, to_dt = _build_time_range_newsapi(daily_only)
    params: Dict[str, Any] = {
        "q": query,
        "pageSize": min(max_results, 100),
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }
    if from_dt:
        params["from"] = from_dt
    if to_dt:
        params["to"] = to_dt

    try:
        resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    articles = data.get("articles") or []
    results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for art in articles:
        raw_url = (art.get("url") or "").strip()
        if not raw_url:
            continue
        canon = _canonicalize_url(raw_url)
        if not canon or canon in seen_urls:
            continue
        seen_urls.add(canon)
        title = (art.get("title") or "").strip()
        published_at = (art.get("publishedAt") or "").strip()
        source = (art.get("source") or {}).get("name") or ""
        results.append({
            "title": title,
            "url": raw_url,
            "published_at": published_at,
            "source_name": source,
        })
        if len(results) >= max_results:
            break

    def _sort_key(item: Dict[str, Any]) -> Any:
        ts_str = item.get("published_at") or ""
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    results.sort(key=_sort_key, reverse=True)
    _cache_set(key, results)
    return results[:max_results]


def _search_naver(
    query: str,
    max_results: int,
    daily_only: bool,
) -> List[Dict[str, Any]]:
    """NAVER 뉴스 검색 API 기반 검색 (주로 한글)."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return []

    provider = "naver"
    key = _cache_key(provider, query, max_results, daily_only)
    cached = _cache_get(key)
    if cached is not None:
        return cached[:max_results]

    display = min(max_results, 100)
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params: Dict[str, Any] = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "sim",
    }

    try:
        resp = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            headers=headers, params=params, timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    items = data.get("items") or []
    items = _filter_by_timerange(items, "pubDate", daily_only)

    results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for it in items:
        raw_url = (it.get("link") or "").strip()
        if not raw_url:
            continue
        canon = _canonicalize_url(raw_url)
        if not canon or canon in seen_urls:
            continue
        seen_urls.add(canon)

        title = (it.get("title") or "").strip()
        pub_raw = (it.get("pubDate") or "").strip()
        try:
            dt = parsedate_to_datetime(pub_raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            published_at = dt_utc.isoformat().replace("+00:00", "Z")
        except Exception:
            published_at = ""

        source_name = (it.get("originallink") or "").strip()
        if not source_name:
            try:
                source_name = urlparse(raw_url).netloc
            except Exception:
                source_name = ""

        results.append({
            "title": title,
            "url": raw_url,
            "published_at": published_at or pub_raw,
            "source_name": source_name,
        })
        if len(results) >= max_results:
            break

    def _sort_key(item: Dict[str, Any]) -> Any:
        ts_str = item.get("published_at") or ""
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            try:
                return parsedate_to_datetime(ts_str)
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

    results.sort(key=_sort_key, reverse=True)
    _cache_set(key, results)
    return results[:max_results]


def news_api_configured() -> bool:
    """API 키가 하나라도 설정되어 있으면 True."""
    return bool(NEWS_API_KEY or (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET))


def search_news_articles(
    query: str,
    max_results: int = 40,
    daily_only: bool = False,
) -> List[Dict[str, Any]]:
    """통합 뉴스 검색 엔트리.

    반환 형식: 각 원소는 아래 키를 가진 dict
    - title, url, published_at, source_name, query
    """
    if not query:
        return []

    if _has_hangul(query):
        primary = _search_naver
        fallback = _search_newsapi
    else:
        primary = _search_newsapi
        fallback = _search_naver

    results = primary(query, max_results=max_results, daily_only=daily_only)
    if results:
        for r in results:
            r.setdefault("query", query)
        return results[:max_results]

    fallback_results = fallback(query, max_results=max_results, daily_only=daily_only)
    for r in fallback_results:
        r.setdefault("query", query)
    return fallback_results[:max_results]
