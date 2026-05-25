"""
StockSight India — Intelligent Indian Stock Market Forecasting Platform
NSE · BSE · Nifty 50 · Prophet ML · Streamlit
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from prophet import Prophet
import ta

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockSight India",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main { background-color: #0a0f1e; }

    .metric-card {
        background: linear-gradient(135deg, #111827, #1a2235);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        margin-bottom: 4px;
    }
    .metric-label {
        color: #64748b;
        font-size: 12px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #f1f5f9;
        font-size: 22px;
        font-weight: 700;
        font-family: monospace;
    }
    .metric-delta-pos { color: #22c55e; font-size: 13px; margin-top: 2px; }
    .metric-delta-neg { color: #ef4444; font-size: 13px; margin-top: 2px; }

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS — Indian Stock Universe
# ─────────────────────────────────────────────────────────────────────────────
SECTORS: dict[str, dict[str, str]] = {
    "🏦 Banking & Finance": {
        "HDFCBANK":   "HDFC Bank",
        "ICICIBANK":  "ICICI Bank",
        "KOTAKBANK":  "Kotak Mahindra Bank",
        "SBIN":       "State Bank of India",
        "AXISBANK":   "Axis Bank",
        "BAJFINANCE": "Bajaj Finance",
        "BAJAJFINSV": "Bajaj Finserv",
        "INDUSINDBK": "IndusInd Bank",
    },
    "💻 Information Technology": {
        "TCS":        "Tata Consultancy Services",
        "INFY":       "Infosys",
        "WIPRO":      "Wipro",
        "HCLTECH":    "HCL Technologies",
        "TECHM":      "Tech Mahindra",
        "LTIM":       "LTIMindtree",
        "LTM":        "LTM Limited",
        "MPHASIS":    "Mphasis",
        "PERSISTENT": "Persistent Systems",
    },
    "💊 Pharma & Healthcare": {
        "SUNPHARMA":  "Sun Pharmaceutical",
        "DRREDDY":    "Dr. Reddy's Laboratories",
        "CIPLA":      "Cipla",
        "DIVISLAB":   "Divi's Laboratories",
        "AUROPHARMA": "Aurobindo Pharma",
        "LUPIN":      "Lupin",
        "APOLLOHOSP": "Apollo Hospitals",
    },
    "🚗 Automobile": {
        "MARUTI":     "Maruti Suzuki",
        "TATAMOTORS": "Tata Motors",
        "M&M":        "Mahindra & Mahindra",
        "BAJAJ-AUTO": "Bajaj Auto",
        "HEROMOTOCO": "Hero MotoCorp",
        "EICHERMOT":  "Eicher Motors",
    },
    "⚡ Energy & Oil": {
        "RELIANCE":   "Reliance Industries",
        "ONGC":       "ONGC",
        "POWERGRID":  "Power Grid Corp",
        "NTPC":       "NTPC",
        "COALINDIA":   "Coal India",
        "IOC":         "Indian Oil Corporation",
        "CHENNPETRO":  "Chennai Petroleum Corporation",
    },
    "🏗️ Infrastructure & Metals": {
        "TATASTEEL":  "Tata Steel",
        "JSWSTEEL":   "JSW Steel",
        "HINDALCO":   "Hindalco Industries",
        "ULTRACEMCO": "UltraTech Cement",
        "GRASIM":     "Grasim Industries",
        "LT":         "Larsen & Toubro",
        "MAZDOCK":    "Mazagon Dock Shipbuilders",
    },
    "🛒 FMCG & Consumer": {
        "HINDUNILVR": "Hindustan Unilever",
        "ITC":        "ITC Limited",
        "NESTLEIND":  "Nestle India",
        "BRITANNIA":  "Britannia Industries",
        "DABUR":      "Dabur India",
        "MARICO":     "Marico",
    },
    "📡 Telecom & Media": {
        "BHARTIARTL": "Bharti Airtel",
        "IDEA":       "Vodafone Idea",
        "DEN":        "DEN Networks",
    },
}

NIFTY50: list[str] = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BHARTIARTL", "BPCL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK",
    "INFY", "ITC", "JSWSTEEL", "KOTAKBANK", "LT",
    "M&M", "MARUTI", "NESTLEIND", "NTPC", "ONGC",
    "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA",
    "TATAMOTORS", "TATASTEEL", "TCS", "TECHM", "TITAN",
    "TRENT", "ULTRACEMCO", "WIPRO", "LTIM", "ADANIGREEN",
]

# NSE/BSE market holidays 2024–2026
INDIAN_HOLIDAYS: list[str] = [
    # 2024
    "2024-01-26", "2024-03-25", "2024-03-29", "2024-04-14", "2024-04-17",
    "2024-04-21", "2024-05-23", "2024-06-17", "2024-07-17", "2024-08-15",
    "2024-10-02", "2024-10-13", "2024-11-01", "2024-11-15", "2024-12-25",
    # 2025
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
    "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15", "2025-08-27",
    "2025-10-02", "2025-10-20", "2025-10-21", "2025-11-05", "2025-12-25",
    # 2026
    "2026-01-26", "2026-03-20", "2026-04-03", "2026-04-14", "2026-04-15",
    "2026-04-17", "2026-05-01", "2026-08-15", "2026-10-02", "2026-10-28",
    "2026-12-25",
]


def make_india_holidays() -> pd.DataFrame:
    dates = pd.to_datetime(INDIAN_HOLIDAYS)
    return pd.DataFrame({"ds": dates, "holiday": "India Market Holiday"})


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 StockSight India")
    st.markdown("*NSE · BSE · Nifty 50*")
    st.divider()

    exchange = st.radio(
        "Exchange",
        ["NSE (.NS)", "BSE (.BO)"],
        horizontal=True,
    )
    suffix = ".NS" if exchange == "NSE (.NS)" else ".BO"

    st.markdown("#### Stock Selection")
    pick_by = st.radio(
        "Pick by",
        ["Sector", "Nifty 50", "Manual Ticker"],
        horizontal=True,
    )

    base_ticker: str
    if pick_by == "Sector":
        sector = st.selectbox("Sector", list(SECTORS.keys()))
        sector_stocks = SECTORS[sector]
        company_display = st.selectbox("Company", list(sector_stocks.values()))
        # reverse-lookup ticker from display name
        base_ticker = next(k for k, v in sector_stocks.items() if v == company_display)

    elif pick_by == "Nifty 50":
        base_ticker = st.selectbox("Nifty 50 Stock", sorted(NIFTY50))

    else:  # Manual Ticker
        base_ticker = st.text_input("Ticker Symbol", value="RELIANCE").upper().strip()

    ticker = base_ticker + suffix
    st.markdown(f"**Full ticker:** `{ticker}`")
    st.divider()

    period_label = st.selectbox(
        "Historical Range",
        ["3 Months", "6 Months", "1 Year", "2 Years", "5 Years"],
        index=2,
    )
    period_map = {
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year":   "1y",
        "2 Years":  "2y",
        "5 Years":  "5y",
    }
    period = period_map[period_label]

    forecast_days = st.slider(
        "Forecast Horizon (days)",
        min_value=7,
        max_value=90,
        value=30,
    )

    show_indicators: list[str] = st.multiselect(
        "Technical Indicators",
        ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "RSI", "MACD"],
        default=["SMA 20", "SMA 50"],
    )
    st.divider()

    run = st.button("🚀 Run Analysis", use_container_width=True, type="primary")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 📈 StockSight India")
st.markdown("*Real-time NSE & BSE data · Technical indicators · AI price forecasting*")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# LANDING STATE
# ─────────────────────────────────────────────────────────────────────────────
if not run:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 🌟 Popular Picks")
        st.markdown(
            """
