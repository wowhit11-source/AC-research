# -*- coding: utf-8 -*-
"""
국내 주식 재무제표 수집 (DART Open API).
종목번호(6자리)로 최근 5년 사업보고서 + 최근 4분기 분기/반기보고서 목록을 수집.
"""
import io
import os
import re
import sys
import zipfile
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import requests

DART_API_KEY = os.getenv("DART_API_KEY")
if not DART_API_KEY:
    raise ValueError("DART_API_KEY 환경변수가 설정되지 않았습니다.")

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
DART_CORPCODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DART_VIEW_URL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}"

# 사업보고서(연간), 반기/1·3분기(분기)
ANNUAL_KEYWORDS = ("사업보고서",)
QUARTERLY_KEYWORDS = ("반기보고서", "1분기보고서", "3분기보고서")


def _get_corp_code_from_stock_code(stock_code: str) -> tuple[str, str]:
    """종목번호(6자리) -> (corp_code 8자리, corp_name). corpCode ZIP 다운로드 후 XML 파싱."""
    code = re.sub(r"\D", "", stock_code)
    if len(code) < 6:
        raise ValueError(f"종목번호는 6자리 이상이어야 합니다: {stock_code}")
    code = code.zfill(6)

    resp = requests.get(DART_CORPCODE_URL, params={"crtfc_key": DART_API_KEY}, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as z:
        names = z.namelist()
        xml_name = next((n for n in names if n.lower().endswith(".xml")), names[0])
        with z.open(xml_name) as f:
            tree = ET.parse(f)
    root = tree.getroot()
    for c in root.findall(".//list"):
        sc = (c.findtext("stock_code") or "").strip()
        if sc == code:
            corp_code = (c.findtext("corp_code") or "").strip()
            corp_name = (c.findtext("corp_name") or "").strip()
            return corp_code, corp_name
    raise ValueError(f"종목번호에 해당하는 회사를 찾을 수 없습니다: {stock_code}")


def _fetch_list(corp_code: str, bgn_de: str, end_de: str) -> list[dict]:
    """공시목록 조회 (list.json)."""
    all_items = []
    page_no = 1
    while True:
        r = requests.get(
            DART_LIST_URL,
            params={
                "crtfc_key": DART_API_KEY,
                "corp_code": corp_code,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "page_no": page_no,
                "page_count": 100,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "000":
            raise RuntimeError(data.get("message", "DART API 오류"))
        lst = data.get("list") or []
        if not lst:
            break
        all_items.extend(lst)
        if len(lst) < 100:
            break
        page_no += 1
    return all_items


def _parse_rcept_dt(dt_str: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD."""
    if not dt_str or len(dt_str) < 8:
        return dt_str
    return f"{dt_str[:4]}-{dt_str[4:6]}-{dt_str[6:8]}"


def collect_dart_reports(stock_code: str) -> list[dict]:
    """
    종목번호(6자리)로 최근 5년 사업보고서 + 최근 4분기 분기/반기보고서 수집.
    반환: list[dict] with 회사명, 보고서종류, 기준연도분기, 제출일, url
    """
    corp_code, corp_name = _get_corp_code_from_stock_code(stock_code)
    end_date = datetime.now()
    bgn_date = end_date - timedelta(days=365 * 5)
    bgn_de = bgn_date.strftime("%Y%m%d")
    end_de = end_date.strftime("%Y%m%d")

    raw = _fetch_list(corp_code, bgn_de, end_de)
    results = []

    for item in raw:
        report_nm = (item.get("report_nm") or "").strip()
        rcept_no = (item.get("rcept_no") or "").strip()
        rcept_dt = (item.get("rcept_dt") or "").strip()
        if not rcept_no:
            continue

        if any(k in report_nm for k in ANNUAL_KEYWORDS):
            kind = "연간"
            base = re.search(r"\((\d{4})\)", report_nm)
            base_str = base.group(1) if base else report_nm[:4] if len(report_nm) >= 4 else ""
        elif any(k in report_nm for k in QUARTERLY_KEYWORDS):
            kind = "분기"
            base = re.search(r"(\d{4}년?\s*[반기\d]?분기)", report_nm) or re.search(r"\((\d{4}[-\s]\d)", report_nm)
            base_str = base.group(1).strip() if base else (report_nm[:20] if len(report_nm) >= 20 else report_nm)
        else:
            continue

        results.append({
            "회사명": corp_name,
            "보고서 종류": kind,
            "기준연도/분기": base_str,
            "제출일": _parse_rcept_dt(rcept_dt),
            "url": DART_VIEW_URL.format(rcp_no=rcept_no),
        })

    # 연간: 최근 5년만 유지. 분기: 최근 4개만 유지
    annual = [r for r in results if r["보고서 종류"] == "연간"]
    quarterly = [r for r in results if r["보고서 종류"] == "분기"]
    annual.sort(key=lambda x: x["제출일"], reverse=True)
    quarterly.sort(key=lambda x: x["제출일"], reverse=True)
    annual = annual[:5]
    quarterly = quarterly[:4]
    combined = annual + quarterly
    combined.sort(key=lambda x: x["제출일"], reverse=True)
    return combined
