"""YouTube Data API v3 search. Uses YOUTUBE_API_KEY from env."""
from datetime import datetime, timedelta, timezone

from app.config import YOUTUBE_API_KEY

try:
    import isodate
    from googleapiclient.discovery import build
except ImportError:
    build = None
    isodate = None


def duration_to_minutes(iso_duration: str) -> float:
    if not isodate:
        return 0.0
    d = isodate.parse_duration(iso_duration)
    return d.total_seconds() / 60.0


def search_youtube_videos(query: str, max_results: int = 30) -> list[dict]:
    """20min+, last 1y, max_results. Returns title, url, duration_minutes, published_at."""
    if not YOUTUBE_API_KEY or not build:
        return []
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
            .list(part="snippet,contentDetails", id=",".join(video_ids))
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
