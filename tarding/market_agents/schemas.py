from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal
import operator

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class NewsItem(BaseModel):
    title: str
    source: str
    published_at: datetime
    url: str
    relevance_score: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)


class MarketSnapshot(BaseModel):
    snapshot_id: str
    ticker: str
    company_name: str | None = None
    asset_type: str = "equity"
    analysis_date: date
    generated_at: datetime
    price_history: list[dict[str, Any]]
    latest_price: dict[str, Any]
    indicators: dict[str, Any]
    fundamentals: dict[str, Any]
    news: list[NewsItem]
    macro: dict[str, Any]
    data_sources: dict[str, Any]
    quality_score: float = Field(ge=0, le=1)
    warnings: list[str] = []
    fatal_errors: list[str] = []
    filtered_counts: dict[str, int] = {}


class AnalystReport(BaseModel):
    summary: str
    evidence: list[str]
    risks: list[str]
    score: float = Field(ge=-1, le=1)


class DebateArgument(BaseModel):
    round: int
    thesis: str
    evidence: list[str]
    rebuttals: list[str]


class ResearchConclusion(BaseModel):
    summary: str
    bull_strength: float = Field(ge=0, le=1)
    bear_strength: float = Field(ge=0, le=1)
    data_quality: float = Field(ge=0, le=1)
    unresolved_questions: list[str]


class RiskReport(BaseModel):
    summary: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "EXTREME"]
    maximum_position_pct: int = Field(ge=0, le=100)
    key_risks: list[str]
    leakage_detected: bool = False


class FinalDecision(BaseModel):
    signal: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    confidence: float = Field(ge=0, le=1)
    position_size_pct: int = Field(ge=0, le=100)
    rationale: str
    risk_controls: list[str]
    snapshot_id: str


class AnalysisState(TypedDict, total=False):
    request: str
    ticker: str
    analysis_date: str
    market_snapshot: MarketSnapshot
    technical_report: AnalystReport
    fundamentals_report: AnalystReport
    news_report: AnalystReport
    bull_arguments: Annotated[list[DebateArgument], operator.add]
    bear_arguments: Annotated[list[DebateArgument], operator.add]
    debate_round: int
    research_conclusion: ResearchConclusion
    risk_report: RiskReport
    final_decision: FinalDecision
    errors: Annotated[list[str], operator.add]

