"""Shared CSS and reusable UI components."""
from __future__ import annotations
import re

import streamlit as st


def mhtml(markup: str) -> None:
    """Render HTML via st.markdown, collapsing newlines so closing tags never leak as text."""
    st.markdown(re.sub(r"\s*\n\s*", " ", markup.strip()), unsafe_allow_html=True)

_CSS = """
<style>
/* ── Base ── */
.main { background-color: #0a0f1e; }

/* ── Metric cards (native st.metric) ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #111827, #1a2235);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px 20px !important;
    text-align: center;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 12px !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    justify-content: center;
}
[data-testid="stMetricLabel"] > div { justify-content: center; }
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    font-family: monospace !important;
    justify-content: center;
}
[data-testid="stMetricDelta"] { justify-content: center; }
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] > div {
    font-size: 13px !important;
    justify-content: center;
}

/* ── Exchange badges ── */
.exchange-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-left: 8px;
}
.nse-badge { background: #1a3a5f; color: #60a5fa; border: 1px solid #2563eb; }
.bse-badge { background: #3a1a1a; color: #f87171; border: 1px solid #dc2626; }

/* ── Role badges ── */
.role-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
}
.role-admin { background: #3a1f5f; color: #c084fc; border: 1px solid #7c3aed; }
.role-user  { background: #1a3a2f; color: #4ade80; border: 1px solid #16a34a; }

/* ── Auth card ── */
.auth-wrap {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 40px;
}
.auth-card {
    background: linear-gradient(135deg, #111827, #1a2235);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 36px 40px;
    width: 100%;
    max-width: 420px;
}
.auth-logo  { font-size: 36px; margin-bottom: 8px; }
.auth-title { color: #f1f5f9; font-size: 22px; font-weight: 700; margin-bottom: 2px; }
.auth-sub   { color: #64748b; font-size: 13px; margin-bottom: 0; }

/* ── Watchlist item ── */
.wl-row {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.wl-ticker { color: #60a5fa; font-size: 16px; font-weight: 700; font-family: monospace; }
.wl-exch   { color: #94a3b8; font-size: 12px; margin-left: 8px; }
.wl-date   { color: #475569; font-size: 11px; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def metric_card(col, label: str, value: str, delta: float | None = None) -> None:
    """Render a styled KPI card using native st.metric (CSS-overridden)."""
    with col:
        if delta is not None:
            st.metric(label=label, value=value, delta=f"{delta:+.2f}%")
        else:
            st.metric(label=label, value=value)


def role_badge(role: str) -> str:
    cls = "role-admin" if role == "admin" else "role-user"
    return f'<span class="role-badge {cls}">{role.upper()}</span>'


def exchange_badge(label: str, suffix: str) -> str:
    cls = "nse-badge" if suffix == ".NS" else "bse-badge"
    return f'<span class="exchange-badge {cls}">{label}</span>'
