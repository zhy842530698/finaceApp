from typing import TypeVar

from pydantic import BaseModel

from market_agents.schemas import (
    AnalystReport, DebateArgument, FinalDecision, ResearchConclusion, RiskReport,
)
from .client import LLMClient

T = TypeVar("T", bound=BaseModel)


class MockLLMClient(LLMClient):
    model_name = "MockLLM"

    def structured(self, system_prompt: str, user_prompt: str, output_schema: type[T]) -> T:
        if output_schema is AnalystReport:
            if "技术" in system_prompt:
                data = {"summary": "趋势温和偏强，但需关注波动与压力位。",
                        "evidence": ["收盘价与均线、RSI、MACD均由代码计算", "20日支撑和压力位已纳入判断"],
                        "risks": ["高波动可能导致技术信号快速失效"], "score": 0.35}
            elif "基本面" in system_prompt:
                data = {"summary": "盈利和现金流总体健康，估值处于偏高区间。",
                        "evidence": ["营收增长、利润率和自由现金流为正", "估值历史分位偏高"],
                        "risks": ["估值压缩", "缺失字段不得推断"], "score": 0.3}
            else:
                data = {"summary": "新闻情绪轻微偏正，但正负催化并存。",
                        "evidence": ["新闻包含来源、时间与链接", "所有新闻不晚于分析日"],
                        "risks": ["新闻样本较少"], "score": 0.15}
        elif output_schema is DebateArgument:
            is_bull = system_prompt.startswith("你是多头研究员")
            data = {"round": 1, "thesis": "增长与趋势支持谨慎看多" if is_bull else "估值与波动限制上涨空间",
                    "evidence": ["综合三份独立报告"], "rebuttals": ["回应对方最新论点，保留不确定性"]}
        elif output_schema is ResearchConclusion:
            data = {"summary": "多头略占优，但并非无条件买入。", "bull_strength": .62,
                    "bear_strength": .48, "data_quality": .86, "unresolved_questions": ["未来盈利兑现速度"]}
        elif output_schema is RiskReport:
            data = {"summary": "整体风险中等，仓位应受限。", "risk_level": "MEDIUM",
                    "maximum_position_pct": 10, "key_risks": ["波动率", "估值压缩", "数据源覆盖有限"],
                    "leakage_detected": False}
        elif output_schema is FinalDecision:
            data = {"signal": "BUY", "confidence": .72, "position_size_pct": 10,
                    "rationale": "技术、基本面与情绪综合偏正，但估值和波动要求控制仓位。",
                    "risk_controls": ["最大仓位不超过10%", "跌破关键支撑位重新评估"], "snapshot_id": "set-by-node"}
        else:
            raise TypeError(f"Mock 不支持 Schema: {output_schema}")
        return output_schema.model_validate(data)
