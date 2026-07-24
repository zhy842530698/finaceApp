from __future__ import annotations

from datetime import date
from typing import Callable

from langgraph.graph import END, START, StateGraph

from market_agents import agents
from market_agents.config import Settings
from market_agents.data import DataService
from market_agents.llm import LLMClient
from market_agents.parser import parse_request
from market_agents.schemas import AnalysisState, AnalystReport


def _safe(name: str, fn: Callable):
    def run(state):
        try:
            return fn(state)
        except Exception as exc:
            result = {"errors": [f"{name}: {type(exc).__name__}: {exc}"]}
            field = {"technical": "technical_report", "fundamentals": "fundamentals_report",
                     "news": "news_report"}.get(name)
            if field:
                result[field] = AnalystReport(summary=f"{name} Agent 执行失败", evidence=[],
                                              risks=["该分支结果不可用"], score=0)
            return result
    return run


def build_graph(settings: Settings, data_service: DataService, llm: LLMClient):
    graph = StateGraph(AnalysisState)

    def identify(state: AnalysisState):
        parsed = parse_request(state["request"])
        return {"ticker": parsed.ticker, "analysis_date": parsed.analysis_date.isoformat(),
                "bull_arguments": [], "bear_arguments": [], "debate_round": 0, "errors": []}

    def snapshot(state: AnalysisState):
        snap = data_service.create_snapshot(state["ticker"], date.fromisoformat(state["analysis_date"]))
        return {"market_snapshot": snap}

    graph.add_node("identify", identify)
    graph.add_node("snapshot", snapshot)
    graph.add_node("technical", _safe("technical", agents.technical_node(llm)))
    graph.add_node("fundamentals", _safe("fundamentals", agents.fundamentals_node(llm)))
    graph.add_node("news", _safe("news", agents.news_node(llm)))
    graph.add_node("bull", _safe("bull", agents.bull_node(llm)))
    graph.add_node("bear", _safe("bear", agents.bear_node(llm)))
    graph.add_node("research", _safe("research", agents.research_node(llm)))
    graph.add_node("risk", _safe("risk", agents.risk_node(llm)))
    graph.add_node("portfolio", _safe("portfolio", agents.portfolio_node(llm)))

    graph.add_edge(START, "identify")
    graph.add_edge("identify", "snapshot")
    graph.add_edge("snapshot", "technical")
    graph.add_edge("snapshot", "fundamentals")
    graph.add_edge("snapshot", "news")
    graph.add_edge(["technical", "fundamentals", "news"], "bull")
    graph.add_edge("bull", "bear")
    graph.add_conditional_edges(
        "bear",
        lambda state: "bull" if state["debate_round"] < settings.max_debate_rounds else "research",
        {"bull": "bull", "research": "research"},
    )
    graph.add_edge("research", "risk")
    graph.add_edge("risk", "portfolio")
    graph.add_edge("portfolio", END)
    return graph.compile()

