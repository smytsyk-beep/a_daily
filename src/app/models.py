# src/app/models.py

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index,
    Float,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func

import sqlalchemy as sa

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    locale = Column(String(8), nullable=True, default="en")
    timezone = Column(String(64), nullable=True)

    # Массив тегов интересов: ["work", "love", "selfcare", "money", "creativity", ...]
    digest_interests = Column(JSONB, nullable=True)

    # Предпочитаемая длина текста: "short" | "medium" | "long"
    digest_length_preference = Column(String(16), nullable=True)

    # --- Telegram / daily delivery settings ---
    # Локальное время отправки дайджеста в формате "HH:MM" (например, "08:00")
    delivery_time_local = Column(String(8), nullable=True)

    # Включена ли вообще ежедневная доставка
    delivery_enabled = Column(Boolean, nullable=True)

    # Quiet mode — если True, пользователь временно «успокоен»
    quiet_mode = Column(Boolean, nullable=True)

    # === Новые поля под онбординг и prefs ===
    display_name = Column(String, nullable=True)

    age_gate_accepted_at = Column(DateTime(timezone=True), nullable=True)
    disclaimer_accepted_at = Column(DateTime(timezone=True), nullable=True)
    birthdata_consent_at = Column(DateTime(timezone=True), nullable=True)

    # общие пользовательские настройки (JSONB)
    # пример структуры:
    # {
    #   "focus_topics": ["work", "love"],
    #   "delivery_mode": "digest",
    #   "delivery_slot": "morning",
    #   "quiet_hours": {"from": "22:00", "to": "07:00"},
    #   "text_length": "medium"
    # }
    prefs = Column(JSONB, nullable=True)


class BirthData(Base):
    __tablename__ = "birth_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(String(8))  # "HH:MM" (может быть пустым)
    tz = Column(String(64))
    place = Column(String(128))
    lat = Column(Float)
    lon = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class NatalCache(Base):
    __tablename__ = "natal_cache"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    payload = Column(JSON, nullable=False)  # предрасчитанная натальная карта
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", name="uq_natalcache_user"),)


class TransitEvent(Base):
    __tablename__ = "transit_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ts_utc = Column(DateTime, index=True, nullable=False)
    kind = Column(String(64), nullable=False)  # e.g. "aspect", "ingress"
    payload = Column(JSON, nullable=False)  # module/kind/payload
    __table_args__ = (Index("ix_transit_user_ts", "user_id", "ts_utc"),)


class ContentAtom(Base):
    __tablename__ = "content_atoms"
    id = Column(Integer, primary_key=True)
    locale = Column(String(8), index=True)  # en/es/ru
    topic_tag = Column(String(64), index=True)  # e.g. "love", "career"
    style = Column(String(32), default="neutral")
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # формальный триггер: напр. "Mercury_trine_Moon", "Moon_phase_Waxing"
    trigger = Column(String, nullable=True, index=True)

    # теги домов, в которые попадает событие: ["III", "VI"]
    # храним как JSONB-массив строк
    house_tags = Column(JSONB, nullable=True)

    # теги "сфер жизни"/персоны: ["work", "relationships", "selfcare"]
    persona_tags = Column(JSONB, nullable=True)

    # подсказка по силе: "light", "medium", "strong", "light_to_medium" и т.п.
    strength_hint = Column(String, nullable=True)

    # короткий текст (short, 280–350 символов)
    copy_short = Column(Text, nullable=True)

    # длинный текст (long, 600+ символов)
    copy_long = Column(Text, nullable=True)

    # опциональный call-to-action (ритуал, упражнение и т.п.)
    cta = Column(Text, nullable=True)


class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module = Column(String(64), nullable=False)  # e.g. "daily_digest"
    kind = Column(String(64), nullable=False)  # e.g. "text","pdf"
    payload = Column(JSON, nullable=True)
    sent_at = Column(DateTime, index=True)
    success = Column(Boolean, default=False)


class ModuleRegistry(Base):
    __tablename__ = "modules_registry"
    __table_args__ = {"schema": "public"}
    id = Column(Integer, primary_key=True)
    module = Column(String(64), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSON)


class Entitlement(Base):
    __tablename__ = "entitlements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(32), nullable=False)  # "basic" / "pro" / "yearly"
    active = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class EventFeedback(Base):
    __tablename__ = "events_feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_ref = Column(String(64), index=True)  # связь с конкретным transit/delivery
    score = Column(Integer)  # 1..5
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    key = sa.Column(sa.String(64), primary_key=True)
    is_enabled = sa.Column(sa.Boolean, nullable=False, default=False)
    payload = sa.Column(JSONB, nullable=True)
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


class Event(Base):
    __tablename__ = "events"
    id = sa.Column(sa.BigInteger, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"))
    kind = sa.Column(sa.String(32), nullable=False)
    ts = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    title = sa.Column(sa.String(256), nullable=False)
    details = sa.Column(JSONB, nullable=True)

    user = sa.orm.relationship("User", lazy="joined")


class UserFeatureFlag(Base):
    __tablename__ = "user_feature_flags"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_key = Column(
        String(64),
        ForeignKey("feature_flags.key", ondelete="CASCADE"),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "feature_key", name="uq_user_feature_flag"),
    )


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"

    id = Column(Integer, primary_key=True)
    place_norm = Column(String(256), nullable=False, unique=True, index=True)
    query_raw = Column(String(256), nullable=True)

    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    display_name = Column(String(512), nullable=True)

    provider = Column(String(32), nullable=False)  # "nominatim" | "google"
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
