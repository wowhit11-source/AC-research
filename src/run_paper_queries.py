# -*- coding: utf-8 -*-
"""
여러 논문 검색 키워드를 한 번에 실행하여 각각 data/papers_<slug>.csv로 저장.
아래 QUERIES 리스트를 수정해서 원하는 검색어를 넣어 사용하면 된다.
유튜브 run_youtube_queries.py와 동일한 구조로 작성.
"""
import os
import sys

# 스크립트 기준 프로젝트 루트 path 보정 (OneDrive/Windows 등)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.paper_scraper import search_papers
from src.utils import save_to_csv
from src.youtube_scraper import slugify

# 이 리스트를 수정해서 원하는 논문 검색 키워드들을 넣어 사용하면 된다.
QUERIES = [
    "AI inference chip competition",
    "lithium supply chain",
    "small modular reactor economics",
]


def main() -> None:
    data_dir = os.path.join(_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    for query in QUERIES:
        try:
            slug = slugify(query)
            output_path = os.path.join(data_dir, f"papers_{slug}.csv")
            papers = search_papers(query, max_results=30)

            if not papers:
                print(f"[경고] '{query}' 검색 결과 없음 (건너뜀)")
                continue

            save_to_csv(papers, output_path)
            # 상대 경로로 로그 출력 (data/...)
            rel_path = os.path.join("data", f"papers_{slug}.csv")
            print(f'[PAPER] "{query}" → {len(papers)}편 저장: {rel_path}')
        except Exception as e:
            print(f"[에러] '{query}' 처리 중 에러 발생: {e}")

    print("논문 검색 일괄 실행 완료.")


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
