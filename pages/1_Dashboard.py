"""
StockSight India SaaS — Main Analytics Dashboard (protected).
Ported from app.py; uses shared core/ modules for auth, styles, and data.
"""
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from prophet import Prophet

from core.auth import current_user, logout, require_auth, add_to_watchlist
from core.indicators import (
    SECTORS, NIFTY50, fetch_and_engineer, make_india_holidays, get_logo_url,
)
from core.styles import inject_css, metric_card, exchange_badge, mhtml

st.set_page_config(
    page_title="Dashboard — StockSight India",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

user = require_auth()
inject_css()

# Handle deep-link from Market Home / Watchlist (pre-populate ticker + auto-run)
_goto = st.session_state.pop("dash_goto_ticker", None)
if _goto:
    st.session_state["_dash_pick_by"]      = "Manual Ticker"
    st.session_state["_dash_manual_input"] = _goto
    st.session_state["analysis_run"]       = True

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 StockSight India")
    st.markdown("*NSE · BSE · Nifty 50*")

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

    exchange = st.radio("Exchange", ["NSE (.NS)", "BSE (.BO)"], horizontal=True)
    suffix   = ".NS" if exchange == "NSE (.NS)" else ".BO"
    exch_lbl = "NSE" if suffix == ".NS" else "BSE"

    st.markdown("#### Stock Selection")
    _default_pick = st.session_state.get("_dash_pick_by", "Sector")
    pick_by = st.radio(
        "Pick by", ["Sector", "Nifty 50", "Manual Ticker"],
        index=["Sector", "Nifty 50", "Manual Ticker"].index(_default_pick),
        horizontal=True,
    )

    base_ticker: str
    if pick_by == "Sector":
        sector        = st.selectbox("Sector", list(SECTORS.keys()))
        sector_stocks = SECTORS[sector]
        company_disp  = st.selectbox("Company", list(sector_stocks.values()))
        base_ticker   = next(k for k, v in sector_stocks.items() if v == company_disp)
    elif pick_by == "Nifty 50":
        base_ticker = st.selectbox("Nifty 50 Stock", sorted(NIFTY50))
    else:
        _default_sym = st.session_state.get("_dash_manual_input", "RELIANCE")
        base_ticker  = st.text_input("Ticker Symbol", value=_default_sym).upper().strip()

    ticker = base_ticker + suffix
    st.markdown(f"**Full ticker:** `{ticker}`")
    st.divider()

    period_label = st.selectbox(
        "Historical Range",
        ["3 Months", "6 Months", "1 Year", "2 Years", "5 Years"],
        index=2,
    )
    period = {"3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y",
              "2 Years": "2y", "5 Years": "5y"}[period_label]

    forecast_days = st.slider("Forecast Horizon (days)", 7, 90, 30)

    show_indicators: list[str] = st.multiselect(
        "Technical Indicators",
        ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "RSI", "MACD"],
        default=["SMA 20", "SMA 50"],
    )
    st.divider()
    if st.button("🚀 Run Analysis", use_container_width=True, type="primary"):
        st.session_state["analysis_run"] = True

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📈 StockSight India")
st.markdown("*Real-time NSE & BSE data · Technical indicators · AI price forecasting*")
st.divider()

# ── Landing state ─────────────────────────────────────────────────────────────
if not st.session_state.get("analysis_run"):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 🌟 Popular Picks")
        st.markdown(
            "- **RELIANCE** — Reliance Industries\n"
            "- **TCS** — Tata Consultancy Services\n"
            "- **HDFCBANK** — HDFC Bank\n"
            "- **INFY** — Infosys\n"
            "- **SBIN** — State Bank of India\n"
            "- **BHARTIARTL** — Bharti Airtel"
        )
    with col_r:
        st.markdown("### 📊 Nifty 50 Snapshot")
        st.info("📌 Configure your stock in the sidebar, then click **Run Analysis**.")
    st.stop()

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner(f"💡 Fetching {ticker} from {exch_lbl}…"):
    df, info = fetch_and_engineer(ticker, period)

if df is None or df.empty:
    st.error(
        f"❌ No data found for **{ticker}**. "
        "Try switching exchange (NSE ↔ BSE) or check the ticker symbol."
    )
    st.stop()

