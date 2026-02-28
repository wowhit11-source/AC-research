# -*- coding: utf-8 -*-
"""
AC-research — Streamlit 웹 리서치 앱.
검색어 하나로 미국 SEC / 국내 DART 재무제표, 유튜브, 논문, 리포트, 뉴스를 한 번에 검색하고
결과를 엑셀로 다운로드합니다.

실행 방법 (프로젝트 루트에서):
    streamlit run app.py
    (또는) python -m streamlit run app.py --server.port 8503
"""
import base64
import re
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent

# .env 파일 로드 (프로젝트 루트)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
ASSETS_DIR = BASE_DIR / "assets"
LOGO_DIR = BASE_DIR / "assets" / "logos"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# apps/api를 sys.path에 추가해 app.config 의존성 해결
_API_DIR = BASE_DIR / "apps" / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from src.paper_scraper import search_papers
from src.sec_scraper import collect_sec_links
from src.youtube_scraper import search_youtube_videos
from src.report_scraper import search_reports

# 뉴스: apps/api/app/services/news.py 직접 사용
try:
    from app.services.news import search_news_articles
    def news_api_configured() -> bool:
        import os
        news_key = (os.getenv("NEWS_API_KEY") or "").strip()
        naver_id = (os.getenv("NAVER_CLIENT_ID") or "").strip()
        naver_secret = (os.getenv("NAVER_CLIENT_SECRET") or "").strip()
        return bool(news_key or (naver_id and naver_secret))
except ImportError:
    from src.news_scraper import search_news_articles, news_api_configured

try:
    from src.dart_scraper import collect_dart_reports
    DART_AVAILABLE = True
except (ValueError, Exception):
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


def _img_b64(name: str) -> str:
    """로고 파일을 base64 data URI로 반환. 없으면 빈 문자열."""
    p = safe_logo_path(name)
    if p is None:
        return ""
    try:
        raw = Path(p).read_bytes()
        ext = Path(p).suffix.lstrip(".").lower()
        mime = "image/svg+xml" if ext == "svg" else f"image/{ext or 'png'}"
        return f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    except Exception:
        return ""


# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AC-research", layout="wide")
st.title("AC-research")
st.markdown(
    "키워드 하나로 **미국 SEC / 국내 DART 재무제표**, **유튜브**, **논문**, **리포트**, **뉴스**를 "
    "한 번에 검색하는 리서치 도구입니다."
)

# ── 검색 영역 ─────────────────────────────────────────────────────────────────
query_input = st.text_input(
    "검색어 또는 티커 (재무제표는 미국주식=티커, 국내주식=종목번호, 나머지=검색어 사용)",
    placeholder="예: DIS, 005930, AI inference chip",
    key="query",
)

# ── 소스 선택 토글 ────────────────────────────────────────────────────────────
_ALL_SOURCES = ["재무제표(SEC)", "재무제표(DART)", "유튜브", "논문", "리포트", "뉴스"]
for _src in _ALL_SOURCES:
    if f"src_{_src}" not in st.session_state:
        st.session_state[f"src_{_src}"] = False

# 숨겨진 st.checkbox로 상태 관리 (HTML 버튼이 JS로 이를 클릭)
import json as _json

# 숨김 CSS
st.markdown("""
<style>
div[data-testid="stCheckbox"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

_cb_cols = st.columns(len(_ALL_SOURCES))
for _col, _src in zip(_cb_cols, _ALL_SOURCES):
    with _col:
        st.checkbox(_src, key=f"src_{_src}", label_visibility="collapsed")

# 현재 선택 상태 + 소스 목록을 JS에 전달해 커스텀 pill 버튼 렌더링
_states = {s: st.session_state[f"src_{s}"] for s in _ALL_SOURCES}
_states_json = _json.dumps(_states)
_sources_json = _json.dumps(_ALL_SOURCES)

components.html(f"""
<style>
  body {{ margin:0; padding:0; background:transparent; }}
  #pill-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 4px 0 2px 0;
  }}
  .pill {{
    padding: 4px 14px;
    font-size: 12.5px;
    font-weight: 500;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.22);
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.75);
    cursor: pointer;
    white-space: nowrap;
    transition: background 100ms, border-color 100ms, color 100ms;
    line-height: 1.5;
    font-family: inherit;
    outline: none;
  }}
  .pill:hover {{
    background: rgba(255,255,255,0.13);
    border-color: rgba(255,255,255,0.40);
    color: #fff;
  }}
  .pill.on {{
    background: rgba(220,53,69,0.22);
    border-color: rgba(220,53,69,0.65);
    color: #ff8088;
    font-weight: 700;
  }}
  .pill.on:hover {{
    background: rgba(220,53,69,0.32);
    border-color: rgba(220,53,69,0.85);
    color: #ffb3b8;
  }}
