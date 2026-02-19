# src/app/jobs/precompute_transits.py
"""
Pre-compute транзитов на завтра для активных пользователей.

Запуск:
  из корня: PYTHONPATH=src python -m app.jobs.precompute_transits
  в Docker:  docker compose exec app python -m app.jobs.precompute_transits

Cron (3:00 UTC): 0 3 * * * docker compose exec app python -m app.jobs.precompute_transits
"""

from __future__ import annotations

import logging
import sys

from app.repo import session_scope
from app.services.transit_events_precompute import (
    precompute_transit_events_tomorrow_for_active_users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> int:
    with session_scope() as db:
        n = precompute_transit_events_tomorrow_for_active_users(db)
    logger.info("Precompute job finished: %d events written", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
