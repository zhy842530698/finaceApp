import json
from pathlib import Path
from typing import Any, Callable


class JsonCache:
    def __init__(self, root: Path):
        self.root = root

    def get_or_fetch(self, namespace: str, key: str, fetch: Callable[[], Any]) -> tuple[Any, bool]:
        path = self.root / namespace / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), True
        value = fetch()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return value, False

