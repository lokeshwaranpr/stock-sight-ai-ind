"""
StockSight India SaaS — Market Home (protected).
Top Nifty 50 gainers / losers today and investment suggestions.
"""
import warnings
warnings.filterwarnings("ignore")

from datetime import date
import streamlit as st
import pandas as pd
import yfinance as yf

from core.auth import require_auth, logout
from core.indicators import MARKET_UNIVERSE
from core.styles import inject_css, metric_card, mhtml

st.set_page_config(
    page_title="Market Home — StockSight India",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

user = require_auth()
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 StockSight India")
    role_color = "#c084fc" if user["role"] == "admin" else "#4ade80"
    mhtml(
        f'<div style="background:#111827; border:1px solid #1e3a5f; border-radius:10px;'
        f' padding:10px 14px; margin-bottom:4px;">'
        f'<span style="color:#94a3b8; font-size:12px;">Signed in as</span><br>'
        f'<span style="color:#f1f5f9; font-weight:700;">@{user["username"]}</span>'
        f'<span style="color:{role_color}; font-size:11px; margin-left:6px;">'
        f'[{user["role"].upper()}]</span></div>'
    )
    if st.button("Sign Out", use_container_width=True):
        logout()
    st.divider()
    st.caption("📊 Live market data · 5-min cache")


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_nifty50_snapshot() -> pd.DataFrame:
    tickers = [f"{t}.NS" for t in MARKET_UNIVERSE]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = yf.download(
            tickers, period="5d",
            auto_adjust=True,
            progress=False, threads=True,
        )
    rows = []
    for sym in MARKET_UNIVERSE:
        full = f"{sym}.NS"
        try:
            close = raw["Close"][full].dropna()
            if len(close) < 2:
                continue
            last  = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            first = float(close.iloc[0])
            rows.append({
                "ticker":     sym,
                "last_price": last,
                "change_1d":  (last - prev)  / prev  * 100,
                "change_5d":  (last - first) / first * 100,
            })
        except Exception:
            continue
    return pd.DataFrame(rows)


def _goto_dashboard(sym: str) -> None:
    st.session_state["dash_goto_ticker"]  = sym
    st.session_state["dash_goto_exchange"] = "NS"
    st.session_state["analysis_run"] = True
    st.switch_page("pages/1_Dashboard.py")


# ── Header ────────────────────────────────────────────────────────────────────
today_str = date.today().strftime("%A, %d %B %Y")
mhtml(
    f'<div style="padding:8px 0 16px 0;">'
    f'<h1 style="color:#f1f5f9; font-size:28px; margin:0 0 4px 0;">📊 Market Overview</h1>'
    f'<p style="color:#64748b; font-size:13px; margin:0;">'
    f'{today_str} &nbsp;·&nbsp; NSE · Nifty 50 + Top Stocks</p></div>'
)

with st.spinner("Fetching live market data…"):
    df = fetch_nifty50_snapshot()

if df.empty:
    st.error("Could not load market data. Please try again in a moment.")
    st.stop()

# ── Summary metrics ───────────────────────────────────────────────────────────
gainers_n = int((df["change_1d"] > 0).sum())
losers_n  = int((df["change_1d"] < 0).sum())
avg_move  = df["change_1d"].mean()
top_gain  = df["change_1d"].max()
top_loss  = df["change_1d"].min()

sm = st.columns(5)
metric_card(sm[0], "Stocks Tracked",  str(len(df)))
metric_card(sm[1], "Advancing",       str(gainers_n), delta=float(gainers_n))
metric_card(sm[2], "Declining",       str(losers_n))
metric_card(sm[3], "Avg Move",        f"{avg_move:+.2f}%", delta=avg_move)
metric_card(sm[4], "Best / Worst",    f"{top_gain:+.1f}% / {top_loss:+.1f}%")

st.markdown("<br>", unsafe_allow_html=True)


# ── Stock row card ────────────────────────────────────────────────────────────
def _stock_row_html(sym: str, price: float, ch1d: float, ch5d: float) -> str:
    c1d  = "#4ade80" if ch1d >= 0 else "#f87171"
    c5d  = "#4ade80" if ch5d >= 0 else "#f87171"
    arr  = "▲" if ch1d >= 0 else "▼"
    tr5  = "▲" if ch5d >= 0 else "▼"
    return (
        f'<div style="background:#111827; border:1px solid #1e3a5f; border-radius:10px;'
        f' padding:12px 16px; margin-bottom:6px;'
        f' display:flex; justify-content:space-between; align-items:center;">'
        f'<div>'
        f'<span style="color:#60a5fa; font-size:16px; font-weight:700; font-family:monospace;">{sym}</span>'
        f'<span style="color:#475569; font-size:11px; margin-left:6px;">NSE</span>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<span style="color:#f1f5f9; font-size:15px; font-weight:600;">₹{price:,.2f}</span><br>'
        f'<span style="color:{c1d}; font-size:13px; font-weight:700;">{arr} {ch1d:+.2f}%</span>'
        f'<span style="color:{c5d}; font-size:11px; margin-left:8px;">5d {tr5}{abs(ch5d):.1f}%</span>'
        f'</div></div>'
    )


# ── Winners & Losers ──────────────────────────────────────────────────────────
col_win, col_lose = st.columns(2)

winners   = df.nlargest(6, "change_1d")
losers_df = df.nsmallest(6, "change_1d")

with col_win:
    mhtml(
        '<div style="color:#4ade80; font-size:16px; font-weight:700;'
        ' margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #1e3a5f;">'
        '🟢 Top Gainers Today</div>'
    )
    for _, r in winners.iterrows():
        mhtml(_stock_row_html(r["ticker"], r["last_price"], r["change_1d"], r["change_5d"]))
        if st.button("📈 Analyse", key=f"g_{r['ticker']}", use_container_width=True):
            _goto_dashboard(r["ticker"])

with col_lose:
    mhtml(
        '<div style="color:#f87171; font-size:16px; font-weight:700;'
        ' margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #1e3a5f;">'
        '🔴 Top Losers Today</div>'
    )
    for _, r in losers_df.iterrows():
        mhtml(_stock_row_html(r["ticker"], r["last_price"], r["change_1d"], r["change_5d"]))
        if st.button("📈 Analyse", key=f"l_{r['ticker']}", use_container_width=True):
            _goto_dashboard(r["ticker"])

st.divider()


# ── Investment Suggestions ────────────────────────────────────────────────────
mhtml(
    '<h2 style="color:#f1f5f9; font-size:22px; margin:0 0 4px 0;">💡 Investment Suggestions</h2>'
)
mhtml(
    '<p style="color:#64748b; font-size:13px; margin:0 0 16px 0;">'
    'Signals based on price momentum and 5-day trend. Not financial advice.</p>'
)

momentum = df[(df["change_5d"] > 2.5) & (df["change_1d"] > 0)].nlargest(4, "change_5d")
dip_buy  = df[(df["change_5d"] > 1.5) & (df["change_1d"] < -0.3)].nlargest(4, "change_5d")
reversal = df[(df["change_5d"] < 0)   & (df["change_1d"] > 0.5)].nlargest(4, "change_1d")


def _suggest_html(sym: str, price: float, ch1d: float, ch5d: float,
                  reason: str, tag: str, tag_clr: str) -> str:
    c1d = "#4ade80" if ch1d >= 0 else "#f87171"
    arr = "▲" if ch1d >= 0 else "▼"
    return (
        f'<div style="background:linear-gradient(135deg,#111827,#1a2235);'
        f' border:1px solid #1e3a5f; border-radius:12px; padding:14px 16px; margin-bottom:10px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">'
        f'<div>'
        f'<span style="color:#60a5fa; font-size:15px; font-weight:700; font-family:monospace;">{sym}</span>'
        f'<span style="background:{tag_clr}22; color:{tag_clr}; font-size:10px; font-weight:700;'
        f' padding:2px 8px; border-radius:20px; margin-left:8px; border:1px solid {tag_clr}55;">{tag}</span>'
        f'</div>'
        f'<span style="color:#f1f5f9; font-size:14px; font-weight:600;">₹{price:,.2f}</span>'
        f'</div>'
        f'<span style="color:{c1d}; font-size:12px;">{arr} {ch1d:+.2f}% today</span>'
        f'<span style="color:#64748b; font-size:12px;"> &nbsp;|&nbsp; 5d: {ch5d:+.2f}%</span><br>'
        f'<span style="color:#94a3b8; font-size:11px;">{reason}</span>'
        f'</div>'
    )


c1, c2, c3 = st.columns(3)

with c1:
    mhtml(
        '<div style="color:#a78bfa; font-size:14px; font-weight:700; margin-bottom:10px;">'
        '🚀 Strong Momentum</div>'
    )
    if momentum.empty:
        st.info("No momentum picks today.")
    else:
        for _, r in momentum.iterrows():
            mhtml(_suggest_html(
                r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "5-day uptrend with positive follow-through. Strong buying interest.",
                "MOMENTUM", "#a78bfa",
            ))
            if st.button("Analyse", key=f"m_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

with c2:
    mhtml(
        '<div style="color:#34d399; font-size:14px; font-weight:700; margin-bottom:10px;">'
        '📉 Dip Buy Opportunity</div>'
    )
    if dip_buy.empty:
        st.info("No dip opportunities today.")
    else:
        for _, r in dip_buy.iterrows():
            mhtml(_suggest_html(
                r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "Healthy pullback within a weekly uptrend. Potential entry on weakness.",
                "DIP BUY", "#34d399",
            ))
            if st.button("Analyse", key=f"d_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

with c3:
    mhtml(
        '<div style="color:#fbbf24; font-size:14px; font-weight:700; margin-bottom:10px;">'
        '⚡ Reversal Signals</div>'
    )
    if reversal.empty:
        st.info("No reversal signals today.")
    else:
        for _, r in reversal.iterrows():
            mhtml(_suggest_html(
                r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "Negative 5-day trend turning positive today. Watch for follow-through.",
                "REVERSAL", "#fbbf24",
            ))
            if st.button("Analyse", key=f"r_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(
    "StockSight India · Data via Yahoo Finance (5-min cache) · "
    "Signals based on price momentum only · Not financial advice"
)