</style>

<div id="pill-row"></div>

<script>
(function() {{
  var sources = {_sources_json};
  var states  = {_states_json};
  var row = document.getElementById('pill-row');

  sources.forEach(function(src) {{
    var btn = document.createElement('button');
    btn.className = 'pill' + (states[src] ? ' on' : '');
    btn.textContent = src;

    btn.addEventListener('click', function() {{
      // 부모 Streamlit 문서에서 해당 소스의 checkbox input 찾아 클릭
      var labels = window.parent.document.querySelectorAll(
        'div[data-testid="stCheckbox"] label'
      );
      for (var i = 0; i < labels.length; i++) {{
        if (labels[i].textContent.trim() === src) {{
          labels[i].click();
          break;
        }}
      }}
    }});

    row.appendChild(btn);
  }});
}})();
</script>
""", height=42, scrolling=False)

options = [s for s in _ALL_SOURCES if st.session_state[f"src_{s}"]]

# ── 단일 검색 버튼 ────────────────────────────────────────────────────────────
search_clicked = st.button("검색", use_container_width=True)

# ── 다중 검색 영역 ────────────────────────────────────────────────────────────
multi_query_input = st.text_area(
    "다중 검색어 (줄바꿈으로 구분)",
    placeholder="예:\nDIS\nAAPL\nAI inference chip",
    key="multi_query",
    height=120,
)
multi_search_clicked = st.button("다중 검색", use_container_width=True)

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
for _key in ["sec_df", "korea_sec_df", "yt_df", "paper_df", "report_df", "news_df", "excel_bytes"]:
    if _key not in st.session_state:
        st.session_state[_key] = None
if "download_filename" not in st.session_state:
    st.session_state.download_filename = "research.xlsx"


# ── 공통 헬퍼: 단일 쿼리 검색 ────────────────────────────────────────────────
def _run_single_search(q: str, opts: list, max_yt: int = 30, max_paper: int = 30,
                       max_report: int = 30, max_news: int = 30):
    """단일 검색어 q에 대해 opts 소스를 검색. 결과 dict 반환."""
    sec_df = korea_sec_df = yt_df = paper_df = report_df = news_df = None
    errors = []

    want_sec = "재무제표(SEC)" in opts
    want_dart = "재무제표(DART)" in opts

    if want_sec or want_dart:
        if is_korea_stock(q):
            # 국내 종목 → DART
            if not DART_AVAILABLE:
                st.error(f"[{q}] DART API 키가 설정되지 않았습니다.")
                korea_sec_df = pd.DataFrame(columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url"])
            else:
                with st.spinner(f"[{q}] DART 수집 중..."):
                    try:
                        rows = collect_dart_reports(q)
                        if rows:
                            korea_sec_df = pd.DataFrame(rows)
                            korea_sec_df["query"] = q
                        else:
                            korea_sec_df = pd.DataFrame(
                                columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url", "query"]
                            )
                    except Exception as e:
                        if "DART_API_KEY" in str(e) or "설정되지 않았습니다" in str(e):
                            st.error(f"[{q}] DART API 키가 설정되지 않았습니다.")
                        else:
                            errors.append(f"DART [{q}]: {e}")
                        korea_sec_df = pd.DataFrame(
                            columns=["회사명", "보고서 종류", "기준연도/분기", "제출일", "url", "query"]
                        )
        else:
            # 미국 티커 → SEC
            with st.spinner(f"[{q}] SEC 수집 중..."):
                try:
                    rows = collect_sec_links(q.upper())
                    if rows:
                        sec_df = pd.DataFrame([
                            {
                                "query": q,
                                "ticker": r.get("ticker", ""),
                                "source_type": r.get("source_type", "SEC"),
                                "published_date": r.get("published_date", ""),
                                "url": r.get("url", ""),
                            }
                            for r in rows
                        ])
                    else:
                        sec_df = pd.DataFrame(
                            columns=["query", "ticker", "source_type", "published_date", "url"]
                        )
                except Exception as e:
                    errors.append(f"SEC [{q}]: {e}")
                    sec_df = pd.DataFrame(
                        columns=["query", "ticker", "source_type", "published_date", "url"]
                    )

    if "유튜브" in opts:
        with st.spinner(f"[{q}] 유튜브 검색 중..."):
            try:
                rows = search_youtube_videos(q, max_results=max_yt)
                if rows:
                    for r in rows:
                        r["query"] = q
                    yt_df = pd.DataFrame(rows)
                else:
                    yt_df = pd.DataFrame(
                        columns=["title", "url", "duration_minutes", "published_at", "query"]
                    )
            except Exception as e:
                errors.append(f"유튜브 [{q}]: {e}")
                yt_df = pd.DataFrame(
                    columns=["title", "url", "duration_minutes", "published_at", "query"]
                )

    if "논문" in opts:
        with st.spinner(f"[{q}] 논문 검색 중 (PDF 있는 논문만)..."):
            try:
                rows = search_papers(q, max_results=max_paper)
                if rows:
                    for r in rows:
                        r.setdefault("query", q)
                    paper_df = pd.DataFrame(rows)
                else:
                    paper_df = pd.DataFrame(
                        columns=["title", "authors", "year", "venue", "citation_count",
                                 "is_open_access", "main_url", "pdf_url", "query"]
                    )
            except Exception as e:
                errors.append(f"논문 [{q}]: {e}")
                paper_df = pd.DataFrame(
                    columns=["title", "authors", "year", "venue", "citation_count",
                             "is_open_access", "main_url", "pdf_url", "query"]
                )

    if "리포트" in opts:
        with st.spinner(f"[{q}] 리포트 검색 중..."):
            try:
                rows = search_reports(q, max_results=max_report)
                if rows:
                    report_df = pd.DataFrame(rows)
                else:
                    report_df = pd.DataFrame(
                        columns=["source", "title", "url", "published_date", "snippet", "score", "query"]
                    )
            except Exception as e:
                errors.append(f"리포트 [{q}]: {e}")
                report_df = pd.DataFrame(
                    columns=["source", "title", "url", "published_date", "snippet", "score", "query"]
                )

    if "뉴스" in opts:
        if not news_api_configured():
            st.warning(
                "뉴스 검색을 사용하려면 환경변수를 설정해 주세요.\n"
                "영문 뉴스: `NEWS_API_KEY` (newsapi.org)\n"
                "한글 뉴스: `NAVER_CLIENT_ID` + `NAVER_CLIENT_SECRET` (네이버 검색 API)"
            )
            news_df = pd.DataFrame(
                columns=["title", "url", "published_at", "source_name", "query"]
            )
        else:
            with st.spinner(f"[{q}] 뉴스 검색 중..."):
                try:
                    rows = search_news_articles(q, max_results=max_news)
                    if rows:
                        news_df = pd.DataFrame(rows)
                    else:
                        news_df = pd.DataFrame(
                            columns=["title", "url", "published_at", "source_name", "query"]
                        )
                except Exception as e:
                    errors.append(f"뉴스 [{q}]: {e}")
                    news_df = pd.DataFrame(
                        columns=["title", "url", "published_at", "source_name", "query"]
                    )

    for err in errors:
        st.error(err)

    return sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df


def _build_excel(opts, sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        if ("재무제표(SEC)" in opts or "재무제표(DART)" in opts) and sec_df is not None:
            sec_df.to_excel(writer, sheet_name="SEC", index=False)
        if ("재무제표(SEC)" in opts or "재무제표(DART)" in opts) and korea_sec_df is not None:
            korea_sec_df.to_excel(writer, sheet_name="KOREA_SEC", index=False)
        if "유튜브" in opts and yt_df is not None:
            yt_df.to_excel(writer, sheet_name="YouTube", index=False)
        if "논문" in opts and paper_df is not None:
            paper_df.to_excel(writer, sheet_name="Papers", index=False)
        if "리포트" in opts and report_df is not None:
            report_df.to_excel(writer, sheet_name="Reports", index=False)
        if "뉴스" in opts and news_df is not None:
            news_df.to_excel(writer, sheet_name="News", index=False)
    return buffer.getvalue()


# ── 단일 검색 ─────────────────────────────────────────────────────────────────
if search_clicked:
    q = (query_input or "").strip()
    if not q:
        st.warning("검색어를 입력해 주세요.")
    elif not options:
        st.warning("최소 하나 이상의 소스를 선택해 주세요.")
    else:
        sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df = _run_single_search(
            q, options,
            max_yt=30, max_paper=30, max_report=30, max_news=30,
        )
        st.session_state.sec_df = sec_df
        st.session_state.korea_sec_df = korea_sec_df
        st.session_state.yt_df = yt_df
        st.session_state.paper_df = paper_df
        st.session_state.report_df = report_df
        st.session_state.news_df = news_df
        st.session_state.excel_bytes = _build_excel(
            options, sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df
        )
        st.session_state.download_filename = f"research_{slugify(q)}.xlsx"

# ── 다중 검색 ─────────────────────────────────────────────────────────────────
if multi_search_clicked:
    raw_queries = [line.strip() for line in (multi_query_input or "").splitlines() if line.strip()]
    if not raw_queries:
        st.warning("다중 검색어를 입력해 주세요.")
    elif not options:
        st.warning("최소 하나 이상의 소스를 선택해 주세요.")
    else:
        all_sec = []
        all_korea_sec = []
        all_yt = []
        all_paper = []
        all_report = []
        all_news = []

        total = len(raw_queries)
        progress_bar = st.progress(0, text="다중 검색 시작...")

        for idx, q in enumerate(raw_queries):
            progress_bar.progress(idx / total, text=f"[{idx + 1}/{total}] '{q}' 검색 중...")
            sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df = _run_single_search(
                q, options,
                max_yt=10, max_paper=10, max_report=10, max_news=10,
            )
            if sec_df is not None:
                all_sec.append(sec_df)
            if korea_sec_df is not None:
                all_korea_sec.append(korea_sec_df)
            if yt_df is not None:
                all_yt.append(yt_df)
            if paper_df is not None:
                all_paper.append(paper_df)
            if report_df is not None:
                all_report.append(report_df)
            if news_df is not None:
                all_news.append(news_df)

        progress_bar.progress(1.0, text="다중 검색 완료!")

        sec_df = pd.concat(all_sec, ignore_index=True) if all_sec else None
        korea_sec_df = pd.concat(all_korea_sec, ignore_index=True) if all_korea_sec else None
        yt_df = pd.concat(all_yt, ignore_index=True) if all_yt else None
        paper_df = pd.concat(all_paper, ignore_index=True) if all_paper else None
        report_df = pd.concat(all_report, ignore_index=True) if all_report else None
        news_df = pd.concat(all_news, ignore_index=True) if all_news else None

        st.session_state.sec_df = sec_df
        st.session_state.korea_sec_df = korea_sec_df
        st.session_state.yt_df = yt_df
        st.session_state.paper_df = paper_df
        st.session_state.report_df = report_df
        st.session_state.news_df = news_df

        slug = slugify("_".join(raw_queries[:3]))
        st.session_state.excel_bytes = _build_excel(
            options, sec_df, korea_sec_df, yt_df, paper_df, report_df, news_df
        )
        st.session_state.download_filename = f"research_multi_{slug}.xlsx"

# ── 리서치 보조 도구 (사이드바) ────────────────────────────────────────────────
st.sidebar.markdown("## 리서치 보조 도구")

_TOOLS = [
    ("ChatGPT", "https://chat.openai.com", "chatgpt.png.png"),
    ("Google Gemini", "https://gemini.google.com", "gemini.png.png"),
    ("Anthropic Claude", "https://claude.ai", "claude.png.png"),
    ("Google NotebookLM", "https://notebooklm.google.com", "notebooklm.png.png"),
]

_tool_items_html = ""
for _label, _url, _logo in _TOOLS:
    _b64 = _img_b64(_logo)
    _icon_html = (
        f'<img src="{_b64}" style="width:20px;height:20px;object-fit:contain;flex-shrink:0;" />'
        if _b64 else
        '<span style="width:20px;height:20px;display:inline-block;"></span>'
    )
    _tool_items_html += f"""
    <a href="{_url}" target="_blank" rel="noopener noreferrer" style="
        display:flex; align-items:center; gap:10px;
        padding:10px 12px; border-radius:10px;
        border:1px solid rgba(255,255,255,0.10);
        text-decoration:none; color:inherit;
        background:rgba(255,255,255,0.02);
        margin-bottom:8px;
        transition:background 120ms ease;
    ">
      {_icon_html}
      <span style="font-size:14px;">{_label}</span>
    </a>"""

st.sidebar.markdown(_tool_items_html, unsafe_allow_html=True)

# ── 네이버 블로그 배너 (사이드바) ────────────────────────────────────────────
st.sidebar.markdown(
    """
    <a href="https://blog.naver.com/hanryang72" target="_blank" rel="noopener noreferrer"
       style="display:block; text-decoration:none; color:inherit;">
      <div style="
        margin-top:8px;
        padding:14px 16px;
        border-radius:12px;
        background:rgba(255,255,255,0.04);
        border:1px solid rgba(255,255,255,0.10);
        transition:background 140ms ease;
      ">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
          <div style="
            width:26px; height:26px; border-radius:8px;
            background:rgba(3,199,90,0.18);
            border:1px solid rgba(3,199,90,0.35);
            display:flex; align-items:center; justify-content:center;
            font-size:13px; font-weight:800; color:#03c75a;
          ">N</div>
          <span style="font-size:14px; font-weight:800;">ACresearch 센터</span>
        </div>
        <div style="font-size:12px; opacity:0.7; line-height:1.5;">
          ACresearch로 만든 정보를 공유하는 블로그입니다.
        </div>
      </div>
    </a>
    """,
    unsafe_allow_html=True,
)

# ── 엑셀 다운로드 ─────────────────────────────────────────────────────────────
if st.session_state.excel_bytes:
    st.download_button(
        label="엑셀 파일 다운로드",
        data=st.session_state.excel_bytes,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name=st.session_state.download_filename,
        key="download_excel",
    )

# ── 검색 결과 테이블 ──────────────────────────────────────────────────────────
def _url_col(df: pd.DataFrame) -> str | None:
    """df에서 URL 컬럼 이름을 반환. 우선순위: url → pdf_url → main_url → None."""
    for c in ["url", "pdf_url", "main_url"]:
        if c in df.columns:
            return c
    return None


def _show_table(title: str, df: pd.DataFrame, url_key: str) -> None:
    """제목(+ 빨간 Copy URLs 버튼 inline) + 데이터프레임 렌더링."""
    import json

    col = _url_col(df)
    urls: list[str] = []
    if col:
        urls = [u for u in df[col].dropna().astype(str).str.strip() if u]
    n = len(urls)

    if urls:
        urls_json = json.dumps(urls)
        components.html(
            f"""
            <style>
              #btn_{url_key} {{
                display: inline-block;
                padding: 4px 13px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                border: none;
                background: #FF4B4B;
                color: #ffffff;
                cursor: pointer;
                white-space: nowrap;
                vertical-align: middle;
                transition: background 120ms ease, opacity 120ms ease;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              }}
              #btn_{url_key}:hover {{ background: #e03c3c; }}
              #btn_{url_key}:active {{ opacity: 0.8; }}
            </style>
            <div style="display:flex; align-items:center; gap:10px; margin:0; padding:2px 0;">
              <span style="
                font-size: 1.3rem;
                font-weight: 700;
                color: #e6edf3;
                line-height: 1.4;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              ">{title}</span>
              <button id="btn_{url_key}">🔗 Copy URLs ({n}개)</button>
            </div>
            <script>
            (function(){{
              var urls = {urls_json};
              var btn  = document.getElementById('btn_{url_key}');
              btn.addEventListener('click', function(){{
                var text = urls.join('\\n');
                var orig = btn.innerText;
                navigator.clipboard.writeText(text).then(function(){{
                  btn.innerText = '✅ 복사됨 ({n}개)';
                  btn.style.background = '#2ea043';
                  setTimeout(function(){{
                    btn.innerText = orig;
                    btn.style.background = '#FF4B4B';
                  }}, 2000);
                }}).catch(function(){{
                  var ta = document.createElement('textarea');
                  ta.value = text;
                  document.body.appendChild(ta);
                  ta.select();
                  document.execCommand('copy');
                  document.body.removeChild(ta);
                  btn.innerText = '✅ 복사됨 ({n}개)';
                  btn.style.background = '#2ea043';
                  setTimeout(function(){{
                    btn.innerText = orig;
                    btn.style.background = '#FF4B4B';
                  }}, 2000);
                }});
              }});
            }})();
            </script>
            """,
            height=48,
            scrolling=False,
        )
    else:
        st.subheader(title)

    st.dataframe(df, use_container_width=True)


if st.session_state.sec_df is not None:
    _show_table("SEC 결과 (미국)", st.session_state.sec_df, "copy_sec")

if st.session_state.korea_sec_df is not None:
    _show_table("DART 결과 (국내)", st.session_state.korea_sec_df, "copy_dart")

if st.session_state.yt_df is not None:
    _show_table("YouTube 결과", st.session_state.yt_df, "copy_yt")

if st.session_state.paper_df is not None:
    _show_table("논문 결과 (PDF URL 있는 논문만)", st.session_state.paper_df, "copy_paper")

if st.session_state.report_df is not None:
    _show_table("리포트 결과", st.session_state.report_df, "copy_report")

if st.session_state.news_df is not None:
    _show_table("뉴스 결과", st.session_state.news_df, "copy_news")

# ── 사용 안내 ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("사용 안내")
st.markdown("""
**재무제표 검색 안내**

