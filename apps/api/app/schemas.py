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
    errors: list[ErrorItem] = Field(default_factory=list)


class ResearchResults(BaseModel):
    dart: Optional[dict[str, Any]] = None
    sec: Optional[dict[str, Any]] = None
    youtube: list[dict[str, Any]] = Field(default_factory=list)
    papers: list[dict[str, Any]] = Field(default_factory=list)
    reports: list[dict[str, Any]] = Field(default_factory=list)
    news: list[dict[str, Any]] = Field(default_factory=list)  # NEW


class ResearchResponse(BaseModel):
    query: str
    slug: str
    results: ResearchResults
    meta: ResearchMeta
