# -*- coding: utf-8 -*-
"""
AC-research — Streamlit 웹 리서치 앱.
검색어 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문을 한 번에 검색하고 결과를 엑셀로 다운로드합니다.

실행 방법 (프로젝트 루트에서):
    streamlit run app.py
    (또는) python -m streamlit run app.py --server.port 8503
"""
import re
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_DIR = BASE_DIR / "assets" / "logos"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.paper_scraper import search_papers
from src.sec_scraper import collect_sec_links
from src.youtube_scraper import search_youtube_videos

try:
    from src.dart_scraper import collect_dart_reports
    DART_AVAILABLE = True
except ValueError:
    collect_dart_reports = None
    DART_AVAILABLE = False

_SLUG_BAD = re.compile(r"[\s\t/\\:?\"'*<>|]+")


def slugify(text: str) -> str:
    s = (text or "").strip().lower()
    s = _SLUG_BAD.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "research"


def is_korea_stock(query: str) -> bool:
    """입력이 국내 종목번호(숫자 6자리 이상)이면 True."""
    q = (query or "").strip()
    digits_only = re.sub(r"\D", "", q)
    return len(digits_only) >= 6


def safe_logo_path(name: str) -> Path | None:
    """로고 파일 경로를 안전하게 반환. 없으면 None. LOGO_DIR → ASSETS_DIR → 이중확장자 fallback."""
    p = LOGO_DIR / name
    if p.is_file():
        return p
    p = ASSETS_DIR / name
    if p.is_file():
        return p
    if name.endswith(".png"):
        fallback = ASSETS_DIR / (name.replace(".png", ".png.png"))
        if fallback.is_file():
            return fallback
    return None


def sidebar_tool(label: str, url: str) -> None:
    """사이드바용: 링크 버튼만 표시."""
    st.sidebar.link_button(label, url)
    st.sidebar.markdown("---")


# ----- 페이지 설정 -----
st.set_page_config(page_title="AC-research", layout="wide")
st.title("AC-research")
st.markdown("키워드 하나로 **미국 SEC / 국내 DART 재무제표**, **유튜브**, **논문**을 한 번에 검색하는 리서치 도구입니다.")

# ----- 검색 영역 (본문) -----
query_input = st.text_input(
    "검색어 또는 티커 (재무제표는 미국주식=티커, 국내주식=종목번호, 유튜브·논문=검색어 사용)",
    placeholder="예: DIS, 005930, AI inference chip",
    key="query",
)
options = st.multiselect(
    "검색할 소스 (복수 선택 가능)",
    options=["재무제표(SEC)", "유튜브", "논문"],
    default=[],
    key="sources",
)
search_clicked = st.button("검색")

# ----- 세션 상태 -----
if "sec_df" not in st.session_state:
    st.session_state.sec_df = None
if "korea_sec_df" not in st.session_state:
    st.session_state.korea_sec_df = None
if "yt_df" not in st.session_state:
    st.session_state.yt_df = None
if "paper_df" not in st.session_state:
    st.session_state.paper_df = None
if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None
if "download_filename" not in st.session_state:
    st.session_state.download_filename = "research.xlsx"

