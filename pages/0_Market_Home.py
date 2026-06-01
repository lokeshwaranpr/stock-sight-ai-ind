"""
StockSight India SaaS — Market Home (protected).
India Fear & Greed Index · Top gainers/losers · Investment suggestions.
"""
import warnings
warnings.filterwarnings("ignore")

from datetime import date
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

from core.auth import require_auth, logout
from core.indicators import MARKET_UNIVERSE, get_logo_url
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


# ── Data functions ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_snapshot() -> pd.DataFrame:
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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_india_vix() -> float | None:
    try:
        hist = yf.Ticker("^INDIAVIX").history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


def compute_fear_greed(df: pd.DataFrame, vix: float | None) -> dict:
    total = len(df)
    if total == 0:
        return {"score": 50, "label": "Neutral", "color": "#fbbf24",
                "breadth": 50.0, "momentum": 50.0, "vix_score": None, "vix_val": None}

    breadth   = (df["change_1d"] > 0).sum() / total * 100
    momentum  = (df["change_5d"] > 0).sum() / total * 100

    if vix is not None:
        # VIX < 12 → score ~90 (greed), VIX > 30 → score ~0 (fear)
        vix_score = max(0.0, min(100.0, (32 - vix) / 22 * 100))
        score = round(0.35 * breadth + 0.35 * momentum + 0.30 * vix_score)
    else:
        vix_score = None
        score = round(0.50 * breadth + 0.50 * momentum)

    score = int(max(0, min(100, score)))

    if score < 25:
        label, color = "Extreme Fear", "#f87171"
    elif score < 45:
        label, color = "Fear", "#fb923c"
    elif score < 55:
        label, color = "Neutral", "#fbbf24"
    elif score < 75:
        label, color = "Greed", "#4ade80"
    else:
        label, color = "Extreme Greed", "#22c55e"

    return {
        "score":     score,
        "label":     label,
        "color":     color,
        "breadth":   round(breadth, 1),
        "momentum":  round(momentum, 1),
        "vix_score": round(vix_score, 1) if vix_score is not None else None,
        "vix_val":   round(vix, 2) if vix is not None else None,
    }


def make_fg_gauge(fg: dict) -> go.Figure:
    score = fg["score"]
    color = fg["color"]
    label = fg["label"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 52, "color": color, "family": "monospace"}, "suffix": ""},
        title={
            "text": f'<b style="font-size:18px;">{label}</b>',
            "font": {"size": 16, "color": color},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#1e3a5f",
                "tickfont": {"color": "#475569", "size": 10},
                "tickvals": [0, 25, 45, 55, 75, 100],
                "ticktext": ["0", "25", "45", "55", "75", "100"],
            },
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "#0a0f1e",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  25],  "color": "#1f0a0a"},
                {"range": [25, 45],  "color": "#1f130a"},
                {"range": [45, 55],  "color": "#1a1a0a"},
                {"range": [55, 75],  "color": "#0a1a10"},
                {"range": [75, 100], "color": "#081a08"},
            ],
            "threshold": {
                "line": {"color": color, "width": 5},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0a0f1e",
        margin={"t": 80, "b": 10, "l": 20, "r": 20},
        height=260,
        font={"family": "Inter, sans-serif"},
    )
    return fig


def _component_bar_html(label: str, score: float, color: str, detail: str = "") -> str:
    pct = int(score)
    return (
        f'<div style="margin-bottom:14px;">'
        f'<div style="display:flex; justify-content:space-between; margin-bottom:4px;">'
        f'<span style="color:#94a3b8; font-size:12px;">{label}</span>'
        f'<span style="color:{color}; font-size:12px; font-weight:700;">{pct}/100'
        f'{(" · " + detail) if detail else ""}</span>'
        f'</div>'
        f'<div style="background:#1e293b; border-radius:4px; height:6px;">'
        f'<div style="background:{color}; width:{pct}%; height:6px; border-radius:4px; '
        f'transition:width 0.5s;"></div>'
        f'</div>'
        f'</div>'
    )


def _goto_dashboard(sym: str) -> None:
    st.session_state["dash_goto_ticker"]   = sym
    st.session_state["dash_goto_exchange"] = "NS"
    st.session_state["analysis_run"]       = True
    st.switch_page("pages/1_Dashboard.py")