# ── Metric cards ──────────────────────────────────────────────────────────────
last  = df["Close"].iloc[-1]
prev  = df["Close"].iloc[-2]
pct   = (last - prev) / prev * 100
high  = df["High"].max()
low   = df["Low"].min()
vol   = df["Volume"].iloc[-1]
rsi   = df["RSI"].iloc[-1]

company_name = info.get("longName", base_ticker)
logo_url     = get_logo_url(base_ticker, info)

col_logo, col_name, col_wl = st.columns([0.7, 4, 1])
with col_logo:
    initials = "".join(w[0] for w in company_name.split()[:2]).upper()
    logo_img  = (
        f'<img src="{logo_url}" width="52" height="52"'
        f' style="position:absolute;top:0;left:0;border-radius:9px;object-fit:cover;"'
        f' onerror="this.style.display=\'none\'">'
        if logo_url else ""
    )
    mhtml(
        f'<div style="display:flex;align-items:center;height:72px;">'
        f'<div style="position:relative;width:52px;height:52px;border-radius:10px;'
        f'background:linear-gradient(135deg,#1e3a5f,#0f2744);'
        f'border:1px solid #334155;display:flex;align-items:center;'
        f'justify-content:center;overflow:hidden;flex-shrink:0;">'
        f'<span style="color:#60a5fa;font-size:15px;font-weight:800;">{initials}</span>'
        f'{logo_img}'
        f'</div></div>'
    )
with col_name:
    st.markdown(
        f"### {company_name} "
        + exchange_badge(exch_lbl, suffix),
        unsafe_allow_html=True,
    )
with col_wl:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⭐ Add to Watchlist", use_container_width=True):
        ok, msg = add_to_watchlist(user["id"], base_ticker, suffix.lstrip("."))
        st.toast(msg if not ok else f"Added {base_ticker} to watchlist!", icon="⭐" if ok else "⚠️")

def _fmt_vol(v: float) -> str:
    return f"{v / 1e5:.2f}L" if v < 1e7 else f"{v / 1e7:.2f}Cr"

cols = st.columns(5)
metric_card(cols[0], "Last Price",  f"₹{last:,.2f}",  delta=pct)
metric_card(cols[1], "52W High",    f"₹{high:,.2f}")
metric_card(cols[2], "52W Low",     f"₹{low:,.2f}")
metric_card(cols[3], "Volume",      _fmt_vol(vol))
metric_card(cols[4], "RSI (14)",    f"{rsi:.1f}")

# ── Candlestick + indicators ──────────────────────────────────────────────────
has_rsi  = "RSI"  in show_indicators
has_macd = "MACD" in show_indicators

# Always add a volume row (row 2), then RSI and MACD
n_sub   = int(has_rsi) + int(has_macd)
n_rows  = 2 + n_sub   # candle + volume + optional sub-charts

candle_h = 0.55
vol_h    = 0.10
sub_h    = round((1 - candle_h - vol_h) / n_sub, 3) if n_sub else 0
row_heights = [candle_h, vol_h] + [sub_h] * n_sub

fig = make_subplots(
    rows=n_rows, cols=1,
    shared_xaxes=True,
    row_heights=row_heights,
    vertical_spacing=0.02,
)

# Candlestick
fig.add_trace(
    go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price",
        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        increasing_fillcolor="#16a34a",  decreasing_fillcolor="#dc2626",
        line=dict(width=1),
    ),
    row=1, col=1,
)

# Overlay indicators on candle row
_overlays = {
    "SMA 20": ("SMA_20", "#60a5fa", 2),
    "SMA 50": ("SMA_50", "#f59e0b", 2),
    "EMA 20": ("EMA_20", "#c084fc", 2),
}
for key, (col_name_ind, color, lw) in _overlays.items():
    if key in show_indicators:
        fig.add_trace(
            go.Scatter(x=df.index, y=df[col_name_ind], name=key,
                       line=dict(color=color, width=lw),
                       hovertemplate=f"{key}: ₹%{{y:,.2f}}<extra></extra>"),
            row=1, col=1,
        )

