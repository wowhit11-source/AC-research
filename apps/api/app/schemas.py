"""Request/response models."""
from typing import Any

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class ErrorItem(BaseModel):
    source: str  # dart | sec | youtube | papers
    message: str


class ResearchMeta(BaseModel):
    elapsed_ms: float
    errors: list[ErrorItem] = Field(default_factory=list)


class ResearchResults(BaseModel):
    dart: dict[str, Any] | None = None
    sec: dict[str, Any] | None = None
    youtube: list[dict[str, Any]] = Field(default_factory=list)
    papers: list[dict[str, Any]] = Field(default_factory=list)


class ResearchResponse(BaseModel):
    query: str
    slug: str
    results: ResearchResults
    meta: ResearchMeta