# ── Header ────────────────────────────────────────────────────────────────────
today_str = date.today().strftime("%A, %d %B %Y")
mhtml(
    f'<div style="padding:8px 0 12px 0;">'
    f'<h1 style="color:#f1f5f9; font-size:28px; margin:0 0 4px 0;">📊 Market Overview</h1>'
    f'<p style="color:#64748b; font-size:13px; margin:0;">'
    f'{today_str} &nbsp;·&nbsp; NSE · Nifty 50 + Top Stocks</p></div>'
)

with st.spinner("Fetching live market data…"):
    df  = fetch_market_snapshot()
    vix = fetch_india_vix()

if df.empty:
    st.error("Could not load market data. Please try again in a moment.")
    st.stop()

fg = compute_fear_greed(df, vix)


# ── Fear & Greed Index ────────────────────────────────────────────────────────
mhtml(
    '<div style="background:linear-gradient(135deg,#0f172a,#111827);'
    ' border:1px solid #1e3a5f; border-radius:16px; padding:20px 24px 8px 24px; margin-bottom:20px;">'
    '<div style="display:flex; align-items:center; gap:10px; margin-bottom:2px;">'
    '<span style="font-size:22px;">🧠</span>'
    '<span style="color:#f1f5f9; font-size:18px; font-weight:700;">India Fear &amp; Greed Index</span>'
    '<span style="background:#1e3a5f; color:#60a5fa; font-size:10px; font-weight:700;'
    ' padding:2px 10px; border-radius:20px; margin-left:6px; border:1px solid #2563eb44;">LIVE</span>'
    '</div>'
    '<p style="color:#475569; font-size:12px; margin:0 0 12px 0;">'
    'Composite of market breadth, 5-day price momentum and India VIX volatility index.</p>'
    '</div>'
)

gauge_col, info_col = st.columns([5, 4])

with gauge_col:
    st.plotly_chart(make_fg_gauge(fg), use_container_width=True, config={"displayModeBar": False})

with info_col:
    st.markdown("<br>", unsafe_allow_html=True)

    # Score interpretation
    score_emoji = "😱" if fg["score"] < 25 else "😰" if fg["score"] < 45 else "😐" if fg["score"] < 55 else "😊" if fg["score"] < 75 else "🤑"
    mhtml(
        f'<div style="background:#111827; border:1px solid #1e3a5f; border-radius:12px;'
        f' padding:16px 20px; margin-bottom:16px;">'
        f'<div style="font-size:36px; margin-bottom:4px;">{score_emoji}</div>'
        f'<div style="color:{fg["color"]}; font-size:24px; font-weight:700; margin-bottom:4px;">'
        f'{fg["label"]}</div>'
        f'<div style="color:#475569; font-size:12px;">'
        f'{"Investors are extremely fearful — may signal a buying opportunity." if fg["score"] < 25 else "Market sentiment is cautious. Tread carefully." if fg["score"] < 45 else "Sentiment is balanced between buyers and sellers." if fg["score"] < 55 else "Investors are optimistic. Watch for overheating." if fg["score"] < 75 else "Market euphoria detected. Consider taking profits."}'
        f'</div></div>'
    )

    # Component bars
    breadth_color   = "#4ade80" if fg["breadth"]  > 55 else "#fb923c" if fg["breadth"]  < 45 else "#fbbf24"
    momentum_color  = "#4ade80" if fg["momentum"] > 55 else "#fb923c" if fg["momentum"] < 45 else "#fbbf24"

    mhtml(
        _component_bar_html("Market Breadth", fg["breadth"],  breadth_color,
                             f'{int(fg["breadth"])}% stocks up today') +
        _component_bar_html("Price Momentum", fg["momentum"], momentum_color,
                             f'{int(fg["momentum"])}% stocks up 5d')  +
        (
            _component_bar_html(
                "India VIX (inverted)", fg["vix_score"], "#a78bfa",
                f'VIX = {fg["vix_val"]}'
            )
            if fg["vix_score"] is not None
            else _component_bar_html("India VIX", 50, "#475569", "unavailable")
        )
    )

st.divider()


# ── Summary metrics ───────────────────────────────────────────────────────────
gainers_n = int((df["change_1d"] > 0).sum())
losers_n  = int((df["change_1d"] < 0).sum())
avg_move  = df["change_1d"].mean()
top_gain  = df["change_1d"].max()
top_loss  = df["change_1d"].min()

sm = st.columns(5)
metric_card(sm[0], "Stocks Tracked", str(len(df)))
metric_card(sm[1], "Advancing",      str(gainers_n), delta=float(gainers_n))
metric_card(sm[2], "Declining",      str(losers_n))
metric_card(sm[3], "Avg Move",       f"{avg_move:+.2f}%", delta=avg_move)
metric_card(sm[4], "Best / Worst",   f"{top_gain:+.1f}% / {top_loss:+.1f}%")

