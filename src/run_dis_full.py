# -*- coding: utf-8 -*-
"""
DIS(디즈니) 리서치 패키지 일괄 수집.
SEC 10-K(최근 5년) + 유튜브 3개 키워드 검색을 한 번에 실행하고 각각 CSV로 저장.
"""
import os
import sys

# 스크립트 기준 프로젝트 루트 path 보정 (Windows/OneDrive 등 경로 이슈 방지)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.sec_scraper import collect_sec_links
from src.utils import save_to_csv
from src.youtube_scraper import search_youtube_videos

DIS_TICKER = "DIS"
SEC_OUTPUT = "DIS_sec_10k.csv"

# 유튜브 검색 키워드 → 저장 파일명( data/ 하위 )
YT_QUERIES = [
    ("Disney earnings call", "youtube_dis_earnings_call.csv"),
    ("Disney financial results", "youtube_dis_financial_results.csv"),
    ("Disney business strategy", "youtube_dis_business_strategy.csv"),
]


def _sec_rows_ordered(rows: list[dict]) -> list[dict]:
    """SEC 결과를 컬럼 순서 ticker, source_type, published_date, url 로 정렬."""
    return [
        {
            "ticker": r.get("ticker", ""),
            "source_type": r.get("source_type", "SEC"),
            "published_date": r.get("published_date", ""),
            "url": r.get("url", ""),
        }
        for r in rows
    ]


def _run_sec() -> None:
    data_dir = os.path.join(_root, "data")
    out_path = os.path.join(data_dir, SEC_OUTPUT)
    try:
        rows = collect_sec_links(DIS_TICKER)
        if not rows:
            print("[경고] SEC 10-K 검색 결과 없음 (건너뜀)")
            return
        ordered = _sec_rows_ordered(rows)
        save_to_csv(ordered, out_path)
        print(f"[SEC] DIS 10-K {len(ordered)}개 저장 완료 → data/{SEC_OUTPUT}")
    except Exception as e:
        print(f"[경고] SEC 수집 실패: {e}")


def _run_youtube() -> None:
    data_dir = os.path.join(_root, "data")
    for query, filename in YT_QUERIES:
        out_path = os.path.join(data_dir, filename)
        try:
            results = search_youtube_videos(query, max_results=30)
            for r in results:
                r["query"] = query
            if not results:
                print(f"[경고] '{query}' 검색 결과 없음 (건너뜀)")
                continue
            save_to_csv(results, out_path)
            print(f"[YT] {query} → {len(results)}개")
        except Exception as e:
            print(f"[경고] YT '{query}' 실패: {e}")


def main() -> None:
    os.makedirs(os.path.join(_root, "data"), exist_ok=True)
    _run_sec()
    _run_youtube()
    print("[완료] DIS 리서치 패키지 생성 완료")


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
