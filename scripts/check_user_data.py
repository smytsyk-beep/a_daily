#!/usr/bin/env python3
"""
Скрипт для проверки данных пользователя в БД.

Usage:
    python scripts/check_user_data.py --user-id 1888
"""
import os
import sys
from pathlib import Path

# Добавляем путь к src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from datetime import date

from app.repo import session_scope
from app import models


def check_user_data(user_id: int, check_date: date | None = None):
    """Проверяет данные пользователя в БД."""
    if check_date is None:
        check_date = date.today()

    print(f"\n{'=' * 60}")
    print(f"Checking data for user_id={user_id} on date={check_date}")
    print(f"{'=' * 60}\n")

    with session_scope() as db:
        # 1. User
        user = db.query(models.User).filter(models.User.id == user_id).one_or_none()
        if not user:
            print(f"❌ User {user_id} NOT FOUND")
            return

        print(f"✅ User found:")
        print(f"   - id: {user.id}")
        print(f"   - tg_user_id: {user.tg_user_id}")
        print(f"   - locale: {user.locale}")
        print(f"   - timezone: {user.timezone}")
        print(f"   - display_name: {user.display_name}")
        print(f"   - digest_interests: {getattr(user, 'digest_interests', None)}")
        print(
            f"   - digest_length_preference: {getattr(user, 'digest_length_preference', None)}"
        )
        print()

        # 2. BirthData
        birth = (
            db.query(models.BirthData)
            .filter(models.BirthData.user_id == user_id)
            .one_or_none()
        )
        if not birth:
            print(f"❌ BirthData NOT FOUND for user {user_id}")
        else:
            print(f"✅ BirthData found:")
            print(f"   - birth_date: {birth.birth_date}")
            print(f"   - birth_time: {birth.birth_time}")
            print(f"   - place: {birth.place}")
            print(f"   - lat: {birth.lat}")
            print(f"   - lon: {birth.lon}")
            print(f"   - tz: {birth.tz}")
        print()

        # 3. NatalCache
        natal_cache = (
            db.query(models.NatalCache)
            .filter(models.NatalCache.user_id == user_id)
            .order_by(models.NatalCache.created_at.desc())
            .first()
        )
        if not natal_cache:
            print(f"⚠️  NatalCache NOT FOUND for user {user_id}")
        else:
            print(f"✅ NatalCache found:")
            print(f"   - id: {natal_cache.id}")
            print(f"   - created_at: {natal_cache.created_at}")
            payload = natal_cache.payload
            if isinstance(payload, dict):
                bodies = payload.get("bodies", {})
                print(f"   - bodies count: {len(bodies)}")
                if "meta" in payload:
                    meta = payload["meta"]
                    print(f"   - computed_at: {meta.get('computed_at')}")
                    print(f"   - signature: {meta.get('signature')[:16]}...")
                    print(f"   - ephemeris: {meta.get('ephemeris_file')}")
        print()

        # 4. TransitEvent
        day_iso = check_date.isoformat()
        transit_events = (
            db.query(models.TransitEvent)
            .filter(models.TransitEvent.user_id == user_id)
            .order_by(models.TransitEvent.ts_utc.desc())
            .limit(10)
            .all()
        )
        if not transit_events:
            print(f"⚠️  No TransitEvent records found for user {user_id}")
        else:
            print(f"✅ Found {len(transit_events)} TransitEvent records (last 10):")
            for te in transit_events:
                print(
                    f"   - {te.id}: {te.kind} at {te.ts_utc} (payload keys: {list(te.payload.keys()) if isinstance(te.payload, dict) else 'N/A'})"
                )
        print()

        # 5. Events (transit_aspect для дайджеста)
        events = (
            db.query(models.Event)
            .filter(
                models.Event.user_id == user_id,
                models.Event.kind == "transit_aspect",
            )
            .order_by(models.Event.ts.desc())
            .limit(10)
            .all()
        )
        if not events:
            print(f"⚠️  No Event (transit_aspect) records found for user {user_id}")
        else:
            print(f"✅ Found {len(events)} Event (transit_aspect) records (last 10):")
            for ev in events:
                details = ev.details or {}
                local_date = details.get("local_date", "N/A")
                bucket = details.get("bucket", "N/A")
                transit_body = details.get("transit_body", "N/A")
                natal_body = details.get("natal_body", "N/A")
                aspect = details.get("aspect", "N/A")
                print(
                    f"   - {ev.id}: {transit_body} {aspect} {natal_body} (local_date={local_date}, bucket={bucket})"
                )
        print()

        # 6. Проверяем события для конкретной даты
        events_for_date = (
            db.query(models.Event)
            .filter(
                models.Event.user_id == user_id,
                models.Event.kind == "transit_aspect",
                models.Event.details["bucket"].as_string() == "digest",
                models.Event.details["local_date"].as_string() == day_iso,
            )
            .all()
        )
        if not events_for_date:
            print(
                f"⚠️  No transit_aspect events found for user {user_id} on date {check_date}"
            )
        else:
            print(
                f"✅ Found {len(events_for_date)} transit_aspect events for {check_date}:"
            )
            for ev in events_for_date:
                details = ev.details or {}
                print(
                    f"   - {ev.id}: {details.get('transit_body')} {details.get('aspect')} {details.get('natal_body')} (orb={details.get('orb_deg')})"
                )

    print(f"\n{'=' * 60}")
    print("Check complete!")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check user data in database for AstroDaily"
    )
    parser.add_argument(
        "--user-id", type=int, required=True, help="User ID to check"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to check (YYYY-MM-DD), default: today",
    )

    args = parser.parse_args()

    check_date = None
    if args.date:
        check_date = date.fromisoformat(args.date)

    check_user_data(args.user_id, check_date)


if __name__ == "__main__":
    main()
