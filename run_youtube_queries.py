# -*- coding: utf-8 -*-
"""Run youtube_scraper with multiple queries (avoids shell encoding issues)."""
import sys
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.youtube_scraper import search_youtube_videos

for query in ["AI 추론 반도체", "엔비디아 추론칩", "AI inference chip competition"]:
    print(f"\n=== {query} ===\n")
    results = search_youtube_videos(query)
    for r in results:
        print(r)
    print(f"({len(results)} results)")
