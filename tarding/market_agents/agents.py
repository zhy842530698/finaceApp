from __future__ import annotations

import json
from typing import Callable

from market_agents.llm import LLMClient
from market_agents.schemas import (
    AnalysisState, AnalystReport, DebateArgument, FinalDecision,
    ResearchConclusion, RiskReport,
)


def _json(value) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, default=str)


def technical_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        snapshot = state["market_snapshot"]
        prompt = _json({"latest_price": snapshot.latest_price, "indicators": snapshot.indicators,
                        "quality": snapshot.quality_score})
        report = llm.structured("你是技术分析师。只解释代码已经计算的指标，不自行计算或编造数值。", prompt, AnalystReport)
        return {"technical_report": report}
    return run


def fundamentals_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        snapshot = state["market_snapshot"]
        report = llm.structured("你是基本面分析师。缺失字段必须明确说明，禁止补全或编造。",
                                _json(snapshot.fundamentals), AnalystReport)
        return {"fundamentals_report": report}
    return run


def news_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        snapshot = state["market_snapshot"]
        report = llm.structured("你是新闻和市场情绪分析师。仅使用给出的、有来源且不晚于分析日的新闻。",
                                _json(snapshot.news), AnalystReport)
        return {"news_report": report}
    return run


def bull_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        round_no = state.get("debate_round", 0) + 1
        context = {"round": round_no, "technical": state["technical_report"],
                   "fundamentals": state["fundamentals_report"], "news": state["news_report"],
                   "latest_bear": state.get("bear_arguments", [])[-1:] }
        result = llm.structured("你是多头研究员。提出最强上涨逻辑，并逐条回应最新空头质疑。", _json(context), DebateArgument)
        result.round = round_no
        return {"bull_arguments": [result], "debate_round": round_no}
    return run


def bear_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        context = {"round": state["debate_round"], "reports": [state["technical_report"],
                   state["fundamentals_report"], state["news_report"]],
                   "latest_bull": state.get("bull_arguments", [])[-1:]}
        result = llm.structured("你是空头研究员。必须针对最新多头论点反驳，检查估值、盈利、技术、宏观、流动性和数据漏洞。",
                                _json(context), DebateArgument)
        result.round = state["debate_round"]
        return {"bear_arguments": [result]}
    return run


def research_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        context = {"reports": [state["technical_report"], state["fundamentals_report"], state["news_report"]],
                   "bull": state["bull_arguments"], "bear": state["bear_arguments"],
                   "data_quality": state["market_snapshot"].quality_score}
        return {"research_conclusion": llm.structured("你是研究经理。综合裁决研究观点，但不得下单。",
                                                      _json(context), ResearchConclusion)}
    return run


def risk_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        snapshot = state["market_snapshot"]
        context = {"research": state["research_conclusion"], "volatility": snapshot.indicators.get("annualized_volatility"),
                   "quality": snapshot.quality_score, "warnings": snapshot.warnings,
                   "filtered_counts": snapshot.filtered_counts}
        return {"risk_report": llm.structured("你是独立风险经理。审查损失、完整性、仓位、集中度、流动性和未来信息泄漏。",
                                              _json(context), RiskReport)}
    return run


def portfolio_node(llm: LLMClient) -> Callable:
    def run(state: AnalysisState):
        snapshot = state["market_snapshot"]
        decision = llm.structured("你是组合经理。根据研究和风控输出建议；这不是交易指令，不得连接券商。",
                                  _json({"research": state["research_conclusion"], "risk": state["risk_report"]}),
                                  FinalDecision)
        decision.snapshot_id = snapshot.snapshot_id
        decision.position_size_pct = min(decision.position_size_pct, state["risk_report"].maximum_position_pct)
        if snapshot.fatal_errors:
            decision.signal, decision.confidence, decision.position_size_pct = "HOLD", 0, 0
            decision.rationale = "数据存在致命错误，禁止生成可执行投资结论。"
        return {"final_decision": decision}
    return run
