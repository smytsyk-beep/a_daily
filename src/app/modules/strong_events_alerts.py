from typing import List, Dict
Atom = Dict[str, object]

def compute(user_id: str, config: dict | None = None) -> List[Atom]:
    cfg = config or {}
    window = cfg.get("window_days", 3)
    return [
        {
            "module": "strong_events_alerts",
            "kind": "alert",
            "weight": 3,
            "text": f"Окно сильных транзитов: ближайшие {window} дня(ей).",
        }
    ]