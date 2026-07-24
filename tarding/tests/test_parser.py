from datetime import date

import pytest

from market_agents.parser import parse_request


@pytest.mark.parametrize("text,ticker,day", [
    ("分析 NVDA 的股票", "NVDA", "2026-07-24"),
    ("分析 0700.HK", "0700.HK", "2026-07-24"),
    ("分析 AAPL 2026-07-20", "AAPL", "2026-07-20"),
])
def test_parse_chinese_request(text, ticker, day):
    result = parse_request(text, today=date(2026, 7, 24))
    assert result.ticker == ticker
    assert result.analysis_date.isoformat() == day


def test_missing_ticker():
    with pytest.raises(ValueError):
        parse_request("帮我看看股票")

