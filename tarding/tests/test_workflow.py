from market_agents.config import Settings
from market_agents.data import DataService
from market_agents.llm.mock import MockLLMClient
from market_agents.reporting import save_reports
from market_agents.workflow import build_graph


def test_full_multi_agent_workflow(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", output_dir=tmp_path / "outputs",
                        max_debate_rounds=2, llm_provider="mock", data_provider="mock")
    graph = build_graph(settings, DataService(settings.data_dir, "mock"), MockLLMClient())
    state = graph.invoke({"request": "分析 NVDA 2026-07-20"})
    assert state["technical_report"]
    assert state["fundamentals_report"]
    assert state["news_report"]
    assert len(state["bull_arguments"]) == 2
    assert len(state["bear_arguments"]) == 2
    assert state["final_decision"].signal in {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}
    target = save_reports(state, settings.output_dir)
    assert (target / "snapshot.json").exists()
    assert (target / "final_decision.json").exists()

