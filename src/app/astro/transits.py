# src/app/astro/transits.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


AspectName = Literal["conjunction", "sextile", "square", "trine", "opposition"]

ASPECTS: Dict[AspectName, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


def _norm_deg(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x


def angle_diff(a: float, b: float) -> float:
    """
    Минимальная разница углов a-b в диапазоне [-180..180].
    """
    d = (_norm_deg(a) - _norm_deg(b)) % 360.0
    if d > 180.0:
        d -= 360.0
    return d


@dataclass(frozen=True)
class TransitAspectEvent:
    kind: str  # "transit_aspect"
    transit_body: str
    natal_body: str
    aspect: AspectName
    exact_deg: float
    orb_deg: float
    transit_lon: float
    natal_lon: float


def detect_transit_aspects(
    transit_lon: Dict[str, float],
    natal_lon: Dict[str, float],
    *,
    orb_deg: float,
    aspects: Optional[Dict[AspectName, float]] = None,
    include_transit_bodies: Optional[set[str]] = None,
    include_natal_bodies: Optional[set[str]] = None,
) -> List[TransitAspectEvent]:
    """
    Находит аспекты транзит→натал с заданным орбом.
    """
    aspects = aspects or ASPECTS
    out: List[TransitAspectEvent] = []

    for t_body, t_deg in transit_lon.items():
        if include_transit_bodies is not None and t_body not in include_transit_bodies:
            continue

        for n_body, n_deg in natal_lon.items():
            if include_natal_bodies is not None and n_body not in include_natal_bodies:
                continue

            d = abs(angle_diff(t_deg, n_deg))
            for a_name, a_exact in aspects.items():
                orb = abs(d - a_exact)
                if orb <= orb_deg:
                    out.append(
                        TransitAspectEvent(
                            kind="transit_aspect",
                            transit_body=t_body,
                            natal_body=n_body,
                            aspect=a_name,
                            exact_deg=a_exact,
                            orb_deg=round(orb, 6),
                            transit_lon=round(_norm_deg(t_deg), 6),
                            natal_lon=round(_norm_deg(n_deg), 6),
                        )
                    )

    # стабильно сортируем: сначала по точности, потом по “силе” аспекта, потом по именам
    aspect_rank = {
        "conjunction": 0,
        "opposition": 1,
        "square": 2,
        "trine": 3,
        "sextile": 4,
    }
    out.sort(
        key=lambda e: (e.orb_deg, aspect_rank[e.aspect], e.transit_body, e.natal_body)
    )
    return out