- **RELIANCE** — Reliance Industries
- **TCS** — Tata Consultancy Services
- **HDFCBANK** — HDFC Bank
- **INFY** — Infosys
- **SBIN** — State Bank of India
- **BHARTIARTL** — Bharti Airtel
            """
        )
    with col_r:
        st.markdown("### 📊 Nifty 50 Snapshot")
        st.info(
            "📌 Configure your stock in the sidebar, then click **Run Analysis**."
        )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# DATA PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_and_engineer(
    ticker: str, period: str
) -> tuple[pd.DataFrame | None, dict]:
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df is None or df.empty:
        return None, {}

    try:
        info = stock.info
    except Exception:
        info = {}

    # ── Technical indicators ──────────────────────────────────────────────
    bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
    macd_obj = ta.trend.MACD(df["Close"])

    df["SMA_20"]      = ta.trend.sma_indicator(df["Close"], window=20)
    df["SMA_50"]      = ta.trend.sma_indicator(df["Close"], window=50)
    df["EMA_20"]      = ta.trend.ema_indicator(df["Close"], window=20)
    df["BB_upper"]    = bb.bollinger_hband()
    df["BB_lower"]    = bb.bollinger_lband()
    df["BB_mid"]      = bb.bollinger_mavg()
    df["RSI"]         = ta.momentum.rsi(df["Close"], window=14)
    df["MACD"]        = macd_obj.macd()
    df["MACD_signal"] = macd_obj.macd_signal()
    df["MACD_hist"]   = macd_obj.macd_diff()
    df["Daily_Return"]= df["Close"].pct_change() * 100
    df["Volatility"]  = df["Daily_Return"].rolling(20).std()

    df.dropna(subset=["SMA_20"], inplace=True)
    return df, info


with st.spinner(f"💡 Fetching {ticker} from {'NSE' if suffix == '.NS' else 'BSE'}…"):
    df, info = fetch_and_engineer(ticker, period)

if df is None or df.empty:
    st.error(
        f"❌ No data found for **{ticker}**. "
        "Try switching exchange (NSE ↔ BSE) or check the ticker symbol."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────────────────────────────────────
last  = df["Close"].iloc[-1]
prev  = df["Close"].iloc[-2]
chg   = last - prev
pct   = chg / prev * 100
high  = df["High"].max()
low   = df["Low"].min()
vol   = df["Volume"].iloc[-1]
rsi   = df["RSI"].iloc[-1]

company_name = info.get("longName", base_ticker)
exch_label   = "NSE" if suffix == ".NS" else "BSE"
badge_cls    = "nse-badge" if suffix == ".NS" else "bse-badge"

st.markdown(
    f"### 🏢 {company_name} "
    f'<span class="exchange-badge {badge_cls}">{exch_label}</span>',
    unsafe_allow_html=True,
)


def _delta_html(value: float) -> str:
    if value >= 0:
        return f'<div class="metric-delta-pos">▲ {value:+.2f}%</div>'
    return f'<div class="metric-delta-neg">▼ {value:.2f}%</div>'


def card(col, label: str, value: str, delta: float | None = None) -> None:
    delta_html = _delta_html(delta) if delta is not None else ""
    col.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _fmt_volume(v: float) -> str:
    if v < 1e7:
        return f"{v / 1e5:.2f}L"
    return f"{v / 1e7:.2f}Cr"


cols = st.columns(5)
card(cols[0], "Last Price",  f"₹{last:,.2f}",     delta=pct)
card(cols[1], "52W High",    f"₹{high:,.2f}")
card(cols[2], "52W Low",     f"₹{low:,.2f}")
card(cols[3], "Volume",      _fmt_volume(vol))
card(cols[4], "RSI (14)",    f"{rsi:.1f}")


# ─────────────────────────────────────────────────────────────────────────────
# CANDLESTICK + INDICATORS CHART
# ─────────────────────────────────────────────────────────────────────────────
has_rsi  = "RSI" in show_indicators
has_macd = "MACD" in show_indicators
rows     = 1 + int(has_rsi) + int(has_macd)
row_heights = [0.6] + [0.2] * (rows - 1)

specs = [[{"type": "xy"}]] * rows
fig = make_subplots(
    rows=rows,
    cols=1,
    shared_xaxes=True,
    row_heights=row_heights,
    vertical_spacing=0.04,
    specs=specs,
)

# ── Candlestick ───────────────────────────────────────────────────────────
fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing_line_color="#22c55e",
        decreasing_line_color="#ef4444",
        increasing_fillcolor="#22c55e",
        decreasing_fillcolor="#ef4444",
    ),
    row=1, col=1,
)

# ── Overlays ──────────────────────────────────────────────────────────────
indicator_config = {
    "SMA 20": {"col": "SMA_20", "color": "#60a5fa", "name": "SMA 20"},
    "SMA 50": {"col": "SMA_50", "color": "#f59e0b", "name": "SMA 50"},
    "EMA 20": {"col": "EMA_20", "color": "#a78bfa", "name": "EMA 20"},
}

for ind_key, cfg in indicator_config.items():
    if ind_key in show_indicators:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[cfg["col"]],
                name=cfg["name"],
                line=dict(color=cfg["color"], width=1.5),
                hovertemplate=f"{cfg['name']}: ₹%{{y:,.2f}}<extra></extra>",
            ),
            row=1, col=1,
        )

if "Bollinger Bands" in show_indicators:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_upper"],
            name="BB Upper",
            line=dict(color="#94a3b8", width=1, dash="dash"),
            hovertemplate="BB Upper: ₹%{y:,.2f}<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_lower"],
            name="BB Lower",
            line=dict(color="#94a3b8", width=1, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(148,163,184,0.07)",
            hovertemplate="BB Lower: ₹%{y:,.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

# ── RSI sub-plot ──────────────────────────────────────────────────────────
current_row = 2
if has_rsi:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI",
            line=dict(color="#e879f9", width=1.5),
            hovertemplate="RSI: %{y:.1f}<extra></extra>",
        ),
        row=current_row, col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=current_row, col=1)
    fig.update_yaxes(title_text="RSI", row=current_row, col=1)
    current_row += 1

# ── MACD sub-plot ─────────────────────────────────────────────────────────
if has_macd:
    macd_colors = [
        "#22c55e" if v >= 0 else "#ef4444" for v in df["MACD_hist"].fillna(0)
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["MACD_hist"],
            name="MACD Hist",
            marker_color=macd_colors,
            hovertemplate="Histogram: %{y:.4f}<extra></extra>",
        ),
        row=current_row, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD"],
            name="MACD",
            line=dict(color="#60a5fa", width=1.5),
            hovertemplate="MACD: %{y:.4f}<extra></extra>",
        ),
        row=current_row, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD_signal"],
            name="Signal",
            line=dict(color="#f59e0b", width=1.5),
            hovertemplate="Signal: %{y:.4f}<extra></extra>",
        ),
        row=current_row, col=1,
    )
    fig.update_yaxes(title_text="MACD", row=current_row, col=1)

fig.update_layout(
    height=600 if rows == 1 else 400 + rows * 150,
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis_tickprefix="₹",
)

st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PROPHET FORECASTING
# ─────────────────────────────────────────────────────────────────────────────
st.subheader(f"🔮 AI Forecast — Next {forecast_days} Trading Days")

with st.spinner("Training forecasting model with Indian market calendar…"):
    prophet_df = (
        df[["Close"]]
        .reset_index()[["Date", "Close"]]
        .copy()
    )
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)

    india_holidays = make_india_holidays()

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
        interval_width=0.8,
        holidays=india_holidays,
    )
    model.fit(prophet_df)

    future   = model.make_future_dataframe(periods=forecast_days, freq="B")
    forecast = model.predict(future)

cutoff      = prophet_df["ds"].max()
fcast_hist  = forecast[forecast["ds"] <= cutoff]
fcast_f     = forecast[forecast["ds"] >  cutoff]

fig2 = go.Figure()

# Actual prices
fig2.add_trace(
    go.Scatter(
        x=prophet_df["ds"],
        y=prophet_df["y"],
        name="Actual",
        line=dict(color="#60a5fa", width=2),
        hovertemplate="Actual: ₹%{y:,.2f}<extra></extra>",
    )
)

# Historical model fit
fig2.add_trace(
    go.Scatter(
        x=fcast_hist["ds"],
        y=fcast_hist["yhat"],
        name="Model Fit",
        line=dict(color="#94a3b8", width=1, dash="dash"),
        hovertemplate="Fit: ₹%{y:,.2f}<extra></extra>",
    )
)

# 80% confidence band (forward only)
band_x = (
    list(fcast_f["ds"]) + list(fcast_f["ds"])[::-1]
)
band_y = (
    list(fcast_f["yhat_upper"]) + list(fcast_f["yhat_lower"])[::-1]
)
fig2.add_trace(
    go.Scatter(
        x=band_x,
        y=band_y,
        name="80% CI",
        fill="toself",
        fillcolor="rgba(34,197,94,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
    )
)

# Forecast line
fig2.add_trace(
    go.Scatter(
        x=fcast_f["ds"],
        y=fcast_f["yhat"],
        name="Forecast",
        line=dict(color="#22c55e", width=2.5),
        hovertemplate="Forecast: ₹%{y:,.2f}<extra></extra>",
    )
)

fig2.update_layout(
    height=420,
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis_tickprefix="₹",
)

st.plotly_chart(fig2, use_container_width=True)

# Forecast summary cards
end_price  = fcast_f["yhat"].iloc[-1]
end_upper  = fcast_f["yhat_upper"].iloc[-1]
end_lower  = fcast_f["yhat_lower"].iloc[-1]
exp_change = (end_price - last) / last * 100

fcols = st.columns(3)
card(fcols[0], f"Forecast Price (+{forecast_days}d)", f"₹{end_price:,.2f}", delta=exp_change)
card(fcols[1], "Upper Bound (80%)",                   f"₹{end_upper:,.2f}")
card(fcols[2], "Lower Bound (80%)",                   f"₹{end_lower:,.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# RETURNS & VOLATILITY PANEL
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📉 Returns & Volatility")

ret_colors = [
    "#22c55e" if v >= 0 else "#ef4444"
    for v in df["Daily_Return"].fillna(0)
]

fig_ret = go.Figure(
    go.Bar(
        x=df.index,
        y=df["Daily_Return"],
        name="Daily Return",
        marker_color=ret_colors,
        hovertemplate="%{x|%b %d, %Y}: %{y:.2f}%<extra></extra>",
    )
)
fig_ret.update_layout(
    height=280,
    title="Daily Returns (%)",
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    margin=dict(l=0, r=0, t=40, b=0),
    showlegend=False,
)

fig_vol = go.Figure(
    go.Scatter(
        x=df.index,
        y=df["Volatility"],
        name="Volatility",
        fill="tozeroy",
        fillcolor="rgba(251,191,36,0.15)",
        line=dict(color="#fbbf24", width=2),
        hovertemplate="%{x|%b %d, %Y}: %{y:.2f}%<extra></extra>",
    )
)
fig_vol.update_layout(
    height=280,
    title="20-Day Rolling Volatility (%)",
    template="plotly_dark",
    paper_bgcolor="#0a0f1e",
    plot_bgcolor="#0a0f1e",
    margin=dict(l=0, r=0, t=40, b=0),
    showlegend=False,
)

col_ret, col_vol = st.columns(2)
with col_ret:
    st.plotly_chart(fig_ret, use_container_width=True)
with col_vol:
    st.plotly_chart(fig_vol, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# RAW DATA EXPANDER
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🗃️ Engineered Dataset"):
    display_cols = [
        "Open", "High", "Low", "Close", "Volume",
        "SMA_20", "SMA_50", "EMA_20", "RSI",
        "Daily_Return", "Volatility",
    ]
    price_cols   = {"Open", "High", "Low", "Close", "SMA_20", "SMA_50", "EMA_20"}

    fmt: dict[str, str] = {
        c: ("₹{:.2f}" if c in price_cols else "{:.2f}")
        for c in display_cols
        if c != "Volume"
    }

    display_df = df[display_cols].tail(100).copy()
    st.dataframe(
        display_df.style.format(fmt),
        use_container_width=True,
    )

    csv = df[display_cols].to_csv(index=True)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"{ticker}_engineered.csv",
        mime="text/csv",
    )


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Data via Yahoo Finance · Exchange: {'NSE' if suffix == '.NS' else 'BSE'} · "
    "Forecasting by Prophet · Indian market holidays applied · Built with Streamlit"
)
