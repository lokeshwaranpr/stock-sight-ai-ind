"""
StockSight India SaaS — User Watchlist (protected).
Users can save, browse, and remove tickers; quick-launch to the Dashboard.
"""
import streamlit as st

from core.auth import (
    current_user, logout, require_auth,
    add_to_watchlist, get_watchlist, remove_from_watchlist,
)
from core.indicators import SECTORS, fetch_and_engineer
from core.styles import inject_css, metric_card, mhtml

st.set_page_config(
    page_title="Watchlist — StockSight India",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)

user = require_auth()
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⭐ Watchlist")
    role_color = "#c084fc" if user["role"] == "admin" else "#4ade80"
    mhtml(
        f"""<div style="background:#111827; border:1px solid #1e3a5f; border-radius:10px;
            padding:10px 14px; margin-bottom:4px;">
            <span style="color:#94a3b8; font-size:12px;">Signed in as</span><br>
            <span style="color:#f1f5f9; font-weight:700;">@{user['username']}</span>
            <span style="color:{role_color}; font-size:11px; margin-left:6px;">
                [{user['role'].upper()}]
            </span>
        </div>"""
    )
    if st.button("Sign Out", use_container_width=True):
        logout()

    st.divider()
    st.markdown("#### Add to Watchlist")

    exchange  = st.radio("Exchange", ["NSE (.NS)", "BSE (.BO)"], horizontal=True, key="wl_exch")
    suffix    = ".NS" if "NSE" in exchange else ".BO"
    exch_code = suffix.lstrip(".")

    add_mode = st.radio("Pick by", ["Sector", "Manual Ticker"], horizontal=True)

    if add_mode == "Sector":
        sector       = st.selectbox("Sector", list(SECTORS.keys()), key="wl_sector")
        sector_stocks = SECTORS[sector]
        company_disp  = st.selectbox("Company", list(sector_stocks.values()), key="wl_company")
        new_ticker    = next(k for k, v in sector_stocks.items() if v == company_disp)
    else:
        new_ticker = st.text_input("Ticker Symbol", value="RELIANCE", key="wl_manual").upper().strip()

    st.markdown(f"**Will add:** `{new_ticker}.{exch_code}`")

    if st.button("⭐ Add to Watchlist", use_container_width=True, type="primary"):
        ok, msg = add_to_watchlist(user["id"], new_ticker, exch_code)
        if ok:
            st.success(f"Added **{new_ticker}.{exch_code}**")
            st.rerun()
        else:
            st.warning(msg)

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("# ⭐ My Watchlist")
st.markdown("*Saved stocks · Click Analyse to run a full dashboard*")
st.divider()

watchlist = get_watchlist(user["id"])

if not watchlist:
    st.info("📌 Your watchlist is empty. Add stocks using the sidebar.")
    st.stop()

# Summary stat
st.markdown(f"**{len(watchlist)} stock{'s' if len(watchlist) != 1 else ''}** saved")
st.markdown("<br>", unsafe_allow_html=True)

# ── Watchlist table with live snapshot ───────────────────────────────────────
for item in watchlist:
    ticker     = item["ticker"]
    exchange   = item["exchange"]
    full_tick  = f"{ticker}.{exchange}"
    added_fmt  = item["added_at"].strftime("%d %b %Y") if item["added_at"] else "—"
    exch_lbl   = "NSE" if exchange == "NS" else "BSE"
    badge_cls  = "nse-badge" if exchange == "NS" else "bse-badge"

    col_info, col_price, col_actions = st.columns([3, 4, 2])

    with col_info:
        mhtml(
            f"""<div style="padding:8px 0;">
                <span style="color:#60a5fa; font-size:18px; font-weight:700;
                    font-family:monospace;">{ticker}</span>
                <span class="exchange-badge {badge_cls}">{exch_lbl}</span><br>
                <span style="color:#475569; font-size:11px;">Added {added_fmt}</span>
            </div>"""
        )

    with col_price:
        with st.spinner(""):
            df, _ = fetch_and_engineer(full_tick, "5d")
        if df is not None and not df.empty:
            last = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2] if len(df) > 1 else last
            pct  = (last - prev) / prev * 100
            rsi  = df["RSI"].iloc[-1] if "RSI" in df.columns else float("nan")
            pcols = st.columns(3)
            metric_card(pcols[0], "Last",     f"₹{last:,.2f}", delta=pct)
            metric_card(pcols[1], "RSI (14)", f"{rsi:.1f}")
            metric_card(pcols[2], "5d Chg",   f"{pct:+.2f}%")
        else:
            st.warning(f"No data for {full_tick}")

    with col_actions:
        st.markdown("<br>", unsafe_allow_html=True)
        # Deep-link: switch to dashboard with this ticker pre-selected
        if st.button("📈 Analyse", key=f"analyse_{full_tick}", use_container_width=True):
            st.session_state["wl_goto_ticker"]   = ticker
            st.session_state["wl_goto_exchange"] = exchange
            st.switch_page("pages/1_Dashboard.py")
        if st.button("🗑️ Remove", key=f"remove_{full_tick}", use_container_width=True):
            remove_from_watchlist(user["id"], ticker, exchange)
            st.rerun()

    st.divider()