if "Bollinger Bands" in show_indicators:
    fig.add_trace(
        go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper",
                   line=dict(color="#7dd3fc", width=1.2, dash="dot"),
                   hovertemplate="BB Upper: ₹%{y:,.2f}<extra></extra>"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower",
                   line=dict(color="#7dd3fc", width=1.2, dash="dot"),
                   fill="tonexty", fillcolor="rgba(125,211,252,0.06)",
                   hovertemplate="BB Lower: ₹%{y:,.2f}<extra></extra>"),
        row=1, col=1,
    )

# Volume bars (row 2, colored by candle direction)
vol_colors = [
    "#16a34a" if c >= o else "#dc2626"
    for c, o in zip(df["Close"], df["Open"])
]
fig.add_trace(
    go.Bar(x=df.index, y=df["Volume"], name="Volume",
           marker_color=vol_colors, marker_opacity=0.6,
           hovertemplate="%{x|%d %b %Y}<br>Volume: %{y:,.0f}<extra></extra>",
           showlegend=False),
    row=2, col=1,
)
fig.update_yaxes(tickformat=".2s", title_text="Vol",
                 title_font=dict(size=10, color="#475569"),
                 tickfont=dict(size=9, color="#475569"), row=2, col=1)

# RSI and MACD sub-charts
sub_row = 3
if has_rsi:
    fig.add_trace(
        go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                   line=dict(color="#e879f9", width=2),
                   hovertemplate="RSI: %{y:.1f}<extra></extra>"),
        row=sub_row, col=1,
    )
    # Overbought / oversold bands
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.06)",
                  line_width=0, row=sub_row, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(34,197,94,0.06)",
                  line_width=0, row=sub_row, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                  line_width=1.2, row=sub_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e",
                  line_width=1.2, row=sub_row, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="#475569",
                  line_width=1, row=sub_row, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100],
                     title_font=dict(size=10, color="#475569"),
                     tickfont=dict(size=9, color="#475569"),
                     tickvals=[30, 50, 70], row=sub_row, col=1)
    sub_row += 1

if has_macd:
    macd_colors = ["#22c55e" if v >= 0 else "#ef4444"
                   for v in df["MACD_hist"].fillna(0)]
    fig.add_trace(
        go.Bar(x=df.index, y=df["MACD_hist"], name="Histogram",
               marker_color=macd_colors, marker_opacity=0.7,
               hovertemplate="Hist: %{y:.3f}<extra></extra>"),
        row=sub_row, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                   line=dict(color="#60a5fa", width=2),
                   hovertemplate="MACD: %{y:.3f}<extra></extra>"),
        row=sub_row, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                   line=dict(color="#fb923c", width=2),
                   hovertemplate="Signal: %{y:.3f}<extra></extra>"),
        row=sub_row, col=1,
    )
    fig.add_hline(y=0, line_color="#475569", line_width=1, row=sub_row, col=1)
    fig.update_yaxes(title_text="MACD",
                     title_font=dict(size=10, color="#475569"),
                     tickfont=dict(size=9, color="#475569"), row=sub_row, col=1)

# Global layout
_chart_height = 620 if n_rows == 2 else 620 + n_sub * 160
fig.update_layout(
    height=_chart_height,
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    xaxis_rangeslider_visible=False,
    legend=dict(
        orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
        bgcolor="rgba(10,15,30,0.85)", bordercolor="#1e3a5f", borderwidth=1,
        font=dict(size=11, color="#cbd5e1"),
    ),
    margin=dict(l=10, r=10, t=50, b=10),
    yaxis_tickprefix="₹",
    font=dict(family="Inter, sans-serif", size=11, color="#94a3b8"),
    hoverlabel=dict(
        bgcolor="#1e293b", bordercolor="#334155",
        font_size=12, font_color="#f1f5f9",
    ),
    hovermode="x unified",
)

# Grid lines on every subplot
for r in range(1, n_rows + 1):
    fig.update_xaxes(
        gridcolor="#1e293b", gridwidth=1,
        zerolinecolor="#334155", zerolinewidth=1,
        showspikes=True, spikecolor="#475569",
        spikethickness=1, spikedash="dot", spikemode="across",
        row=r, col=1,
    )
    fig.update_yaxes(
        gridcolor="#1e293b", gridwidth=1,
        zerolinecolor="#334155", zerolinewidth=1,
        row=r, col=1,
    )

