# src/app/test_plan.py

from app.db import SessionLocal
from app.plan_service import (
    get_effective_plan_for_user,
    get_user_digest_length_cap,
    user_plan_allows_feature,
)
from common.plans import PlanFeature


def main() -> None:
    user_id = 1383  # подставь любого тестового юзера

    with SessionLocal() as db:
        plan = get_effective_plan_for_user(db, user_id)
        digest_cap = get_user_digest_length_cap(db, user_id)
        # Лучше использовать новое имя enum-значения
        has_alerts = user_plan_allows_feature(db, user_id, PlanFeature.STRONG_ALERTS)

    # plan у нас сейчас строка; но если когда-нибудь станет Enum со .value —
    # этот код всё равно отработает.
    plan_display = getattr(plan, "value", plan)

    print("plan:", plan_display)
    print("digest_cap:", digest_cap)
    print("has_strong_alerts:", has_alerts)


if __name__ == "__main__":
    main()
