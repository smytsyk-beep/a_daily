from typing import List, Dict
from app.repo import get_session, list_enabled_modules
from app.modules.daily_digest import compute as daily_digest_compute
from app.modules.strong_events_alerts import compute as alerts_compute

Atom = Dict[str, object]

MODULES = {
    "daily_digest": daily_digest_compute,
    "strong_events_alerts": alerts_compute,
}

def compute_atoms(user_id: str) -> List[Atom]:
    atoms: List[Atom] = []
    with get_session() as db:
        enabled = list_enabled_modules(db)
        for row in enabled:
            fn = MODULES.get(row.module)
            if not fn:
                continue
            cfg = row.config or {}
            atoms.extend(fn(user_id=user_id, config=cfg))
    return atoms

def rank_atoms(atoms: List[Atom]) -> List[Atom]:
    return sorted(atoms, key=lambda a: a.get("weight", 1), reverse=True)

def render_text(atoms: List[Atom]) -> str:
    lines = []
    for a in atoms:
        lines.append(str(a.get("text", "")))
    return "\n".join(lines)

def run_preview(user_id: str) -> Dict[str, object]:
    atoms = compute_atoms(user_id)
    ranked = rank_atoms(atoms)
    text = render_text(ranked[:10])
    return {"ok": True, "count": len(ranked), "atoms": ranked, "text": text}