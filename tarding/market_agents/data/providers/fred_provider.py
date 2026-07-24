from .base import MarketDataProvider


class FREDProvider(MarketDataProvider):
    """预留宏观数据适配器。"""

    name = "fred"

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        raise NotImplementedError("FRED 不提供个股行情")

    def get_fundamentals(self, ticker: str, as_of_date: str) -> dict:
        raise NotImplementedError("FRED 不提供公司基本面")

    def get_news(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        raise NotImplementedError("FRED 不提供公司新闻")
