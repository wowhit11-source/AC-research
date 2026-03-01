"""
AC-research API. FastAPI app.
Endpoints: GET /health, POST /api/research, GET /api/research/{slug}/excel
Production: Render (port from PORT env, default 10000). CORS via ALLOWED_ORIGINS.
"""
from __future__ import annotations

import io
import os
import time
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.cache import get as cache_get, set_ as cache_set
from app.schemas import ErrorItem, MultiResearchRequest, ResearchMeta, ResearchRequest, ResearchResponse, ResearchResults
from app.utils import is_korea_stock, slugify

# 리포트 스크리닝
from app.services.reports import screen_reports

# CORS: 배포 테스트용 "*" 허용. Production에서 ALLOWED_ORIGINS로 제한 권장.
_origins_str = os.getenv("ALLOWED_ORIGINS", "").strip()
if _origins_str:
    _allow_origins = [o.strip() for o in _origins_str.split(",") if o.strip()]
else:
    _allow_origins = ["*"]  # 임시 허용 (배포 테스트용)

app = FastAPI(title="AC-research API", version="1.0.0", debug=os.getenv("ENV") != "production")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_item(source: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Add title, url, date, snippet for frontend. Keep raw fields."""
    out = dict(raw)

    if source == "sec":
        out["title"] = f"{raw.get('ticker', '')} {raw.get('source_type', '')} {raw.get('published_date', '')}"
        out["url"] = raw.get("url", "")
        out["date"] = raw.get("published_date", "")
        out["snippet"] = ""
    elif source == "dart":
        out["title"] = f"{raw.get('회사명', '')} {raw.get('보고서 종류', '')} {raw.get('기준연도/분기', '')}"
        out["url"] = raw.get("url", "")
        out["date"] = raw.get("제출일", "")
        out["snippet"] = raw.get("기준연도/분기", "")
    elif source == "youtube":
        out["title"] = raw.get("title", "")
        out["url"] = raw.get("url", "")
        out["date"] = raw.get("published_at", "")
        out["snippet"] = f"{raw.get('duration_minutes', 0)} min"
    elif source == "papers":
        out["title"] = raw.get("title", "")
        out["url"] = raw.get("pdf_url", "") or raw.get("main_url", "")
        out["date"] = str(raw.get("year", ""))
        out["snippet"] = f"{raw.get('authors', '')} | {raw.get('venue', '')}"
    elif source == "news":
        out["title"] = raw.get("title", "")
        out["url"] = raw.get("url", "")
        out["date"] = raw.get("published_at", "")
        out["snippet"] = raw.get("source_name", "")
    return out


@app.get("/health")
def health():
    return {"ok": True}


def _run_research(
    query: str,
    daily_only: bool = False,
    max_yt: int = 30,
    max_paper: int = 30,
    max_news: int = 40,
    max_report: int = 30,
) -> tuple[ResearchResults, list[ErrorItem]]:
    """단일 쿼리에 대해 모든 소스를 검색하고 ResearchResults를 반환."""
    errors: list[ErrorItem] = []
    dart_data: dict[str, Any] | None = None
    sec_data: dict[str, Any] | None = None
    youtube_list: list[dict[str, Any]] = []
    papers_list: list[dict[str, Any]] = []
    reports_list: list[dict[str, Any]] = []
    news_list: list[dict[str, Any]] = []

    # DART (국내 종목코드 6자리+)
    if is_korea_stock(query):
        try:
            from app.services.dart import collect_dart_reports
            rows = collect_dart_reports(query, daily_only=daily_only)
            dart_data = {"items": [_normalize_item("dart", r) for r in rows], "raw": rows}
        except Exception as e:
            errors.append(ErrorItem(source="dart", message=str(e)))
    else:
        # SEC (US ticker)
        try:
            from app.services.sec import collect_sec_links
            rows = collect_sec_links(query.upper(), daily_only=daily_only)
            sec_data = {"items": [_normalize_item("sec", r) for r in rows], "raw": rows}
        except Exception as e:
            errors.append(ErrorItem(source="sec", message=str(e)))

    # YouTube
    try:
        from app.services.youtube import search_youtube_videos
        rows = search_youtube_videos(query, max_results=max_yt, daily_only=daily_only)
        youtube_list = [_normalize_item("youtube", r) for r in rows]
    except Exception as e:
        errors.append(ErrorItem(source="youtube", message=str(e)))

    # Papers
    try:
        from app.services.papers import search_papers
        rows = search_papers(query, max_results=max_paper)
        papers_list = [_normalize_item("papers", r) for r in rows]
    except Exception as e:
        errors.append(ErrorItem(source="papers", message=str(e)))

    # News
    try:
        from app.services.news import search_news_articles
        rows = search_news_articles(query, max_results=max_news, daily_only=daily_only)
        news_list = [_normalize_item("news", r) for r in rows]
    except Exception as e:
        errors.append(ErrorItem(source="news", message=str(e)))

    # Reports screening
    try:
        candidates: list[dict[str, Any]] = []
        if papers_list:
            candidates.extend(papers_list)
        if sec_data and sec_data.get("items"):
            candidates.extend(sec_data["items"])
        if dart_data and dart_data.get("items"):
            candidates.extend(dart_data["items"])
        screened = screen_reports(query=query, candidates=candidates, max_items=max_report)
        reports_list = []
        for it in screened:
            out = dict(it)
            if "published_date" in out and "date" not in out:
                out["date"] = out.get("published_date", "")
            if "source" in out and "source_type" not in out:
                out["source_type"] = out.get("source", "")
            reports_list.append(out)
    except Exception as e:
        errors.append(ErrorItem(source="reports", message=str(e)))

    results = ResearchResults(
        dart=dart_data,
        sec=sec_data,
        youtube=youtube_list,
        papers=papers_list,
        reports=reports_list,
        news=news_list,
    )
    return results, errors


def _add_query_col(results: ResearchResults, query: str) -> ResearchResults:
    """각 결과 항목에 query 컬럼을 추가해 다중 검색 결과 구분을 돕는다."""
    def _tag(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{**it, "query": query} for it in items]

    def _tag_keyed(obj: dict[str, Any] | None) -> dict[str, Any] | None:
        if obj is None:
            return None
        tagged_items = _tag(obj.get("items") or [])
        tagged_raw = [{**r, "query": query} for r in (obj.get("raw") or [])]
        return {**obj, "items": tagged_items, "raw": tagged_raw}

    return ResearchResults(
        dart=_tag_keyed(results.dart),
        sec=_tag_keyed(results.sec),
        youtube=_tag(results.youtube),
        papers=_tag(results.papers),
        reports=_tag(results.reports),
        news=_tag(results.news),
    )


def _merge_results(all_results: list[ResearchResults]) -> ResearchResults:
    """여러 쿼리 결과를 하나의 ResearchResults로 병합."""
    dart_items, dart_raw = [], []
    sec_items, sec_raw = [], []
    youtube, papers, reports, news = [], [], [], []

    for r in all_results:
        if r.dart:
            dart_items.extend(r.dart.get("items") or [])
            dart_raw.extend(r.dart.get("raw") or [])
        if r.sec:
            sec_items.extend(r.sec.get("items") or [])
            sec_raw.extend(r.sec.get("raw") or [])
        youtube.extend(r.youtube)
        papers.extend(r.papers)
        reports.extend(r.reports)
        news.extend(r.news)

    return ResearchResults(
        dart={"items": dart_items, "raw": dart_raw} if dart_items else None,
        sec={"items": sec_items, "raw": sec_raw} if sec_items else None,
        youtube=youtube,
        papers=papers,
        reports=reports,
        news=news,
    )


@app.post("/api/research", response_model=ResearchResponse)
def research(body: ResearchRequest, daily_only: bool = False):
    """
    단일 쿼리 검색.
    daily_only=True: SEC/DART/YouTube/News를 최근 24시간 이내 자료로 제한.
    """
    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    slug = slugify(query)
    daily_flag = 1 if daily_only else 0
    cache_key = f"research:{slug}:daily={daily_flag}"

    cached = cache_get(cache_key)
    if cached is not None:
        return ResearchResponse(**cached)

    start = time.perf_counter()
    results, errors = _run_research(query, daily_only=daily_only)
    elapsed_ms = (time.perf_counter() - start) * 1000

    meta = ResearchMeta(elapsed_ms=round(elapsed_ms, 2), errors=errors)
    resp = ResearchResponse(query=query, slug=slug, results=results, meta=meta)
    cache_set(cache_key, resp.model_dump())
    return resp


@app.post("/api/research/multi", response_model=ResearchResponse)
def research_multi(body: MultiResearchRequest, daily_only: bool = False):
    """
    다중 쿼리 검색.
    - 유튜브/논문/뉴스/리포트는 검색어당 body.max_results(기본 10)개로 제한.
    - SEC/DART는 기존 한도 유지 (전체 수집).
    - 각 결과에 query 컬럼을 추가해 어느 검색어에서 나온 결과인지 구분 가능.
    - 모든 쿼리 결과를 합쳐서 하나의 ResearchResponse로 반환.
    """
    queries = [q.strip() for q in (body.queries or []) if q.strip()]
    if not queries:
        raise HTTPException(status_code=400, detail="queries must not be empty")

    mr = body.max_results
    slug = slugify("_".join(queries[:3]))
    daily_flag = 1 if daily_only else 0
    cache_key = f"research:multi:{slug}:max={mr}:daily={daily_flag}"

    cached = cache_get(cache_key)
    if cached is not None:
        return ResearchResponse(**cached)

    start = time.perf_counter()
    all_results: list[ResearchResults] = []
    all_errors: list[ErrorItem] = []

    for q in queries:
        results, errors = _run_research(
            q,
            daily_only=daily_only,
            max_yt=mr,
            max_paper=mr,
            max_news=mr,
            max_report=mr,
        )
        tagged = _add_query_col(results, q)
        all_results.append(tagged)
        all_errors.extend(errors)

    merged = _merge_results(all_results)
    elapsed_ms = (time.perf_counter() - start) * 1000

    meta = ResearchMeta(elapsed_ms=round(elapsed_ms, 2), errors=all_errors)
    combined_query = " | ".join(queries)
    resp = ResearchResponse(query=combined_query, slug=slug, results=merged, meta=meta)
    cache_set(cache_key, resp.model_dump())
    return resp


@app.get("/api/research/{slug}/excel")
def research_excel(slug: str, daily_only: bool = False):
    """
    Return Excel file for cached research result.
    Filename: research_{slug}.xlsx

    daily_only는 /api/research 호출 시와 동일하게 맞춰야
    대응되는 캐시를 찾을 수 있다.
    """
    daily_flag = 1 if daily_only else 0
    cache_key = f"research:{slug}:daily={daily_flag}"

    cached = cache_get(cache_key)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Research result not found or expired. Run search first (check daily_only flag).",
        )

    results = cached.get("results") or {}
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        if results.get("dart") and results["dart"].get("raw"):
            df = pd.DataFrame(results["dart"]["raw"])
            df.to_excel(writer, sheet_name="KOREA_SEC", index=False)

        if results.get("sec") and results["sec"].get("raw"):
            df = pd.DataFrame(results["sec"]["raw"])
            df.to_excel(writer, sheet_name="SEC", index=False)

        if results.get("youtube"):
            rows: list[dict[str, Any]] = []
            for it in results["youtube"]:
                rows.append(
                    {
                        "title": it.get("title"),
                        "url": it.get("url"),
                        "duration_minutes": it.get("duration_minutes"),
                        "published_at": it.get("date"),
                    }
                )
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="YouTube", index=False)

        if results.get("papers"):
            rows = []
            for it in results["papers"]:
                rows.append(
                    {
                        "title": it.get("title"),
                        "authors": it.get("authors"),
                        "year": it.get("year"),
                        "venue": it.get("venue"),
                        "citation_count": it.get("citation_count"),
                        "main_url": it.get("main_url"),
                        "pdf_url": it.get("url"),
                    }
                )
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="Papers", index=False)

        if results.get("reports"):
            rows = []
            for it in results["reports"]:
                rows.append(
                    {
                        "source": it.get("source") or it.get("source_type"),
                        "title": it.get("title"),
                        "url": it.get("url"),
                        "published_date": it.get("published_date") or it.get("date"),
                        "score": it.get("score"),
                    }
                )
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="Reports", index=False)

        if results.get("news"):
            rows = []
            for it in results["news"]:
                rows.append(
                    {
                        "title": it.get("title"),
                        "url": it.get("url"),
                        "published_at": it.get("date") or it.get("published_at"),
                        "source_name": it.get("snippet") or it.get("source_name"),
                    }
                )
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="News", index=False)

    buffer.seek(0)
    filename = f"research_{slug}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
