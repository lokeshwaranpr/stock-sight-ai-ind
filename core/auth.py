"""
Authentication, session management, RBAC guards, and user/watchlist CRUD.
All DB access is scoped inside `with SessionLocal()` to ensure proper cleanup.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import TypedDict

import bcrypt
import streamlit as st
from sqlalchemy.exc import IntegrityError

from core.database import SessionLocal, User, WatchlistItem, init_db

_COOKIE_NAME = "ss_auth"
_COOKIE_DAYS = 30
_SECRET      = os.getenv("SECRET_KEY", "stocksight-default-secret")


# ── Session type ──────────────────────────────────────────────────────────────

class UserSession(TypedDict):
    id:       int
    email:    str
    username: str
    role:     str


# ── Validation helpers ────────────────────────────────────────────────────────

def _validate_email(email: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return "Invalid email address."
    return ""


def _validate_password(pw: str) -> str:
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", pw):
        return "Must contain at least one uppercase letter."
    if not re.search(r"[0-9]", pw):
        return "Must contain at least one digit."
    return ""


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Auth operations ───────────────────────────────────────────────────────────

def register_user(
    email: str, username: str, password: str
) -> tuple[UserSession | None, str]:
    """Returns (session_data, error). error is '' on success."""
    err = (
        _validate_email(email)
        or _validate_password(password)
        or ("" if len(username) >= 3 else "Username must be at least 3 characters.")
    )
    if err:
        return None, err

    with SessionLocal() as db:
        if db.query(User).filter(User.email == email.lower()).first():
            return None, "Email already registered."
        if db.query(User).filter(User.username == username.lower()).first():
            return None, "Username already taken."
        user = User(
            email=email.lower(),
            username=username.lower(),
            password_hash=_hash(password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return _to_session(user), ""


def authenticate(email: str, password: str) -> tuple[UserSession | None, str]:
    """Verify credentials. Returns (session_data, error)."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not _verify(password, user.password_hash):
            return None, "Invalid email or password."
        if not user.is_active:
            return None, "Account suspended. Contact support."
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        return _to_session(user), ""


def _to_session(user: User) -> UserSession:
    return {
        "id":       user.id,
        "email":    user.email,
        "username": user.username,
        "role":     user.role,
    }


# ── Cookie helpers ────────────────────────────────────────────────────────────

def _make_token(user: UserSession) -> str:
    data    = {**user, "exp": int(time.time()) + _COOKIE_DAYS * 86400}
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    sig     = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _verify_token(token: str) -> UserSession | None:
    try:
        decoded      = base64.urlsafe_b64decode(token.encode()).decode()
        payload, sig = decoded.rsplit("|", 1)
        expected     = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            data = json.loads(payload)
            if data.get("exp", 0) > time.time():
                return {k: v for k, v in data.items() if k != "exp"}  # type: ignore[return-value]
    except Exception:
        pass
    return None


def _get_cookie_manager():
    try:
        import extra_streamlit_components as stx
        return stx.CookieManager(key="auth_cookies")
    except Exception:
        return None


# ── Session helpers ───────────────────────────────────────────────────────────

def login(session_data: UserSession) -> None:
    st.session_state["user"] = session_data
    mgr = _get_cookie_manager()
    if mgr is not None:
        try:
            from datetime import timedelta
            mgr.set(_COOKIE_NAME, _make_token(session_data),
                    expires_at=datetime.now() + timedelta(days=_COOKIE_DAYS))
        except Exception:
            pass


def logout() -> None:
    mgr = _get_cookie_manager()
    if mgr is not None:
        try:
            mgr.delete(_COOKIE_NAME)
        except Exception:
            pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.switch_page("Home.py")


def current_user() -> UserSession | None:
    return st.session_state.get("user")


def _restore_from_cookie() -> UserSession | None:
    """Try to restore session from persistent cookie."""
    mgr = _get_cookie_manager()
    if mgr is None:
        return None
    try:
        token = mgr.get(_COOKIE_NAME)
        if token:
            user = _verify_token(token)
            if user:
                st.session_state["user"] = user
                return user
    except Exception:
        pass
    return None


def require_auth() -> UserSession:
    """Page guard — redirects to login if unauthenticated."""
    user = current_user() or _restore_from_cookie()
    if not user:
        st.switch_page("Home.py")
    return user  # type: ignore[return-value]


def require_admin() -> UserSession:
    """Page guard — blocks non-admins."""
    user = require_auth()
    if user["role"] != "admin":
        st.error("⛔ Administrator access required.")
        st.stop()
    return user


# ── Watchlist CRUD ────────────────────────────────────────────────────────────

def get_watchlist(user_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = (
            db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.added_at.desc())
            .all()
        )
        return [
            {"ticker": r.ticker, "exchange": r.exchange, "added_at": r.added_at}
            for r in rows
        ]


def add_to_watchlist(user_id: int, ticker: str, exchange: str) -> tuple[bool, str]:
    with SessionLocal() as db:
        try:
            db.add(WatchlistItem(
                user_id=user_id, ticker=ticker.upper(), exchange=exchange
            ))
            db.commit()
            return True, ""
        except IntegrityError:
            return False, f"{ticker}.{exchange} is already in your watchlist."


def remove_from_watchlist(user_id: int, ticker: str, exchange: str) -> None:
    with SessionLocal() as db:
        db.query(WatchlistItem).filter(
            WatchlistItem.user_id == user_id,
            WatchlistItem.ticker  == ticker.upper(),
            WatchlistItem.exchange == exchange,
        ).delete()
        db.commit()


# ── Admin CRUD ────────────────────────────────────────────────────────────────

def list_users() -> list[dict]:
    with SessionLocal() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                "id":              u.id,
                "username":        u.username,
                "email":           u.email,
                "role":            u.role,
                "is_active":       u.is_active,
                "created_at":      u.created_at,
                "last_login":      u.last_login,
                "watchlist_count": len(u.watchlist),
            }
            for u in users
        ]


def toggle_active(user_id: int) -> None:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            user.is_active = not user.is_active
            db.commit()


def delete_user(user_id: int) -> None:
    with SessionLocal() as db:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()


def get_stats() -> dict:
    with SessionLocal() as db:
        return {
            "total_users":     db.query(User).count(),
            "active_users":    db.query(User).filter(User.is_active == True).count(),
            "total_watchlist": db.query(WatchlistItem).count(),
            "admin_count":     db.query(User).filter(User.role == "admin").count(),
        }


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def bootstrap() -> None:
    """Create tables and seed default admin on first run."""
    import os
    try:
        init_db()
    except Exception as exc:
        import streamlit as st
        db_url = os.getenv("DATABASE_URL", "NOT SET")
        masked  = db_url[:30] + "..." if len(db_url) > 30 else db_url
        st.error(
            f"**Database connection failed.**\n\n"
            f"DATABASE_URL starts with: `{masked}`\n\n"
            f"Error: `{type(exc).__name__}: {exc}`\n\n"
            "Check your Streamlit Cloud secrets → DATABASE_URL."
        )
        st.stop()
    with SessionLocal() as db:
        if db.query(User).count() == 0:
            db.add(User(
                email="admin@stocksight.in",
                username="admin",
                password_hash=_hash("Admin@123!"),
                role="admin",
            ))
            db.commit()
