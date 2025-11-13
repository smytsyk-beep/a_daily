from typing import Dict, List

# Контракт модуля: compute(user_id, config) -> список "атомов"
Atom = Dict[str, object]  # {module, kind, weight, text, ...}


def example_signature(user_id: str, config: dict) -> List[Atom]:  # документация
    raise NotImplementedError
