from datetime import date, datetime, timezone


def _to_date(value) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def validate_snapshot_parts(ticker: str, analysis_date: date, prices: list[dict],
                            fundamentals: dict, news: list[dict], indicators: dict) -> dict:
    warnings, fatal = [], []
    if not ticker:
        fatal.append("股票代码为空")
    if not prices:
        fatal.append("行情为空")
    if prices and _to_date(prices[-1].get("date")) > analysis_date:
        fatal.append("最新行情晚于分析日期")
    if any(float(x.get("close") or 0) <= 0 for x in prices):
        fatal.append("存在异常收盘价")
    if any(x.get("volume") is None for x in prices):
        warnings.append("部分成交量缺失")
    if len(prices) < 200:
        warnings.append("历史窗口不足200个交易日，SMA200可能缺失")
    if not fundamentals.get("published_at"):
        warnings.append("基本面真实发布时间缺失，已排除或标记不可用")
    if any(_to_date(x.get("published_at")) and _to_date(x["published_at"]) > analysis_date for x in news):
        fatal.append("新闻仍包含未来信息")
    missing_indicators = [k for k, v in indicators.items() if v is None]
    if missing_indicators:
        warnings.append("部分技术指标缺失: " + ", ".join(missing_indicators))
    penalty = min(.8, .07 * len(warnings) + .3 * len(fatal))
    return {"quality_score": round(1 - penalty, 2), "warnings": warnings, "fatal_errors": fatal}

