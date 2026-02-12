#!/usr/bin/env python3
"""
티커(symbol) 기반 URL 수집기
- SEC 연간보고서(10-K) 최근 5년치만 수집 후 CSV 저장
- 수집은 기존 4개 소스에서 수행한 뒤, SEC 10-K만 필터·정렬·상위 5개 유지

# 사용법: python main.py AAPL
# 출력: data/AAPL_links.csv
"""

import argparse
import os

from src.sec_scraper import collect_sec_links
from src.utils import save_to_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="출력 csv 경로 (기본: data/{ticker}_links.csv)"
    )
    args = parser.parse_args()

    ticker = args.ticker.upper()
    output_path = args.output or os.path.join("data", f"{ticker}_links.csv")

    print(f"[시작] 티커: {ticker} | 출력: {output_path}")
    print("-" * 50)

    sec_links = collect_sec_links(ticker)

    print("DEBUG sec_links:", sec_links)

    if not sec_links:
        print("[경고] SEC 링크 없음")
        return

    save_to_csv(sec_links, output_path)
    print(f"[완료] {len(sec_links)}개 SEC 링크 저장 완료")

if __name__ == "__main__":
    main()

