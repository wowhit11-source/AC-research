"""Shared utilities."""
import re

_SLUG_BAD = re.compile(r"[\s\t/\\:?\"'*<>|]+")


def slugify(text: str) -> str:
    """Safe filename slug from query: lowercase, bad chars → underscore."""
    s = (text or "").strip().lower()
    s = _SLUG_BAD.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "research"


def is_korea_stock(query: str) -> bool:
    """True if query looks like domestic stock code (6+ digits)."""
    q = (query or "").strip()
    digits_only = re.sub(r"\D", "", q)
    return len(digits_only) >= 6
