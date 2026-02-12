"""
AC-research API. FastAPI app.
Endpoints: GET /health, POST /api/research, GET /api/research/{slug}/excel
Production: Render (port from PORT env, default 10000). CORS via ALLOWED_ORIGINS.
"""
import io
import os
import time
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.cache import get as cache_get, set_ as cache_set
from app.schemas import ErrorItem, ResearchMeta, ResearchRequest, ResearchResponse, ResearchResults
from app.utils import is_korea_stock, slugify

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
    return out


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/research", response_model=ResearchResponse)
def research(body: ResearchRequest):
    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    slug = slugify(query)
    cache_key = f"research:{slug}"

    cached = cache_get(cache_key)
    if cached is not None:
        return ResearchResponse(**cached)

    start = time.perf_counter()
    errors: list[ErrorItem] = []
    dart_data: dict[str, Any] | None = None
    sec_data: dict[str, Any] | None = None
    youtube_list: list[dict[str, Any]] = []
    papers_list: list[dict[str, Any]] = []

    # DART (domestic stock code: 6+ digits)
    if is_korea_stock(query):
        try:
            from app.services.dart import collect_dart_reports
            rows = collect_dart_reports(query)
            dart_data = {"items": [_normalize_item("dart", r) for r in rows], "raw": rows}
        except Exception as e:
            errors.append(ErrorItem(source="dart", message=str(e)))
    else:
        # SEC (US ticker)
        try:
            from app.services.sec import collect_sec_links
            rows = collect_sec_links(query.upper())
            sec_data = {"items": [_normalize_item("sec", r) for r in rows], "raw": rows}
        except Exception as e:
            errors.append(ErrorItem(source="sec", message=str(e)))

    # YouTube
    try:
        from app.services.youtube import search_youtube_videos
        rows = search_youtube_videos(query, max_results=30)
        youtube_list = [_normalize_item("youtube", r) for r in rows]
    except Exception as e:
        errors.append(ErrorItem(source="youtube", message=str(e)))

    # Papers (pdf_url only)
    try:
        from app.services.papers import search_papers
        rows = search_papers(query, max_results=30)
        papers_list = [_normalize_item("papers", r) for r in rows]
    except Exception as e:
        errors.append(ErrorItem(source="papers", message=str(e)))

    elapsed_ms = (time.perf_counter() - start) * 1000
    results = ResearchResults(dart=dart_data, sec=sec_data, youtube=youtube_list, papers=papers_list)
    meta = ResearchMeta(elapsed_ms=round(elapsed_ms, 2), errors=errors)
    resp = ResearchResponse(query=query, slug=slug, results=results, meta=meta)
    cache_set(cache_key, resp.model_dump())
    return resp


@app.get("/api/research/{slug}/excel")
def research_excel(slug: str):
    """Return Excel file for cached research result. Filename: research_{slug}.xlsx."""
    cache_key = f"research:{slug}"
    cached = cache_get(cache_key)
    if not cached:
        raise HTTPException(status_code=404, detail="Research result not found or expired. Run search first.")
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
            # raw-like: title, url, duration_minutes, published_at
            rows = []
            for it in results["youtube"]:
                rows.append({
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "duration_minutes": it.get("duration_minutes"),
                    "published_at": it.get("date"),
                })
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="YouTube", index=False)
        if results.get("papers"):
            rows = []
            for it in results["papers"]:
                rows.append({
                    "title": it.get("title"),
                    "authors": it.get("authors"),
                    "year": it.get("year"),
                    "venue": it.get("venue"),
                    "citation_count": it.get("citation_count"),
                    "main_url": it.get("main_url"),
                    "pdf_url": it.get("url"),
                })
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="Papers", index=False)
    buffer.seek(0)
    filename = f"research_{slug}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
