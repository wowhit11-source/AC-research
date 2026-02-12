"""OpenAlex paper search. Only results with pdf_url. No API key required."""
import time
import requests

OPENALEX_BASE = "https://api.openalex.org"
USER_AGENT = "AC-research API (paper scraper)"
REQUEST_DELAY = 0.2
TIMEOUT = 30


def search_papers(query: str, max_results: int = 30) -> list[dict]:
    """Search OpenAlex; only include items with pdf_url; sort by citation_count desc."""
    if not query or not query.strip():
        return []
    query = query.strip()
    column_order = [
        "title", "authors", "year", "venue", "citation_count",
        "is_open_access", "main_url", "pdf_url", "query",
    ]
    all_rows = []
    page = 1
    per_page = 25
    max_pages = 8
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
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            break
        except ValueError:
            break
        results = data.get("results") or []
        if not results:
            break
        for w in results:
            authorships = w.get("authorships") or []
            authors = ", ".join(
                (a.get("author") or {}).get("display_name") or "" for a in authorships
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
    all_rows.sort(key=lambda x: x["citation_count"], reverse=True)
    return all_rows[:max_results]
