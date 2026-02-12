"""SEC EDGAR 10-K/10-Q link collection. No Streamlit dependency."""
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
    records = []
    for form, date_str, acc, primary in zip(forms, dates, accession_numbers, primary_docs):
        if form not in form_filter:
            continue
        filed_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        if cutoff_date and filed_date < cutoff_date:
            continue
        accession_nodash = acc.replace("-", "")
        cik_no_padding = str(int(cik))
        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_no_padding}/{accession_nodash}/{primary}"
        )
        records.append({
            "source_type": "SEC",
            "url": doc_url,
            "published_date": filed_date.isoformat(),
            "ticker": None,
        })
    records.sort(key=lambda r: r["published_date"], reverse=True)
    if max_items is not None:
        records = records[:max_items]
    return records


def _get_recent_10k_filings(cik: str, years: int = 5) -> list[dict]:
    padded_cik = cik.zfill(10)
    api_url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    resp = _sec_get(api_url, host="data.sec.gov")
    data = resp.json()
    filings = data.get("filings", {}).get("recent", {})
    cutoff = dt.date.today() - dt.timedelta(days=365 * years)
    return _filing_records_from_recent(cik, filings, ["10-K"], cutoff, None)


def _get_recent_10q_filings(cik: str, quarters: int = 4) -> list[dict]:
    padded_cik = cik.zfill(10)
    api_url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    resp = _sec_get(api_url, host="data.sec.gov")
    data = resp.json()
    filings = data.get("filings", {}).get("recent", {})
    return _filing_records_from_recent(cik, filings, ["10-Q"], None, quarters)


def collect_sec_links(ticker: str) -> list[dict]:
    """Recent 5y 10-K + 4 quarters 10-Q. Each dict: source_type, url, published_date, ticker."""
    t = ticker.upper()
    cik = _get_cik_from_ticker(ticker)
    records = _get_recent_10k_filings(cik, years=5) + _get_recent_10q_filings(cik, quarters=4)
    records.sort(key=lambda r: r["published_date"], reverse=True)
    for r in records:
        r["ticker"] = t
    return records