재무제표 검색 시 미국 주식은 티커(symbol), 국내 주식은 종목번호를 기준으로 조회됩니다. 정확한 검색을 위해 티커 또는 종목번호만 단독으로 입력하는 것을 권장합니다.

유튜브 영상이나 논문을 검색할 때 티커 또는 종목번호만으로 검색하면 원하는 결과가 정확히 나오지 않을 수 있습니다. 이 경우에는 기업명 또는 관련 키워드를 함께 활용해 검색하시기 바랍니다.

**뉴스 검색 안내**

뉴스는 한글 쿼리이면 NAVER 뉴스 API, 영문 쿼리이면 NewsAPI.org를 사용합니다. 환경변수(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NEWS_API_KEY)가 설정되어 있어야 합니다.

**사용 방법 (Notebook LM 기준)**

1. Notebook LM에 접속하여 새 노트를 생성합니다.
2. 좌측의 소스 추가 버튼을 클릭한 뒤 웹사이트를 선택합니다.
3. 프로그램에서 검색된 URL을 복사해 붙여넣고 추가합니다.
4. 소스 추가가 완료되면 궁금한 내용을 질문하거나, 스튜디오 기능을 실행하여 분석을 진행합니다.

다른 AI 플랫폼에서도 동일한 방식으로 URL을 추가해 활용하시면 됩니다.
""")
