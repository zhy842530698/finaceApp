from .base import MarketDataProvider


class AlphaVantageProvider(MarketDataProvider):
    """预留适配器；实现前不会被默认路由静默选中。"""

    name = "alpha_vantage"

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        raise NotImplementedError("Alpha Vantage 适配器尚未启用")

    def get_fundamentals(self, ticker: str, as_of_date: str) -> dict:
        raise NotImplementedError("Alpha Vantage 适配器尚未启用")

    def get_news(self, ticker: str, start_date: str, end_date: str) -> list[dict]:
        raise NotImplementedError("Alpha Vantage 适配器尚未启用")

