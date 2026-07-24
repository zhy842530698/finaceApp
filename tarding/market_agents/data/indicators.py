from __future__ import annotations

import math
from statistics import mean, pstdev


def _sma(values: list[float], n: int) -> float | None:
    return mean(values[-n:]) if len(values) >= n else None


def _ema_series(values: list[float], n: int) -> list[float]:
    if not values:
        return []
    alpha, out = 2 / (n + 1), [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (1 - alpha) * out[-1])
    return out


def calculate_indicators(rows: list[dict]) -> dict:
    closes = [float(x["close"]) for x in rows]
    highs = [float(x["high"]) for x in rows]
    lows = [float(x["low"]) for x in rows]
    volumes = [float(x.get("volume") or 0) for x in rows]
    if not closes:
        return {}

    def ret(n: int) -> float | None:
        return closes[-1] / closes[-n - 1] - 1 if len(closes) > n else None

    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(v, 0) for v in changes[-14:]]
    losses = [max(-v, 0) for v in changes[-14:]]
    avg_gain, avg_loss = (mean(gains) if gains else 0), (mean(losses) if losses else 0)
    rsi = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)

    ema12, ema26 = _ema_series(closes, 12), _ema_series(closes, 26)
    macd_series = [a - b for a, b in zip(ema12, ema26)]
    signal = _ema_series(macd_series, 9)
    true_ranges = []
    for i in range(len(closes)):
        prev = closes[i - 1] if i else closes[i]
        true_ranges.append(max(highs[i] - lows[i], abs(highs[i] - prev), abs(lows[i] - prev)))
    daily_returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    recent_vol = volumes[-20:] if len(volumes) >= 20 else volumes
    previous_vol = volumes[-40:-20] if len(volumes) >= 40 else []

    return {
        "return_5d": ret(5), "return_20d": ret(20), "return_60d": ret(60),
        "sma20": _sma(closes, 20), "sma50": _sma(closes, 50), "sma200": _sma(closes, 200),
        "rsi14": rsi, "macd": macd_series[-1], "macd_signal": signal[-1],
        "atr14": mean(true_ranges[-14:]) if len(true_ranges) >= 14 else None,
        "volume_change": (mean(recent_vol) / mean(previous_vol) - 1) if previous_vol and mean(previous_vol) else None,
        "annualized_volatility": pstdev(daily_returns[-60:]) * math.sqrt(252) if len(daily_returns) >= 2 else None,
        "support_20d": min(lows[-20:]), "resistance_20d": max(highs[-20:]),
    }

