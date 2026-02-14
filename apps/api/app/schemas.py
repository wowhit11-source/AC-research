# apps/api/app/schemas.py
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., description="Ticker / code / keyword")


class ErrorItem(BaseModel):
    source: str
    message: str


class ResearchMeta(BaseModel):
    elapsed_ms: float
    errors: list[ErrorItem] = []


class ResearchResults(BaseModel):
    dart: Optional[dict[str, Any]] = None
    sec: Optional[dict[str, Any]] = None
    youtube: list[dict[str, Any]] = []
    papers: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []


class ResearchResponse(BaseModel):
    query: str
    slug: str
    results: ResearchResults
    meta: ResearchMeta
