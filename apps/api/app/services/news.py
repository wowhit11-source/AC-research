"""News search service for AC-research.

- Uses NEWS_API_KEY from env (configured in app.config).
- Returns URL 중심의 뉴스 리스트.
- 같은 URL이 여러 번 나오는 경우 URL 기준으로 중복 제거.
- daily_only=True 인 경우 최근 24시간 이내 기사만 조회.
- daily_only=False 인 경우 기본 30일(또는 API 기본값) 범위에서 조회.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests

try:
    from app.config import NEWS_API_KEY  # type: ignore[attr-defined]
except Exception:  # config에 아직 없을 경우를 대비한 안전장치
    NEWS_API_KEY = ""  # type: ignore[assignment]


# 1시간 메모리 캐시 (프로세스 단위)
_CACHE_TTL_SECONDS = 60 * 60
_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _now_ts() -> float:
    return time.time()


def _cache_key(query: str, max_results: int, daily_only: bool) -> str:
    q = (query or "").strip().lower()
    d = "1d" if daily_only else "default"
    return f"news:{q}:max={max_results}:range={d}"


def _cache_get(key: str) -> list[dict[str, Any]] | None:
    item = _cache.get(key)
    if not item:
        return None
    ts, val = item
    if _now_ts() - ts > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return val


def _cache_set(key: str, val: list[dict[str, Any]]) -> None:
    _cache[key] = (_now_ts(), val)


def _canonicalize_url(url: str) -> str:
    """
    URL 기반 중복 제거용 정규화.

    - scheme/host/path만 유지하고, 추적용 쿼리 파라미터는 제거(utm_*, gclid, fbclid 등).
    - trailing slash는 유지하지만, 대소문자는 host 부분만 소문자로 통일.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        # host는 소문자로
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


def _build_time_range(daily_only: bool) -> tuple[str | None, str | None]:
    """
    News API에 전달할 from / to 파라미터 생성.

    - daily_only=True  → 최근 24시간
    - daily_only=False → 최근 30일 (너무 오래된 뉴스는 잘 안 쓰이므로)
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


def search_news_articles(
    query: str,
    max_results: int = 40,
    daily_only: bool = False,
) -> list[dict[str, Any]]:
    """
    뉴스 검색.

    반환 형식: 각 원소는 아래 키를 가진 dict
    - title: 기사 제목
    - url: 원문 URL
    - published_at: ISO8601 문자열
    - source_name: 매체 이름

    중복 제거:
    - 같은 canonical URL(도메인+경로+정리된 쿼리)이 여러 번 나오면 최초 1개만 유지.
    """

    if not query:
        return []

    if not NEWS_API_KEY:
        # 환경변수 미설정 시 조용히 빈 리스트 반환
        return []

    # 캐시 확인
    key = _cache_key(query, max_results, daily_only)
    cached = _cache_get(key)
    if cached is not None:
        return cached[:max_results]

    from_dt, to_dt = _build_time_range(daily_only)

    # 여기서는 대표적인 뉴스 API 패턴(예: newsapi.org)을 가정한다.
    # 실제 엔드포인트 / 파라미터는 사용 중인 API 스펙에 맞게 조정 가능.
    url = "https://newsapi.org/v2/everything"
    params: dict[str, Any] = {
        "q": query,
        "pageSize": min(max_results, 100),
        "sortBy": "publishedAt",
        "language": "en",  # 필요에 따라 ko 등으로 바꿀 수 있음
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
        # 뉴스는 필수 소스가 아니므로, 실패 시 빈 리스트만 반환
        return []

    articles = data.get("articles") or []
    results: list[dict[str, Any]] = []

    seen_urls: set[str] = set()

    for art in articles:
        raw_url = (art.get("url") or "").strip()
        if not raw_url:
            continue

        canon = _canonicalize_url(raw_url)
        if not canon or canon in seen_urls:
            # 같은 기사 URL이 여러 번 나오는 케이스는 여기서 제거됨
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

    # 최신순 정렬 (API가 이미 정렬해 주더라도 한 번 더 명시적으로)
    def _sort_key(item: dict[str, Any]) -> Any:
        ts_str = item.get("published_at") or ""
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    results.sort(key=_sort_key, reverse=True)

    _cache_set(key, results)
    return results[:max_results]