# Price axis font
fig.update_yaxes(tickprefix="₹", tickfont=dict(size=11, color="#94a3b8"), row=1, col=1)
# Hide x-axis labels on all rows except the last
for r in range(1, n_rows):
    fig.update_xaxes(showticklabels=False, row=r, col=1)
fig.update_xaxes(tickfont=dict(size=10, color="#64748b"), row=n_rows, col=1)

st.plotly_chart(fig, use_container_width=True, config={
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "filename": f"{ticker}_chart", "scale": 2},
})

# ── Prophet forecast ──────────────────────────────────────────────────────────
st.subheader(f"🔮 AI Forecast — Next {forecast_days} Trading Days")

with st.spinner("Training forecasting model with Indian market calendar…"):
    import pandas as pd
    prophet_df = df[["Close"]].reset_index()[["Date", "Close"]].copy()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
        interval_width=0.8,
        holidays=make_india_holidays(),
    )
    model.fit(prophet_df)
    future   = model.make_future_dataframe(periods=forecast_days, freq="B")
    forecast = model.predict(future)

cutoff     = prophet_df["ds"].max()
fcast_hist = forecast[forecast["ds"] <= cutoff]
fcast_f    = forecast[forecast["ds"] >  cutoff]

fig2 = go.Figure()

# Actual price line
fig2.add_trace(go.Scatter(
    x=prophet_df["ds"], y=prophet_df["y"], name="Actual Price",
    line=dict(color="#60a5fa", width=2.5),
    hovertemplate="%{x|%d %b %Y}<br>Actual: ₹%{y:,.2f}<extra></extra>",
))

# Model fit on historical period
fig2.add_trace(go.Scatter(
    x=fcast_hist["ds"], y=fcast_hist["yhat"], name="Model Fit",
    line=dict(color="#475569", width=1.5, dash="dot"),
    hovertemplate="Fit: ₹%{y:,.2f}<extra></extra>",
))

# Confidence band (filled between upper and lower)
fig2.add_trace(go.Scatter(
    x=fcast_f["ds"], y=fcast_f["yhat_upper"], name="Upper (80% CI)",
    line=dict(color="rgba(34,197,94,0)", width=0),
    hovertemplate="Upper: ₹%{y:,.2f}<extra></extra>",
    showlegend=False,
))
fig2.add_trace(go.Scatter(
    x=fcast_f["ds"], y=fcast_f["yhat_lower"], name="80% Confidence Band",
    line=dict(color="rgba(34,197,94,0)", width=0),
    fill="tonexty", fillcolor="rgba(34,197,94,0.18)",
    hovertemplate="Lower: ₹%{y:,.2f}<extra></extra>",
))

# Forecast centre line
fig2.add_trace(go.Scatter(
    x=fcast_f["ds"], y=fcast_f["yhat"], name="Forecast",
    line=dict(color="#22c55e", width=3),
    hovertemplate="%{x|%d %b %Y}<br>Forecast: ₹%{y:,.2f}<extra></extra>",
))

# Vertical divider at forecast start
fig2.add_vline(x=cutoff, line_width=1.5, line_dash="dash", line_color="#475569")
fig2.add_annotation(
    x=cutoff, y=0.97, yref="paper",
    text="Forecast →", showarrow=False, xanchor="left",
    font=dict(color="#64748b", size=11),
)

fig2.update_layout(
    height=480,
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
        bgcolor="rgba(10,15,30,0.85)", bordercolor="#1e3a5f", borderwidth=1,
        font=dict(size=11, color="#cbd5e1"),
    ),
    margin=dict(l=10, r=10, t=50, b=10),
    yaxis=dict(
        tickprefix="₹", gridcolor="#1e293b", gridwidth=1,
        zerolinecolor="#334155", tickfont=dict(size=11, color="#94a3b8"),
    ),
    xaxis=dict(
        gridcolor="#1e293b", gridwidth=1,
        tickfont=dict(size=10, color="#64748b"),
        showspikes=True, spikecolor="#475569", spikethickness=1, spikedash="dot",
    ),
    font=dict(family="Inter, sans-serif", size=11, color="#94a3b8"),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#334155",
                    font_size=12, font_color="#f1f5f9"),
    hovermode="x unified",
)
st.plotly_chart(fig2, use_container_width=True, config={
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "filename": f"{ticker}_forecast", "scale": 2},
})

