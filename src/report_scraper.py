# -*- coding: utf-8 -*-
"""
리포트 검색 스크래퍼 — 네이버 금융 리서치 (종목분석 리포트)

타겟: https://finance.naver.com/research/company_list.naver
스크래핑: requests + BeautifulSoup
- 검색어(query)가 종목명 또는 증권사명에 포함된 리포트만 필터링
- 결과 형식: title, url, source(증권사명), published_date, query

API 키 불필요.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://finance.naver.com/research/company_list.naver"
BASE_HOST = "https://finance.naver.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/research/",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
TIMEOUT = 15


def _fetch_page(page: int) -> List[Dict[str, Any]]:
    """한 페이지에서 리포트 목록 추출."""
    try:
        resp = requests.get(
            BASE_URL,
            params={"page": page},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        resp.encoding = "euc-kr"
        html = resp.text
    except Exception:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # 리포트 목록 테이블: class="type_1"
    table = soup.find("table", {"class": "type_1"})
    if not table:
        return []

    rows = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue

        # 컬럼 순서: 종목명 | 리포트제목 | 증권사 | 첨부 | 작성일 | 조회수
        # (종목명 td에 a 태그, 제목 td에 a 태그)
        try:
            stock_td  = tds[0]
            title_td  = tds[1]
            source_td = tds[2]
            date_td   = tds[4] if len(tds) >= 5 else tds[3]
        except IndexError:
            continue

        stock_name = stock_td.get_text(strip=True)

        title_a = title_td.find("a")
        if not title_a:
            continue
        title = title_a.get_text(strip=True)
        href  = title_a.get("href", "")
        url   = href if href.startswith("http") else BASE_HOST + href

        source       = source_td.get_text(strip=True)
        published_at = date_td.get_text(strip=True)

        rows.append({
            "stock_name":     stock_name,
            "title":          title,
            "url":            url,
            "source":         source,
            "published_date": published_at,
        })

    return rows


def search_reports(query: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    네이버 금융 리서치 종목분석 리포트 검색.

    query가 종목명 또는 제목에 포함된 리포트만 반환.
    페이지를 순회하며 max_results 개 이상 모이면 중단.

    반환 dict 키: title, url, source, published_date, query
    """
    if not (query or "").strip():
        return []

    q = query.strip()
    q_lower = q.lower()

    results: List[Dict[str, Any]] = []
    page = 1
    max_pages = 20  # 최대 20페이지까지 탐색

    while len(results) < max_results and page <= max_pages:
        rows = _fetch_page(page)
        if not rows:
            break

        for row in rows:
            stock = row["stock_name"].lower()
            title = row["title"].lower()

            if q_lower in stock or q_lower in title:
                results.append({
                    "title":          row["title"],
                    "url":            row["url"],
                    "source":         row["source"],
                    "published_date": row["published_date"],
                    "query":          q,
                })
                if len(results) >= max_results:
                    break

        page += 1

    return results[:max_results]
