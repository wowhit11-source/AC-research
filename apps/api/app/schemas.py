# apps/api/app/schemas.py
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., description="Ticker / code / keyword")


class MultiResearchRequest(BaseModel):
    queries: list[str] = Field(..., description="검색어 목록 (줄바꿈으로 구분된 것을 split해서 전달)")
    max_results: int = Field(default=10, ge=1, le=50, description="유튜브/논문/뉴스/리포트 검색어당 max_results")


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
