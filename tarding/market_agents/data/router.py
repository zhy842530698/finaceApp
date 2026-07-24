from dataclasses import dataclass

from .providers.base import MarketDataProvider


@dataclass
class RoutedResult:
    value: object
    metadata: dict


class ProviderRouter:
    def __init__(self, providers: dict[str, MarketDataProvider], primary: str, fallbacks: list[str] | None = None):
        self.providers = providers
        self.primary = primary
        self.fallbacks = fallbacks or []

    def call(self, method: str, *args) -> RoutedResult:
        errors: list[str] = []
        for index, name in enumerate([self.primary, *self.fallbacks]):
            try:
                value = getattr(self.providers[name], method)(*args)
                if value in (None, [], {}):
                    raise ValueError("数据为空")
                return RoutedResult(value, {
                    "requested_provider": self.primary, "actual_provider": name,
                    "fallback_used": index > 0, "errors_before_success": errors,
                })
            except Exception as exc:
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
        raise RuntimeError(f"{method} 所有数据源均失败: {'; '.join(errors)}")