end_price  = fcast_f["yhat"].iloc[-1]
exp_change = (end_price - last) / last * 100
fcols = st.columns(3)
metric_card(fcols[0], f"Forecast (+{forecast_days}d)", f"₹{end_price:,.2f}", delta=exp_change)
metric_card(fcols[1], "Upper Bound (80%)",             f"₹{fcast_f['yhat_upper'].iloc[-1]:,.2f}")
metric_card(fcols[2], "Lower Bound (80%)",             f"₹{fcast_f['yhat_lower'].iloc[-1]:,.2f}")

# ── Returns & Volatility ──────────────────────────────────────────────────────
st.subheader("📉 Returns & Volatility")
col_ret, col_vol = st.columns(2)

_sub_layout = dict(
    template="plotly_dark",
    paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
    margin=dict(l=10, r=10, t=50, b=10),
    showlegend=False,
    font=dict(family="Inter, sans-serif", size=11, color="#94a3b8"),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#334155",
                    font_size=12, font_color="#f1f5f9"),
    xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=10, color="#64748b"),
               showspikes=True, spikecolor="#475569", spikethickness=1, spikedash="dot"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
               tickfont=dict(size=10, color="#94a3b8")),
    hovermode="x unified",
)

with col_ret:
    ret_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df["Daily_Return"].fillna(0)]
    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(
        x=df.index, y=df["Daily_Return"],
        marker_color=ret_colors, marker_opacity=0.8,
        hovertemplate="%{x|%d %b %Y}<br>Return: %{y:+.2f}%<extra></extra>",
    ))
    fig_r.add_hline(y=0, line_color="#334155", line_width=1.5)
    fig_r.update_layout(
        height=320, title=dict(text="📊 Daily Returns (%)", font=dict(size=13, color="#cbd5e1")),
        yaxis_ticksuffix="%",
        **_sub_layout,
    )
    st.plotly_chart(fig_r, use_container_width=True)

with col_vol:
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(
        x=df.index, y=df["Volatility"],
        fill="tozeroy", fillcolor="rgba(251,191,36,0.12)",
        line=dict(color="#fbbf24", width=2.5),
        hovertemplate="%{x|%d %b %Y}<br>Volatility: %{y:.2f}%<extra></extra>",
    ))
    # Mark current volatility level
    curr_vol = df["Volatility"].iloc[-1]
    fig_v.add_hline(y=curr_vol, line_dash="dot", line_color="#fb923c",
                    line_width=1.2,
                    annotation_text=f"Now: {curr_vol:.2f}%",
                    annotation_position="top right",
                    annotation_font=dict(color="#fb923c", size=10))
    fig_v.update_layout(
        height=320,
        title=dict(text="🌊 20-Day Rolling Volatility (%)", font=dict(size=13, color="#cbd5e1")),
        yaxis_ticksuffix="%",
        **_sub_layout,
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("🗃️ Engineered Dataset"):
    disp_cols  = ["Open","High","Low","Close","Volume","SMA_20","SMA_50","EMA_20",
                  "RSI","Daily_Return","Volatility"]
    price_cols = {"Open","High","Low","Close","SMA_20","SMA_50","EMA_20"}
    fmt = {c: ("₹{:.2f}" if c in price_cols else "{:.2f}")
           for c in disp_cols if c != "Volume"}
    st.dataframe(df[disp_cols].tail(100).style.format(fmt), use_container_width=True)
    st.download_button("⬇️ Download CSV", df[disp_cols].to_csv(index=True),
                       f"{ticker}_engineered.csv", "text/csv")

st.divider()
st.caption(
    f"Data via Yahoo Finance · Exchange: {exch_lbl} · "
    "Forecasting by Prophet · Indian market holidays applied · Built with Streamlit"
)
