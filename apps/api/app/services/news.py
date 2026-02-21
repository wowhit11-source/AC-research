"""News search service for AC-research.

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

import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from app.config import NEWS_API_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET


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
    """URL 기반 중복 제거용 정규화.

    - scheme/host/path만 유지하고, 추적용 쿼리 파라미터는 제거(utm_*, gclid, fbclid 등).
    - trailing slash는 유지하지만, host는 소문자로 통일.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())

        # host를 소문자로 통일
        netloc = parsed.netloc.lower()

        # 쿼리 파라미터 정리 (utm_, gclid, fbclid 등 제거)
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
        # 문제가 생기면 원본 URL 그대로 반환
        return url.strip()


def _build_time_range_newsapi(daily_only: bool) -> Tuple[str | None, str | None]:
    """NewsAPI.org에 전달할 from/to 파라미터 생성.

    - daily_only=True  → 최근 24시간
    - daily_only=False → 최근 30일
    """
    now = datetime.now(timezone.utc)
    to_dt = now
    if daily_only:
        from_dt = now - timedelta(days=1)
    else:
        from_dt = now - timedelta(days=30)

    return (
        from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _filter_by_timerange(
    items: List[Dict[str, Any]],
    key: str,
    daily_only: bool,
) -> List[Dict[str, Any]]:
    """pubDate 같은 문자열에서 datetime을 뽑아 최근 24시간/30일만 남김."""
    if not items:
        return []

    now = datetime.now(timezone.utc)
    if daily_only:
        from_dt = now - timedelta(days=1)
    else:
        from_dt = now - timedelta(days=30)

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
            # 파싱 실패 시 일단 포함
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

    url = "https://newsapi.org/v2/everything"
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
        resp = requests.get(url, params=params, timeout=20)
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

        results.append(
            {
                "title": title,
                "url": raw_url,
                "published_at": published_at,
                "source_name": source,
            }
        )

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

    url = "https://openapi.naver.com/v1/search/news.json"
    display = min(max_results, 100)

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params: Dict[str, Any] = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "sim",  # 정확도순. 필요하면 "date"로 변경 가능
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    items = data.get("items") or []

    # pubDate 기준으로 최근 24시간/30일 필터링
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
                parsed = urlparse(raw_url)
                source_name = parsed.netloc
            except Exception:
                source_name = ""

        results.append(
            {
                "title": title,
                "url": raw_url,
                "published_at": published_at or pub_raw,
                "source_name": source_name,
            }
        )

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


def search_news_articles(
    query: str,
    max_results: int = 40,
    daily_only: bool = False,
) -> List[Dict[str, Any]]:
    """통합 뉴스 검색 엔트리.

    반환 형식: 각 원소는 아래 키를 가진 dict
    - title: 기사 제목
    - url: 원문 URL
    - published_at: ISO8601 또는 원본 날짜 문자열
    - source_name: 매체 이름
    """
    if not query:
        return []

    # 한글 포함 여부로 기본 소스 결정
    if _has_hangul(query):
        primary = _search_naver
        fallback = _search_newsapi
    else:
        primary = _search_newsapi
        fallback = _search_naver

    results = primary(query, max_results=max_results, daily_only=daily_only)
    if results:
        return results[:max_results]

    # 주 소스가 실패하면 보조 소스로라도 결과 시도
    fallback_results = fallback(query, max_results=max_results, daily_only=daily_only)
    return fallback_results[:max_results]
