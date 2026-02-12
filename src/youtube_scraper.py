"""
YouTube Data API v3 기반 검색 스크래퍼.
검색어로 영상을 찾고, 20분 이상·최근 1년·최대 30개 조건으로 반환한다.
"""
import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# python src/youtube_scraper.py 로 실행 시 프로젝트 루트를 path에 추가
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)

import isodate
from googleapiclient.discovery import build

from src.utils import save_to_csv

YOUTUBE_API_KEY = "AIzaSyA3_eBaJ7pATItERb4ET723jywcBCPNb6o"

# 파일명에 사용할 수 없는 문자 → 언더스코어로 치환
_SLUG_BAD_CHARS = re.compile(r"[\s\t/\\:?\"'*<>|]+")


def slugify(query: str) -> str:
    """
    검색어를 파일명용 안전한 slug로 변환.
    소문자화, 공백/특수문자 → _, 연속 _ 축약, 앞뒤 _ 제거.
    """
    s = query.strip().lower()
    s = _SLUG_BAD_CHARS.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "query"


def duration_to_minutes(iso_duration: str) -> float:
    """ISO 8601 duration 문자열(예: PT1H23M45S)을 분 단위로 변환."""
    d = isodate.parse_duration(iso_duration)
    return d.total_seconds() / 60.0


def search_youtube_videos(query: str, max_results: int = 30) -> list[dict]:
    """
    검색어로 YouTube 영상 검색.
    조건: 20분 이상, 최근 1년 이내, 최대 max_results개.
    반환: list[dict] with title, url, duration_minutes, published_at.
    """
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    published_after = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")
    results = []
    next_page_token = None
    min_duration_minutes = 20.0

    while len(results) < max_results:
        search_resp = (
            youtube.search()
            .list(
                part="snippet",
                q=query,
                type="video",
                maxResults=50,
                publishedAfter=published_after,
                pageToken=next_page_token or "",
            )
            .execute()
        )

        video_ids = [
            item["id"]["videoId"]
            for item in search_resp.get("items", [])
            if item["id"].get("kind") == "youtube#video"
        ]
        if not video_ids:
            break

        details_resp = (
            youtube.videos()
            .list(
                part="snippet,contentDetails",
                id=",".join(video_ids),
            )
            .execute()
        )

        for item in details_resp.get("items", []):
            vid = item["id"]
            duration_str = item.get("contentDetails", {}).get("duration") or "PT0S"
            try:
                duration_min = duration_to_minutes(duration_str)
            except (ValueError, TypeError):
                continue
            if duration_min < min_duration_minutes:
                continue
            snippet = item.get("snippet", {})
            published_at = snippet.get("publishedAt") or ""
            results.append({
                "title": snippet.get("title") or "",
                "url": f"https://www.youtube.com/watch?v={vid}",
                "duration_minutes": round(duration_min, 2),
                "published_at": published_at,
            })
            if len(results) >= max_results:
                break

        next_page_token = search_resp.get("nextPageToken")
        if not next_page_token:
            break

    return results[:max_results]


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="YouTube 검색어로 영상 검색 후 CSV로 저장 (20분 이상, 최근 1년, 최대 30개)"
    )
    parser.add_argument("query", type=str, help="검색어")
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="출력 CSV 경로 (기본: data/youtube_<slug>.csv)",
    )
    args = parser.parse_args()

    query = args.query
    results = search_youtube_videos(query)

    if args.output:
        output_path = args.output
    else:
        slug = slugify(query)
        output_path = os.path.join("data", f"youtube_{slug}.csv")

    if not results:
        print(f"[경고] 검색 결과가 없습니다: {query}")
        sys.exit(0)

    save_to_csv(results, output_path)
    print(f"[완료] '{query}' 검색 결과 {len(results)}개를 {output_path}에 저장했습니다.")
