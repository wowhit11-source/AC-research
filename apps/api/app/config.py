"""Environment and app config. No hardcoded API keys."""
from __future__ import annotations

import os
from typing import Optional


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else None


# 공시 / 유튜브
DART_API_KEY = _get_env("DART_API_KEY")
YOUTUBE_API_KEY = _get_env("YOUTUBE_API_KEY")

# NewsAPI (영문 뉴스)
NEWS_API_KEY = _get_env("NEWS_API_KEY")

# NAVER 뉴스 검색 API (한글 뉴스)
NAVER_CLIENT_ID = _get_env("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _get_env("NAVER_CLIENT_SECRET")
