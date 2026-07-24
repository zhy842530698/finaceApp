from datetime import date, datetime, timedelta, timezone
import math
import random

from .base import MarketDataProvider


class MockProvider(MarketDataProvider):
    name = "mock"

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        rng = random.Random(f"{ticker}:{end_date}")
        rows, price, day = [], 100.0 + rng.random() * 30, start
        while day <= end:
            if day.weekday() < 5:
                drift = 0.0007 + rng.gauss(0, 0.015)
                close = max(1, price * (1 + drift))
                rows.append({
                    "date": day.isoformat(), "open": round(price, 4),
                    "high": round(max(price, close) * (1 + rng.random() * .01), 4),
                    "low": round(min(price, close) * (1 - rng.random() * .01), 4),
                    "close": round(close, 4), "volume": int(20_000_000 * (0.7 + rng.random())),
                })
                price = close
            day += timedelta(days=1)
        return rows

    def get_fundamentals(self, ticker: str, as_of_date: str) -> dict:
        published = date.fromisoformat(as_of_date) - timedelta(days=30)
        return {
            "published_at": published.isoformat(), "period": "TTM",
            "revenue": 120_000_000_000, "revenue_yoy": 0.22,
            "net_income": 35_000_000_000, "gross_margin": 0.61,
            "net_margin": 0.29, "free_cash_flow": 28_000_000_000,
            "debt_to_assets": 0.24, "roe": 0.42, "pe": 31.0,
            "forward_pe": 27.0, "pb": 18.0, "ps": 15.0,
            "valuation_history_percentile": 0.72,
        }

    def get_news(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        end = date.fromisoformat(end_date)
        return [
            {"title": f"{ticker} 发布业务更新", "source": "MockWire",
             "published_at": datetime.combine(end - timedelta(days=2), datetime.min.time(), timezone.utc).isoformat(),
             "url": "https://example.com/mock/business-update", "relevance_score": .9, "sentiment_score": .35},
            {"title": f"{ticker} 所在行业面临估值波动", "source": "MockWire",
             "published_at": datetime.combine(end - timedelta(days=1), datetime.min.time(), timezone.utc).isoformat(),
             "url": "https://example.com/mock/sector-risk", "relevance_score": .8, "sentiment_score": -.25},
        ]

    def get_macro(self, as_of_date: str) -> dict:
        return {"as_of_date": as_of_date, "risk_free_rate": 0.042, "source": "mock"}

