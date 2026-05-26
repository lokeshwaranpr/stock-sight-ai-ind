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

_URL = os.getenv("DATABASE_URL", "sqlite:///stocksight.db")
_kwargs = {"check_same_thread": False} if _URL.startswith("sqlite") else {}

engine = create_engine(_URL, connect_args=_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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
    Base.metadata.create_all(engine)
