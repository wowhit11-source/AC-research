"""Environment and app config. No hardcoded API keys."""
import os


def _get_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else None


DART_API_KEY = _get_env("DART_API_KEY")
YOUTUBE_API_KEY = _get_env("YOUTUBE_API_KEY")

# News APIs
NEWS_API_KEY = _get_env("NEWS_API_KEY")  # NewsAPI.org 등 영문 뉴스용

# NAVER 뉴스 검색 API
NAVER_CLIENT_ID = _get_env("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _get_env("NAVER_CLIENT_SECRET")
