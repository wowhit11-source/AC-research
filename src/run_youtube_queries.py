# -*- coding: utf-8 -*-
"""
여러 검색어를 한 번에 실행하여 각각 data/youtube_<slug>.csv로 저장.
아래 QUERIES 리스트를 수정해서 원하는 검색어를 넣어 사용하면 된다.
"""
import os
import sys

# python src/run_youtube_queries.py 로 실행 시 프로젝트 루트를 path에 추가
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.utils import save_to_csv
from src.youtube_scraper import search_youtube_videos, slugify

# 이 리스트를 수정해서 원하는 검색어들을 넣어 사용하면 된다.
QUERIES = [
    "AI inference chip competition",
    "엔비디아 추론칩 경쟁",
    "L4 GPU vs TPU vs custom AI chip",
]


def main() -> None:
    os.makedirs("data", exist_ok=True)
    success_count = 0
    fail_count = 0

    for query in QUERIES:
        try:
            slug = slugify(query)
            output_path = os.path.join("data", f"youtube_{slug}.csv")
            results = search_youtube_videos(query)

            if not results:
                print(f"[경고] '{query}' 검색 결과 없음 (건너뜀)")
                fail_count += 1
                continue

            save_to_csv(results, output_path)
            print(f"[완료] '{query}' → {len(results)}개, 파일: {output_path}")
            success_count += 1
        except Exception as e:
            print(f"[에러] '{query}' 처리 중 에러 발생: {e}")
            fail_count += 1

    print(f"전체 {len(QUERIES)}개 검색어 처리 완료. 성공: {success_count}, 실패/경고: {fail_count}")


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    main()
