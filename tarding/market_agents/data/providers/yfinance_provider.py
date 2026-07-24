from datetime import date, timedelta

from .base import MarketDataProvider


class YahooFinanceProvider(MarketDataProvider):
    name = "yfinance"

    def _ticker(self, ticker: str):
        import yfinance as yf
        return yf.Ticker(ticker)

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        end_exclusive = (date.fromisoformat(end_date) + timedelta(days=1)).isoformat()
        frame = self._ticker(ticker).history(start=start_date, end=end_exclusive, auto_adjust=False)
        return [
            {"date": idx.date().isoformat(), "open": float(row["Open"]), "high": float(row["High"]),
             "low": float(row["Low"]), "close": float(row["Close"]), "volume": int(row["Volume"])}
            for idx, row in frame.iterrows()
        ]

    def get_fundamentals(self, ticker: str, as_of_date: str) -> dict:
        info = self._ticker(ticker).info
        # Yahoo 的 info 多为当前快照，无法证明历史可见性；历史分析时明确拒绝使用。
        if date.fromisoformat(as_of_date) < date.today():
            return {"published_at": None, "unavailable_reason": "yfinance 当前公司快照不适用于历史时点"}
        keys = ["totalRevenue", "revenueGrowth", "netIncomeToCommon", "grossMargins",
                "profitMargins", "freeCashflow", "debtToEquity", "returnOnEquity",
                "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months"]
        return {"published_at": as_of_date, **{k: info.get(k) for k in keys}}

    def get_news(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        items = []
        for raw in self._ticker(ticker).news or []:
            content = raw.get("content", raw)
            canonical = content.get("canonicalUrl") or {}
            items.append({
                "title": content.get("title", ""), "source": (content.get("provider") or {}).get("displayName", "Yahoo"),
                "published_at": content.get("pubDate"), "url": canonical.get("url", ""),
                "relevance_score": 0.7, "sentiment_score": 0.0,
            })
        return items

