from app.db import SessionLocal
from app.models import ModuleRegistry

DEFAULT = [
    {"module": "daily_digest", "enabled": True, "config": {"time_local": "08:00"}},
    {"module": "strong_events_alerts", "enabled": True, "config": {"window_days": 3}},
]


def run():
    db = SessionLocal()
    try:
        for item in DEFAULT:
            row = (
                db.query(ModuleRegistry).filter_by(module=item["module"]).one_or_none()
            )
            if not row:
                row = ModuleRegistry(**item)
                db.add(row)
        db.commit()
        print("Seed OK")
    finally:
        db.close()


if __name__ == "__main__":
    run()