st.markdown("<br>", unsafe_allow_html=True)


# ── Stock row card ────────────────────────────────────────────────────────────
def _stock_row_html(sym: str, price: float, ch1d: float, ch5d: float) -> str:
    c1d      = "#4ade80" if ch1d >= 0 else "#f87171"
    c5d      = "#4ade80" if ch5d >= 0 else "#f87171"
    arr      = "▲" if ch1d >= 0 else "▼"
    tr5      = "▲" if ch5d >= 0 else "▼"
    logo_url = get_logo_url(sym)
    logo_img  = (
        f'<img src="{logo_url}" width="32" height="32"'
        f' style="position:absolute;top:0;left:0;border-radius:5px;object-fit:cover;"'
        f' onerror="this.style.display=\'none\'">'
        if logo_url else ""
    )
    logo_html = (
        f'<div style="position:relative;width:32px;height:32px;border-radius:6px;'
        f'background:linear-gradient(135deg,#1e3a5f,#0f2744);border:1px solid #334155;'
        f'display:flex;align-items:center;justify-content:center;overflow:hidden;'
        f'margin-right:10px;flex-shrink:0;">'
        f'<span style="color:#60a5fa;font-size:10px;font-weight:800;">{sym[:2]}</span>'
        f'{logo_img}</div>'
    )
    return (
        f'<div style="background:#111827; border:1px solid #1e3a5f; border-radius:10px;'
        f' padding:10px 14px; margin-bottom:6px;'
        f' display:flex; justify-content:space-between; align-items:center;">'
        f'<div style="display:flex; align-items:center;">'
        f'{logo_html}'
        f'<div>'
        f'<span style="color:#60a5fa; font-size:15px; font-weight:700; font-family:monospace;">{sym}</span>'
        f'<span style="color:#475569; font-size:11px; margin-left:6px;">NSE</span>'
        f'</div></div>'
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
mhtml('<h2 style="color:#f1f5f9; font-size:22px; margin:0 0 4px 0;">💡 Investment Suggestions</h2>')
mhtml(
    '<p style="color:#64748b; font-size:13px; margin:0 0 16px 0;">'
    'Signals based on price momentum and 5-day trend. Not financial advice.</p>'
)

momentum_df = df[(df["change_5d"] > 2.5) & (df["change_1d"] > 0)].nlargest(4, "change_5d")
dip_buy     = df[(df["change_5d"] > 1.5) & (df["change_1d"] < -0.3)].nlargest(4, "change_5d")
reversal    = df[(df["change_5d"] < 0)   & (df["change_1d"] > 0.5)].nlargest(4, "change_1d")


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
    mhtml('<div style="color:#a78bfa; font-size:14px; font-weight:700; margin-bottom:10px;">🚀 Strong Momentum</div>')
    if momentum_df.empty:
        st.info("No momentum picks today.")
    else:
        for _, r in momentum_df.iterrows():
            mhtml(_suggest_html(r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "5-day uptrend with positive follow-through. Strong buying interest.",
                "MOMENTUM", "#a78bfa"))
            if st.button("Analyse", key=f"m_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

with c2:
    mhtml('<div style="color:#34d399; font-size:14px; font-weight:700; margin-bottom:10px;">📉 Dip Buy Opportunity</div>')
    if dip_buy.empty:
        st.info("No dip opportunities today.")
    else:
        for _, r in dip_buy.iterrows():
            mhtml(_suggest_html(r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "Healthy pullback within a weekly uptrend. Potential entry on weakness.",
                "DIP BUY", "#34d399"))
            if st.button("Analyse", key=f"d_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

with c3:
    mhtml('<div style="color:#fbbf24; font-size:14px; font-weight:700; margin-bottom:10px;">⚡ Reversal Signals</div>')
    if reversal.empty:
        st.info("No reversal signals today.")
    else:
        for _, r in reversal.iterrows():
            mhtml(_suggest_html(r["ticker"], r["last_price"], r["change_1d"], r["change_5d"],
                "Negative 5-day trend turning positive today. Watch for follow-through.",
                "REVERSAL", "#fbbf24"))
            if st.button("Analyse", key=f"r_{r['ticker']}", use_container_width=True):
                _goto_dashboard(r["ticker"])

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(
    "StockSight India · Data via Yahoo Finance (5-min cache) · "
    "Fear & Greed = breadth + momentum + India VIX · Not financial advice"
)
