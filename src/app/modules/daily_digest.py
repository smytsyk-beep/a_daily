from typing import List, Dict

Atom = Dict[str, object]


def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    cfg = config or {}
    time_local = cfg.get("time_local", "08:00")
    return [
        {
            "module": "daily_digest",
            "kind": "digest",
            "weight": 2,
            "text": f"Daily digest at {time_local}: день выглядит продуктивным.",
        }
    ]
