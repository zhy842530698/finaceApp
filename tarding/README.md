# Market Agents

一个参考 TradingAgents 思路、但强调本地可运行、统一数据快照、时间截断与审计的 Python + LangGraph 多智能体股票分析项目。

> 仅用于研究和教学，不构成投资建议，不连接券商，也不会执行真实交易。

## 1. 特性

- 一个 Terminal 内完成股票分析和连续追问。
- LangGraph 共享 `AnalysisState`，三个分析师节点并行，汇合后才进入辩论。
- 多头读取最新空头观点，空头读取最新多头观点；轮数由 `MAX_DEBATE_ROUNDS` 控制。
- 技术指标完全由 Python 计算，LLM 只解释。
- Agent 只读取统一 `MarketSnapshot`，不直接访问数据接口。
- 数据源显式路由和降级，记录 requested/actual provider、fallback 和 cache hit。
- 严格按 `published_at`/行情日期过滤未来数据。
- SHA256 快照 ID、原始/标准化/快照/Agent 报告分层保存。
- 支持 Mock、MiniMax Anthropic-compatible、Anthropic 和 OpenAI-compatible。

## 2. 架构

```text
Terminal
  -> LangGraph
     -> 标的识别 -> DataService -> 单一 MarketSnapshot
     -> [Technical | Fundamental | News]（并行）
     -> Bull -> Bear -> Bull ...（条件循环）
     -> Research Manager -> Risk Manager -> Portfolio Manager
  -> outputs/<ticker>/<date>/
```

数据链路：

```text
Agent -> DataService -> ProviderRouter -> Provider
      -> 时间截断 -> 标准化 -> 指标计算 -> 验证
      -> MarketSnapshot -> 缓存与审计
```

关键目录：

```text
market_agents/
├── agents.py              # Agent 节点职责
├── workflow.py            # LangGraph 并行、汇合与条件循环
├── schemas.py             # AnalysisState 与 Pydantic 输出模型
├── parser.py              # 中文股票代码/日期解析
├── reporting.py           # 输出、审计与连续追问
├── cli.py                 # market-agents 入口
├── llm/                   # 统一 structured() 适配
└── data/
    ├── service.py         # 单一快照编排
    ├── router.py          # 显式路由/降级
    ├── indicators.py      # 确定性技术指标
    ├── validator.py       # 数据质量和致命错误
    ├── cache.py
    └── providers/
        ├── base.py
        ├── mock.py
        └── yfinance_provider.py
```

`alpha_vantage_provider.py` 与 `fred_provider.py` 是下一阶段适配点；第一版按验收要求实现 Mock 和 Yahoo。

## 3. 安装

建议 Python 3.11 或 3.12：

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
pytest -q
```

无 API Key 即可运行：

```env
LLM_PROVIDER=mock
DATA_PROVIDER=mock
MAX_DEBATE_ROUNDS=2
```

```bash
market-agents
```

或单次运行：

```bash
market-agents --query "分析 NVDA 2026-07-20"
```

## 4. MiniMax 配置

MiniMax 走 Anthropic-compatible Messages API：

```env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=你的Key
MINIMAX_BASE_URL=https://api.minimax.io/anthropic
MINIMAX_MODEL=MiniMax-M2.1
```

模型名需以你账户实际可用列表为准。

## 5. Anthropic 配置

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=你的Key
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=你的账户可用Claude模型
```

## 6. OpenAI-compatible 配置

适用于 OpenAI、本地 vLLM、Ollama、LM Studio 等：

```env
LLM_PROVIDER=openai_compatible
OPENAI_API_KEY=可选或真实Key
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_MODEL=Qwen3.5-35B-A3B
```

## 7. Yahoo 真实数据

```env
DATA_PROVIDER=yfinance
```

Yahoo 接口并不保证完整历史基本面和历史新闻。为防止未来信息泄漏，本实现不会用“今天的公司 info”覆盖历史分析日；无法验证真实发布时间的字段会明确标记不可用。若 Yahoo 失败，会显式降级到 Mock，并在 `snapshot.json` 的 `data_sources` 中留下记录。生产环境应接入带 point-in-time 财务数据的数据源。

## 8. Terminal 示例

```text
Market Analysis Agents
模型：MockLLM；数据源：mock

你 > 分析 NVDA 2026-07-20
系统 > 正在获取并验证数据……
系统 > 技术面、基本面、新闻 Agent 正在并行分析……

[技术面]
...
[最终结论]
信号：BUY
置信度：72%
建议仓位：10%

你 > 空头认为最大的风险是什么？
空头核心观点：估值与波动限制上涨空间
```

只有明确输入“重新分析”或更换股票代码/日期才会重新运行图；普通追问读取内存中的完整状态。

## 9. 输出与审计

```text
data/
├── raw/
├── normalized/
├── snapshots/
└── cache/

outputs/NVDA/2026-07-20/
├── snapshot.json
├── technical_report.json
├── fundamentals_report.json
├── news_report.json
├── debate.json
├── research_conclusion.json
├── risk_report.json
├── final_decision.json
└── agent_audit.json
```

任何 API Key 都不会写入报告。

## 10. 当前限制

- Mock 数据用于离线验收，不代表真实 NVDA 历史数据。
- yfinance 的 point-in-time 基本面、新闻覆盖和稳定性有限。
- 新闻情绪在真实模式由 LLM 判断；第一版未引入专门金融情绪模型。
- 当前仓位建议是研究输出，不包含用户资产、成本、税务或组合相关性。
- Provider 配置文件已提供示例；当前 CLI 通过 `DATA_PROVIDER` 选择主源，后续可把 YAML 路由扩展到各数据类别。

建议下一步接入 Alpha Vantage/FMP/Polygon 等可验证发布时间的数据源、FRED 宏观数据、跨源价格偏差校验、LangGraph checkpoint 持久会话，以及人工评测集和可观测性平台。
