# -*- coding: utf-8 -*-
"""
논문 검색 모듈 (OpenAlex API).
키워드로 관련 논문을 검색하고, 인용 횟수 기준 상위 N편을 반환한다.
유튜브 검색 모듈(search_youtube_videos)과 동일한 인터페이스 형태로 설계.
"""
import os
import sys
import time

import requests

# 스크립트 기준 프로젝트 루트 path 보정 (Windows/OneDrive 등)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

# OpenAlex는 API 키 없이 사용 가능. 공식 메타데이터 API만 사용.
OPENALEX_BASE = "https://api.openalex.org"
USER_AGENT = "SEC_project paper scraper (mailto:your-email@example.com)"
# Rate limit 완화를 위한 요청 간 대기(초)
REQUEST_DELAY = 0.2


def search_papers(query: str, max_results: int = 30) -> list[dict]:
    """
    OpenAlex API로 키워드 검색 후, 인용 횟수 내림차순으로 상위 max_results개 반환.
    반환 list[dict] 필드: title, authors, year, venue, citation_count,
    is_open_access, main_url, pdf_url, query.
    """
    if not query or not query.strip():
        return []

    query = query.strip()
    # CSV 컬럼 순서에 맞춰 dict 키 순서 고정 (Python 3.7+)
    column_order = [
        "title", "authors", "year", "venue", "citation_count",
        "is_open_access", "main_url", "pdf_url", "query",
    ]

    all_rows = []
    page = 1
    per_page = 25
    max_pages = 8  # PDF 있는 논문만 쓰므로 더 많은 페이지 조회

    while len(all_rows) < max_results and page <= max_pages:
        url = (
            f"{OPENALEX_BASE}/works"
            f"?search={requests.utils.quote(query)}"
            f"&sort=cited_by_count:desc"
            f"&per-page={per_page}"
            f"&page={page}"
        )
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            # 한 페이지 실패 시 지금까지 수집한 결과만 반환
            break
        except ValueError:
            break

        results = data.get("results") or []
        if not results:
            break

        for w in results:
            authorships = w.get("authorships") or []
            authors = ", ".join(
                (a.get("author") or {}).get("display_name") or ""
                for a in authorships
            ).strip()

            primary = w.get("primary_location") or {}
            source = primary.get("source") or {}
            venue = source.get("display_name") or ""

            locations = w.get("locations") or []
            pdf_url = ""
            for loc in locations:
                if loc.get("pdf_url"):
                    pdf_url = (loc.get("pdf_url") or "").strip()
                    break

            # pdf_url이 있는 논문만 포함
            if not pdf_url:
                continue

            row = {
                "title": w.get("title") or "",
                "authors": authors,
                "year": w.get("publication_year") or "",
                "venue": venue,
                "citation_count": int(w.get("cited_by_count") or 0),
                "is_open_access": bool((w.get("open_access") or {}).get("is_oa")),
                "main_url": w.get("id") or "",
                "pdf_url": pdf_url,
                "query": query,
            }
            ordered = {k: row[k] for k in column_order}
            all_rows.append(ordered)
            if len(all_rows) >= max_results:
                break

        if len(results) < per_page:
            break
        page += 1
        time.sleep(REQUEST_DELAY)

    # 인용 수 내림차순 정렬 후 상위 max_results개
    all_rows.sort(key=lambda x: x["citation_count"], reverse=True)
    return all_rows[:max_results]
