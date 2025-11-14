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
import sqlalchemy as sa

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(String(64), unique=True, index=True, nullable=False)
    locale = Column(String(8), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)


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
