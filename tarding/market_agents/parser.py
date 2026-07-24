import re
from datetime import date

from pydantic import BaseModel


class ParsedRequest(BaseModel):
    ticker: str
    analysis_date: date


_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_TICKER = re.compile(r"(?<![A-Z0-9])([A-Z]{1,6}(?:\.[A-Z]{1,3})?|\d{4,6}\.HK)(?![A-Z0-9])", re.I)


def parse_request(text: str, today: date | None = None) -> ParsedRequest:
    normalized = text.strip().upper()
    ticker_match = _TICKER.search(normalized)
    if not ticker_match:
        raise ValueError("未识别到股票代码，请输入例如：分析 NVDA 2026-07-20")
    date_match = _DATE.search(normalized)
    analysis_date = date.fromisoformat(date_match.group(1)) if date_match else (today or date.today())
    return ParsedRequest(ticker=ticker_match.group(1), analysis_date=analysis_date)

