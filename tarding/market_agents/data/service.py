from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from market_agents.schemas import MarketSnapshot, NewsItem
from .cache import JsonCache
from .indicators import calculate_indicators
from .providers import MockProvider, YahooFinanceProvider
from .router import ProviderRouter
from .validator import validate_snapshot_parts


class DataService:
    def __init__(self, data_dir: Path, primary: str = "mock", fallbacks: list[str] | None = None):
        self.data_dir = Path(data_dir)
        self.cache = JsonCache(self.data_dir / "cache")
        providers = {"mock": MockProvider(), "yfinance": YahooFinanceProvider()}
        fallback_names = fallbacks if fallbacks is not None else (["mock"] if primary != "mock" else [])
        self.router = ProviderRouter(providers, primary, fallback_names)

    def _fetch(self, namespace: str, key: str, method: str, *args):
        payload, cache_hit = self.cache.get_or_fetch(
            namespace, key,
            lambda: (lambda result: {"value": result.value, "metadata": result.metadata})(
                self.router.call(method, *args)
            ),
        )
        payload["metadata"]["cache_hit"] = cache_hit
        raw_path = self.data_dir / "raw" / namespace / f"{key}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if not raw_path.exists():
            raw_path.write_text(json.dumps(payload["value"], ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return payload["value"], payload["metadata"]

    @staticmethod
    def _visible_date(value) -> date | None:
        if not value:
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()

    def create_snapshot(self, ticker: str, analysis_date: date) -> MarketSnapshot:
        start = analysis_date - timedelta(days=400)
        sources, filtered = {}, {"prices": 0, "news": 0, "fundamentals": 0}

        raw_price_value, price_meta = self._fetch("price", f"{ticker}_{start}_{analysis_date}",
                                                  "get_price_history", ticker, start.isoformat(), analysis_date.isoformat())
        raw_prices = list(raw_price_value)
        sources["price"] = price_meta
        prices = [x for x in raw_prices if self._visible_date(x.get("date")) <= analysis_date]
        filtered["prices"] = len(raw_prices) - len(prices)

        fundamentals_value, fundamentals_meta = self._fetch("fundamentals", f"{ticker}_{analysis_date}",
                                                              "get_fundamentals", ticker, analysis_date.isoformat())
        fundamentals = dict(fundamentals_value)
        sources["fundamentals"] = fundamentals_meta
        published = self._visible_date(fundamentals.get("published_at"))
        if not published or published > analysis_date:
            fundamentals = {
                "published_at": fundamentals.get("published_at"),
                "unavailable_reason": "财务数据发布时间晚于分析日或无法验证",
            }
            filtered["fundamentals"] = 1

        news_value, news_meta = self._fetch("news", f"{ticker}_{start}_{analysis_date}",
                                            "get_news", ticker, start.isoformat(), analysis_date.isoformat())
        raw_news = list(news_value)
        sources["news"] = news_meta
        news = [x for x in raw_news if self._visible_date(x.get("published_at")) and self._visible_date(x["published_at"]) <= analysis_date]
        filtered["news"] = len(raw_news) - len(news)

        macro_value, macro_meta = self._fetch("macro", f"macro_{analysis_date}", "get_macro", analysis_date.isoformat())
        sources["macro"] = macro_meta
        indicators = calculate_indicators(prices)
        quality = validate_snapshot_parts(ticker, analysis_date, prices, fundamentals, news, indicators)

        normalized = {
            "ticker": ticker, "analysis_date": analysis_date.isoformat(), "price_history": prices,
            "indicators": indicators, "fundamentals": fundamentals, "news": news,
            "macro": macro_value, "data_sources": sources, "filtered_counts": filtered,
        }
        # cache_hit 属于本次读取路径，不属于标准化市场数据；否则同一内容首次/再次读取会产生不同 ID。
        hash_sources = {
            category: {k: v for k, v in metadata.items() if k != "cache_hit"}
            for category, metadata in sources.items()
        }
        hash_payload = {**normalized, "data_sources": hash_sources}
        snapshot_id = sha256(json.dumps(hash_payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
        snapshot = MarketSnapshot(
            snapshot_id=snapshot_id, ticker=ticker, analysis_date=analysis_date,
            generated_at=datetime.now(timezone.utc), price_history=prices,
            latest_price=prices[-1] if prices else {}, indicators=indicators,
            fundamentals=fundamentals, news=[NewsItem.model_validate(x) for x in news],
            macro=macro_value, data_sources=sources, filtered_counts=filtered, **quality,
        )
        normalized_path = self.data_dir / "normalized" / ticker / analysis_date.isoformat() / "market_data.json"
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        path = self.data_dir / "snapshots" / ticker / analysis_date.isoformat() / f"{snapshot_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        return snapshot
