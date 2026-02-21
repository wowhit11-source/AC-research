"""SEC EDGAR 10-K/10-Q/8-K link collection. No Streamlit dependency."""
from __future__ import annotations

import datetime as dt
import requests

USER_AGENT = "AC-research API (SEC scraper)"
TIMEOUT = 25


def _sec_get(url: str, host: str = "www.sec.gov") -> requests.Response:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": host,
    }
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


def _get_cik_from_ticker(ticker: str) -> str:
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = _sec_get(url, host="www.sec.gov")
    data = resp.json()
    t = ticker.upper()
    for item in data.values():
        if item["ticker"].upper() == t:
            return str(item["cik_str"])
    raise ValueError(f"CIK not found for ticker {ticker}")


def _filing_records_from_recent(
    cik: str,
    filings: dict,
    form_filter: list[str],
    cutoff_date: dt.date | None,
    max_items: int | None,
) -> list[dict]:
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    records: list[dict] = []

    for form, date_str, acc, primary in zip(forms, dates, accession_numbers, primary_docs):
        if form not in form_filter:
            continue
        filed_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        if cutoff_date and filed_date < cutoff_date:
            continue

        accession_nodash = acc.replace("-", "")
        cik_no_padding = str(int(cik))
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_padding}/{accession_nodash}/{primary}"

        records.append(
            {
                "source_type": "SEC",
                "url": doc_url,
                "published_date": filed_date.isoformat(),
                "ticker": None,
            }
        )

    records.sort(key=lambda r: r["published_date"], reverse=True)
    if max_items is not None:
        records = records[:max_items]
    return records


def _get_recent_filings_payload(cik: str) -> dict:
    padded_cik = cik.zfill(10)
    api_url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    resp = _sec_get(api_url, host="data.sec.gov")
    data = resp.json()
    return data.get("filings", {}).get("recent", {})


def _get_recent_10k_filings(cik: str, years: int = 5) -> list[dict]:
    filings = _get_recent_filings_payload(cik)
    cutoff = dt.date.today() - dt.timedelta(days=365 * years)
    return _filing_records_from_recent(cik, filings, ["10-K"], cutoff, None)


def _get_recent_10q_filings(cik: str, quarters: int = 4) -> list[dict]:
    filings = _get_recent_filings_payload(cik)
    # 최근 filing 목록에서 10-Q만 form 기준으로 잘라내고, 개수(quarters)만 제한
    return _filing_records_from_recent(cik, filings, ["10-Q"], None, quarters)


def _get_recent_8k_filings(cik: str, days: int = 365, max_items: int = 30) -> list[dict]:
    filings = _get_recent_filings_payload(cik)
    cutoff = dt.date.today() - dt.timedelta(days=days)
    return _filing_records_from_recent(cik, filings, ["8-K"], cutoff, max_items)


def _filter_last_24h(records: list[dict]) -> list[dict]:
    """
    SEC 'filingDate'는 날짜만 제공되므로,
    - 현재 UTC 기준 24시간 전을 date로 내림하여
    - 그 날짜 이상인 것만 포함한다.
    """
    if not records:
        return []

    now_utc = dt.datetime.now(dt.timezone.utc)
    cutoff_dt = now_utc - dt.timedelta(hours=24)
    cutoff_date = cutoff_dt.date()

    filtered: list[dict] = []
    for r in records:
        date_str = r.get("published_date")
        if not date_str:
            continue
        try:
            filed_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if filed_date >= cutoff_date:
            filtered.append(r)

    # 안전하게 다시 날짜 내림차순 정렬
    filtered.sort(key=lambda r: r["published_date"], reverse=True)
    return filtered


def collect_sec_links(ticker: str, daily_only: bool = False) -> list[dict]:
    """
    Recent 5y 10-K + 4 quarters 10-Q + recent 1y 8-K.

    Each dict:
      - source_type: "SEC"
      - url
      - published_date (YYYY-MM-DD)
      - ticker (uppercased)

    daily_only=False: 기존과 동일 (5y 10-K, 4x 10-Q, 1y 8-K 전부)
    daily_only=True : 위 전체 중에서 최근 24시간(UTC 기준) 이내 제출분만 반환
    """
    t = ticker.upper()
    cik = _get_cik_from_ticker(ticker)

    records = (
        _get_recent_10k_filings(cik, years=5)
        + _get_recent_10q_filings(cik, quarters=4)
        + _get_recent_8k_filings(cik, days=365, max_items=30)
    )

    # URL 기준 중복 제거
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in records:
        u = r.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        r["ticker"] = t
        deduped.append(r)

    deduped.sort(key=lambda r: r["published_date"], reverse=True)

    if daily_only:
        deduped = _filter_last_24h(deduped)

    return deduped
