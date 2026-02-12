"""Environment and app config. No hardcoded API keys."""
import os

DART_API_KEY = os.getenv("DART_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
