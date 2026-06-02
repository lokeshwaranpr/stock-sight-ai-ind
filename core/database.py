"""
SQLAlchemy models and database engine.
Defaults to SQLite for local dev; swap DATABASE_URL env var for PostgreSQL in prod.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String,
    UniqueConstraint, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

def _make_engine():
    url = os.getenv("DATABASE_URL", "sqlite:///stocksight.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    from sqlalchemy.pool import NullPool
    if "sslmode" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return create_engine(url, poolclass=NullPool)


# Engine built fresh on every import so secret changes are always picked up
engine = _make_engine()


class SessionLocal:
    """Always builds a fresh engine so DATABASE_URL changes take effect immediately."""
    def __new__(cls):
        eng = _make_engine()
        return sessionmaker(bind=eng, autoflush=False, autocommit=False)()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, nullable=False, index=True)
    username      = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="user")   # "user" | "admin"
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login    = Column(DateTime, nullable=True)

    watchlist = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan",
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker   = Column(String, nullable=False)
    exchange = Column(String, nullable=False)          # "NS" | "BO"
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlist")

    __table_args__ = (UniqueConstraint("user_id", "ticker", "exchange"),)


def init_db() -> None:
    Base.metadata.create_all(_make_engine())