# ----- 검색 버튼 동작 -----
if search_clicked:
    q = (query_input or "").strip()
    if not q:
        st.warning("검색어를 입력해 주세요.")
    elif not options:
        st.warning("최소 하나 이상의 소스(재무제표, 유튜브, 논문)를 선택해 주세요.")
    else:
        sec_df = None
        korea_sec_df = None
        yt_df = None
        paper_df = None
        errors = []

        if "재무제표(SEC)" in options:
            if is_korea_stock(q):
                if not DART_AVAILABLE:
                    st.error("DART API 키가 설정되지 않았습니다. 실행 안내 문서를 확인하세요.")
                    korea_sec_df = pd.DataFrame(columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url"])
                else:
                    with st.spinner("국내 DART 재무제표 수집 중..."):
                        try:
                            rows = collect_dart_reports(q)
                            if rows:
                                korea_sec_df = pd.DataFrame(rows)
                            else:
                                korea_sec_df = pd.DataFrame(columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url"])
                        except Exception as e:
                            if "DART_API_KEY" in str(e) or "설정되지 않았습니다" in str(e):
                                st.error("DART API 키가 설정되지 않았습니다. 실행 안내 문서를 확인하세요.")
                            else:
                                errors.append(f"DART(국내): {e}")
                            korea_sec_df = pd.DataFrame(columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url"])
            else:
                with st.spinner("미국 SEC 10-K/10-Q 수집 중..."):
                    try:
                        rows = collect_sec_links(q.upper())
                        if rows:
                            sec_df = pd.DataFrame([
                                {
                                    "ticker": r.get("ticker", ""),
                                    "source_type": r.get("source_type", "SEC"),
                                    "published_date": r.get("published_date", ""),
                                    "url": r.get("url", ""),
                                }
                                for r in rows
                            ])
                        else:
                            sec_df = pd.DataFrame(columns=["ticker", "source_type", "published_date", "url"])
                    except Exception as e:
                        errors.append(f"SEC: {e}")
                        sec_df = pd.DataFrame(columns=["ticker", "source_type", "published_date", "url"])

        if "유튜브" in options:
            with st.spinner("유튜브 검색 중..."):
                try:
                    rows = search_youtube_videos(q, max_results=30)
                    if rows:
                        for r in rows:
                            r["query"] = q
                        yt_df = pd.DataFrame(rows)
                    else:
                        yt_df = pd.DataFrame(columns=["title", "url", "duration_minutes", "published_at", "query"])
                except Exception as e:
                    errors.append(f"유튜브: {e}")
                    yt_df = pd.DataFrame(columns=["title", "url", "duration_minutes", "published_at", "query"])

        if "논문" in options:
            with st.spinner("논문 검색 중 (PDF 있는 논문만)..."):
                try:
                    rows = search_papers(q, max_results=30)
                    if rows:
                        paper_df = pd.DataFrame(rows)
                    else:
                        paper_df = pd.DataFrame(columns=[
                            "title", "authors", "year", "venue", "citation_count",
                            "is_open_access", "main_url", "pdf_url", "query",
                        ])
                except Exception as e:
                    errors.append(f"논문: {e}")
                    paper_df = pd.DataFrame(columns=[
                        "title", "authors", "year", "venue", "citation_count",
                        "is_open_access", "main_url", "pdf_url", "query",
                    ])

        for err in errors:
            st.error(err)

        st.session_state.sec_df = sec_df
        st.session_state.korea_sec_df = korea_sec_df
        st.session_state.yt_df = yt_df
        st.session_state.paper_df = paper_df

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            if "재무제표(SEC)" in options and sec_df is not None:
                sec_df.to_excel(writer, sheet_name="SEC", index=False)
            if "재무제표(SEC)" in options and korea_sec_df is not None:
                korea_sec_df.to_excel(writer, sheet_name="KOREA_SEC", index=False)
            if "유튜브" in options and yt_df is not None:
                yt_df.to_excel(writer, sheet_name="YouTube", index=False)
            if "논문" in options and paper_df is not None:
                paper_df.to_excel(writer, sheet_name="Papers", index=False)
        st.session_state.excel_bytes = buffer.getvalue()
        st.session_state.download_filename = f"research_{slugify(q)}.xlsx"

# ----- 리서치 보조 도구 (사이드바) -----
st.sidebar.markdown("## 리서치 보조 도구")
sidebar_tool("ChatGPT (GPT)", "https://chat.openai.com")
sidebar_tool("Google Gemini", "https://gemini.google.com")
sidebar_tool("Anthropic Claude", "https://claude.ai")
sidebar_tool("Google NotebookLM", "https://notebooklm.google.com")

# ----- 실행 방법 (사이드바) -----
st.sidebar.markdown("**실행 방법**")
st.sidebar.code("streamlit run app.py", language="text")

# ----- 엑셀 다운로드 -----
if st.session_state.excel_bytes:
    st.download_button(
        label="엑셀 파일 다운로드",
        data=st.session_state.excel_bytes,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name=st.session_state.download_filename,
        key="download_excel",
    )

# ----- 검색 결과 테이블 -----
if st.session_state.sec_df is not None:
    st.subheader("SEC 결과 (미국)")
    st.dataframe(st.session_state.sec_df, use_container_width=True)

if st.session_state.korea_sec_df is not None:
    st.subheader("DART 결과 (국내)")
    st.dataframe(st.session_state.korea_sec_df, use_container_width=True)

if st.session_state.yt_df is not None:
    st.subheader("YouTube 결과")
    st.dataframe(st.session_state.yt_df, use_container_width=True)

if st.session_state.paper_df is not None:
    st.subheader("논문 결과 (PDF URL 있는 논문만)")
    st.dataframe(st.session_state.paper_df, use_container_width=True)

# ----- 사용 안내 -----
st.markdown("---")
st.subheader("사용 안내")
st.markdown("""
**재무제표 검색 안내**

재무제표 검색 시 미국 주식은 티커(symbol), 국내 주식은 종목번호를 기준으로 조회됩니다. 정확한 검색을 위해 티커 또는 종목번호만 단독으로 입력하는 것을 권장합니다. 다른 단어를 함께 입력할 경우 검색 정확도가 떨어질 수 있습니다.

유튜브 영상이나 논문을 검색할 때 티커 또는 종목번호만으로 검색하면 원하는 결과가 정확히 나오지 않을 수 있습니다. 이 경우에는 기업명 또는 관련 키워드를 함께 활용해 검색하시기 바랍니다.

**사용 방법 (Notebook LM 기준)**

1. Notebook LM에 접속하여 새 노트를 생성합니다.
2. 좌측의 소스 추가 버튼을 클릭한 뒤 웹사이트를 선택합니다.
3. 프로그램에서 검색된 URL을 복사해 붙여넣고 추가합니다. 필요한 URL을 모두 추가합니다.
4. 소스 추가가 완료되면 궁금한 내용을 질문하거나, 스튜디오 기능을 실행하여 분석을 진행합니다.

다른 AI 플랫폼에서도 동일한 방식으로 URL을 추가해 활용하시면 됩니다.
""")
