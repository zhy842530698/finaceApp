from __future__ import annotations

import typer
from rich.console import Console

from market_agents.config import Settings
from market_agents.data import DataService
from market_agents.llm import build_llm_client
from market_agents.parser import parse_request
from market_agents.reporting import answer_followup, format_report, save_reports
from market_agents.workflow import build_graph

app = typer.Typer(add_completion=False)
console = Console()


def _is_new_analysis(text: str, state) -> bool:
    if state is None or "重新分析" in text:
        return True
    try:
        parsed = parse_request(text)
        return parsed.ticker != state["ticker"] or parsed.analysis_date.isoformat() != state["analysis_date"]
    except ValueError:
        return False


@app.command()
def main(
    query: str | None = typer.Option(None, "--query", "-q", help="单次分析请求；省略则进入交互模式"),
):
    settings = Settings()
    llm = build_llm_client(settings)
    service = DataService(settings.data_dir, settings.data_provider)
    graph = build_graph(settings, service, llm)
    console.print("[bold cyan]Market Analysis Agents[/bold cyan]")
    console.print(f"模型：{llm.model_name}；数据源：{settings.data_provider}")
    state = None

    def handle(text: str):
        nonlocal state
        if _is_new_analysis(text, state):
            console.print("系统 > 正在获取并验证数据……")
            console.print("系统 > 技术面、基本面、新闻 Agent 正在并行分析……")
            state = graph.invoke({"request": text})
            report_dir = save_reports(state, settings.output_dir)
            console.print(format_report(state))
            console.print(f"\n报告已保存：{report_dir}")
        else:
            console.print(answer_followup(text, state))

    if query:
        handle(query)
        return
    while True:
        try:
            text = console.input("\n[bold green]你 > [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n再见。")
            break
        if text.lower() in {"exit", "quit", "退出"}:
            break
        if text:
            try:
                handle(text)
            except Exception as exc:
                console.print(f"[red]系统错误：{type(exc).__name__}: {exc}[/red]")


if __name__ == "__main__":
    app()
