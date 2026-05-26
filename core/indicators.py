"""
Shared stock universe constants and cached data pipeline.
Extracted from app.py so both the Dashboard and Watchlist pages can import
without duplicating the fetch/engineer logic.
"""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import streamlit as st
import ta
import yfinance as yf

# ── Stock Universe ────────────────────────────────────────────────────────────

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
        "RELIANCE":    "Reliance Industries",
        "ONGC":        "ONGC",
        "POWERGRID":   "Power Grid Corp",
        "NTPC":        "NTPC",
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

INDIAN_HOLIDAYS: list[str] = [
    "2024-01-26", "2024-03-25", "2024-03-29", "2024-04-14", "2024-04-17",
    "2024-04-21", "2024-05-23", "2024-06-17", "2024-07-17", "2024-08-15",
    "2024-10-02", "2024-10-13", "2024-11-01", "2024-11-15", "2024-12-25",
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
    "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15", "2025-08-27",
    "2025-10-02", "2025-10-20", "2025-10-21", "2025-11-05", "2025-12-25",
    "2026-01-26", "2026-03-20", "2026-04-03", "2026-04-14", "2026-04-15",
    "2026-04-17", "2026-05-01", "2026-08-15", "2026-10-02", "2026-10-28",
    "2026-12-25",
]


def make_india_holidays() -> pd.DataFrame:
    return pd.DataFrame({
        "ds":      pd.to_datetime(INDIAN_HOLIDAYS),
        "holiday": "India Market Holiday",
    })


# ── Data pipeline ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_and_engineer(
    ticker: str, period: str
) -> tuple[pd.DataFrame | None, dict]:
    stock = yf.Ticker(ticker)
    df    = stock.history(period=period)
    if df is None or df.empty:
        return None, {}

    try:
        info = stock.info
    except Exception:
        info = {}

    bb      = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
    macd    = ta.trend.MACD(df["Close"])

    df["SMA_20"]       = ta.trend.sma_indicator(df["Close"], window=20)
    df["SMA_50"]       = ta.trend.sma_indicator(df["Close"], window=50)
    df["EMA_20"]       = ta.trend.ema_indicator(df["Close"], window=20)
    df["BB_upper"]     = bb.bollinger_hband()
    df["BB_lower"]     = bb.bollinger_lband()
    df["BB_mid"]       = bb.bollinger_mavg()
    df["RSI"]          = ta.momentum.rsi(df["Close"], window=14)
    df["MACD"]         = macd.macd()
    df["MACD_signal"]  = macd.macd_signal()
    df["MACD_hist"]    = macd.macd_diff()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    df["Volatility"]   = df["Daily_Return"].rolling(20).std()

    df.dropna(subset=["SMA_20"], inplace=True)
    return df, info
