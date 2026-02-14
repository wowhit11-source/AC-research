# apps/api/app/services/reports.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


ALLOWED_REPORT_DOMAINS: Dict[str, int] = {
    # Global institutions / central banks / research
    "bis.org": 120,
    "imf.org": 115,
    "worldbank.org": 110,
    "oecd.org": 105,
    "ecb.europa.eu": 105,
    "federalreserve.gov": 105,
    "bankofengland.co.uk": 100,
    "nber.org": 95,
    "ssrn.com": 75,
    "arxiv.org": 60,

    # KR public / think tanks
    "bok.or.kr": 100,
    "kdi.re.kr": 95,
    "keei.re.kr": 90,
    "ser.org": 90,
    "lgbr.co.kr": 85,
    "posri.re.kr": 85,

    # KR brokers / research portals (필요하면 계속 추가)
    "samsungpop.com": 95,
    "koreainvestment.com": 90,
    "nhqv.com": 90,
    "shinhaninvest.com": 90,
    "daishin.com": 85,
    "kiwoom.com": 85,
    "meritz.co.kr": 85,
    "kbsec.com": 85,
    "hanaw.com": 85,
    "ibks.com": 80,
    "sksecurities.co.kr": 80,
}

DEFAULT_MAX_ITEMS = 30
DEFAULT_MAX_AGE_DAYS = 365 * 5  # 5년


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _match_domain(url: str) -> Tuple[bool, str, int]:
    h = _host(url)
    for d, score in ALLOWED_REPORT_DOMAINS.items():
        if h == d or h.endswith("." + d):
            return True, d, score
    return False, h, 0


def _safe_str(x) -> str:
    return str(x) if x is not None else ""


def _parse_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    if not s:
        return None

    fmts = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


def _days_ago(dt: datetime) -> int:
    now = datetime.now(timezone.utc)
    delta = now - dt
    return max(0, int(delta.total_seconds() // 86400))


def _tokenize(q: str) -> List[str]:
    q = (q or "").strip().lower()
    if not q:
        return []
    toks = [t for t in q.split() if len(t) >= 2]
    return toks[:8]


def _keyword_score(title: str, snippet: str, tokens: List[str]) -> int:
    if not tokens:
        return 0
    text = (title + " " + snippet).lower()
    hit = 0
    for t in tokens:
        if t in text:
            hit += 1

    title_l = (title or "").lower()
    title_hit = sum(1 for t in tokens if t in title_l)

    return hit * 8 + title_hit * 6


def _recency_score(published: Optional[datetime], max_age_days: int) -> int:
    if not published:
        return 0
    age = _days_ago(published)
    if age > max_age_days:
        return -9999
    return max(0, 40 - int(age / 30) * 5)


def _normalize_title(title: str) -> str:
    t = (title or "").strip().lower()
    return " ".join(t.split())


def _is_low_quality_url(url: str) -> bool:
    u = (url or "").lower()
    if not u:
        return True
    if "sessionid=" in u:
        return True
    if "phpsessid=" in u:
        return True
    return False


@dataclass
class ReportItem:
    source: str
    title: str
    url: str
    published_date: str = ""
    snippet: str = ""
    score: int = 0


def screen_reports(
    query: str,
    candidates: List[dict],
    max_items: int = DEFAULT_MAX_ITEMS,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> List[dict]:
    tokens = _tokenize(query)

    items: List[ReportItem] = []
    seen_urls = set()
    seen_titles = set()

    for r in candidates or []:
        url = _safe_str(r.get("url") or r.get("main_url") or r.get("link") or r.get("pdf_url") or "")
        if not url:
            continue
        if _is_low_quality_url(url):
            continue

        ok, domain, domain_score = _match_domain(url)
        if not ok:
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = _safe_str(r.get("title") or "")
        snippet = _safe_str(r.get("snippet") or r.get("abstract") or "")

        norm_title = _normalize_title(title)
        if norm_title and norm_title in seen_titles:
            continue
        if norm_title:
            seen_titles.add(norm_title)

        published_s = _safe_str(r.get("published_date") or r.get("published_at") or r.get("date") or "")
        published_dt = _parse_date(published_s)

        rs = _recency_score(published_dt, max_age_days)
        if rs < -1000:
            continue

        ks = _keyword_score(title, snippet, tokens)

        bonus = 0
        if url.lower().endswith(".pdf"):
            bonus += 10

        penalty = 0
        if len(title) and len(title) < 10:
            penalty += 10
        if "utm_" in url.lower():
            penalty += 2

        score = domain_score + rs + ks + bonus - penalty

        items.append(
            ReportItem(
                source=domain,
                title=title,
                url=url,
                published_date=published_s,
                snippet=snippet,
                score=score,
            )
        )

    items.sort(key=lambda x: x.score, reverse=True)
    items = items[:max_items]

    return [asdict(x) for x in items]
