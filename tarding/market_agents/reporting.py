from __future__ import annotations

import json
from pathlib import Path

from market_agents.schemas import AnalysisState


def _dump(path: Path, value) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def save_reports(state: AnalysisState, output_root: Path) -> Path:
    target = Path(output_root) / state["ticker"] / state["analysis_date"]
    target.mkdir(parents=True, exist_ok=True)
    mapping = {
        "snapshot.json": state["market_snapshot"],
        "technical_report.json": state["technical_report"],
        "fundamentals_report.json": state["fundamentals_report"],
        "news_report.json": state["news_report"],
        "debate.json": {"bull_arguments": state["bull_arguments"], "bear_arguments": state["bear_arguments"]},
        "research_conclusion.json": state["research_conclusion"],
        "risk_report.json": state["risk_report"],
        "final_decision.json": state["final_decision"],
        "agent_audit.json": {
            "snapshot_id": state["market_snapshot"].snapshot_id,
            "agent_inputs": {
                "technical": ["latest_price", "indicators", "quality_score"],
                "fundamentals": ["fundamentals"],
                "news": ["news"],
                "bull_bear": ["three_reports", "opponent_latest_argument"],
                "risk": ["research_conclusion", "quality", "volatility", "filtered_counts"],
            },
            "errors": state.get("errors", []),
        },
    }
    for name, value in mapping.items():
        _dump(target / name, value)
    return target


def format_report(state: AnalysisState) -> str:
    def report(title, value):
        evidence = "\n".join(f"- {x}" for x in value.evidence)
        risks = "\n".join(f"- {x}" for x in value.risks)
        return f"[{title}]\n{value.summary}\n证据：\n{evidence}\n风险：\n{risks}\n评分：{value.score:.2f}"

    bull = "\n".join(f"第{x.round}轮：{x.thesis}" for x in state["bull_arguments"])
    bear = "\n".join(f"第{x.round}轮：{x.thesis}" for x in state["bear_arguments"])
    risk, final = state["risk_report"], state["final_decision"]
    return "\n\n".join([
        report("技术面", state["technical_report"]),
        report("基本面", state["fundamentals_report"]),
        report("新闻情绪", state["news_report"]),
        f"[多头观点]\n{bull}", f"[空头观点]\n{bear}",
        f"[风险经理]\n{risk.summary}\n风险等级：{risk.risk_level}\n"
        + "\n".join(f"- {x}" for x in risk.key_risks),
        f"[最终结论]\n信号：{final.signal}\n置信度：{final.confidence:.0%}\n"
        f"建议仓位：{final.position_size_pct}%\n理由：{final.rationale}\n"
        f"风控：{'；'.join(final.risk_controls)}\n快照：{final.snapshot_id}",
    ])


def answer_followup(question: str, state: AnalysisState) -> str:
    q = question.strip()
    if "多头" in q:
        return "\n".join(f"第{x.round}轮：{x.thesis}；依据：{'；'.join(x.evidence)}" for x in state["bull_arguments"])
    if "空头" in q or "风险" in q:
        bear = state["bear_arguments"][-1]
        return f"空头核心观点：{bear.thesis}\n风险经理：{'；'.join(state['risk_report'].key_risks)}"
    if "技术" in q:
        return state["technical_report"].summary + "\n" + "；".join(state["technical_report"].evidence)
    if "最终" in q or "建议" in q or "买入" in q:
        d = state["final_decision"]
        return f"{d.signal}，置信度 {d.confidence:.0%}，建议仓位 {d.position_size_pct}%。{d.rationale}"
    return "你可以继续问：为什么建议买入、多头核心依据、空头最大风险、技术面或最终建议。"

