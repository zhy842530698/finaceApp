from abc import ABC, abstractmethod


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> list[dict]: ...

    @abstractmethod
    def get_fundamentals(self, ticker: str, as_of_date: str) -> dict: ...

    @abstractmethod
    def get_news(self, ticker: str, start_date: str, end_date: str) -> list[dict]: ...

    def get_macro(self, as_of_date: str) -> dict:
        return {"as_of_date": as_of_date, "status": "unavailable"}

