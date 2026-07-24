from datetime import date

from market_agents.data import DataService
from market_agents.data.indicators import calculate_indicators


def test_snapshot_is_deterministic_and_cutoff(tmp_path):
    service = DataService(tmp_path, "mock")
    snapshot = service.create_snapshot("NVDA", date(2026, 7, 20))
    assert snapshot.price_history
    assert all(row["date"] <= "2026-07-20" for row in snapshot.price_history)
    assert all(item.published_at.date() <= date(2026, 7, 20) for item in snapshot.news)
    assert snapshot.snapshot_id
    assert not snapshot.fatal_errors
    second = service.create_snapshot("NVDA", date(2026, 7, 20))
    assert second.snapshot_id == snapshot.snapshot_id
    assert second.data_sources["price"]["cache_hit"] is True


def test_indicators_are_code_computed():
    rows = [{"close": float(i), "open": float(i), "high": i + 1.0, "low": i - 1.0, "volume": 100 + i}
            for i in range(1, 221)]
    indicators = calculate_indicators(rows)
    assert indicators["sma200"] is not None
    assert indicators["return_20d"] > 0
    assert 0 <= indicators["rsi14"] <= 100

