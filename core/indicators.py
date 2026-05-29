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
        # Large-cap private banks
        "HDFCBANK":   "HDFC Bank",
        "ICICIBANK":  "ICICI Bank",
        "KOTAKBANK":  "Kotak Mahindra Bank",
        "AXISBANK":   "Axis Bank",
        "INDUSINDBK": "IndusInd Bank",
        # PSU banks
        "SBIN":       "State Bank of India",
        "PNB":        "Punjab National Bank",
        "BANKBARODA": "Bank of Baroda",
        "CANBK":      "Canara Bank",
        "UNIONBANK":  "Union Bank of India",
        "MAHABANK":   "Bank of Maharashtra",
        # NBFCs
        "BAJFINANCE": "Bajaj Finance",
        "BAJAJFINSV": "Bajaj Finserv",
        "CHOLAFIN":   "Cholamandalam Finance",
        "MUTHOOTFIN": "Muthoot Finance",
        "M&MFIN":     "M&M Financial Services",
        # Small finance & others
        "BANDHANBNK": "Bandhan Bank",
        "FEDERALBNK": "Federal Bank",
        "IDFCFIRSTB": "IDFC First Bank",
        "AUBANK":     "AU Small Finance Bank",
        "RBLBANK":    "RBL Bank",
        "YESBANK":    "Yes Bank",
    },
    "💻 Information Technology": {
        # Large-cap
        "TCS":        "Tata Consultancy Services",
        "INFY":       "Infosys",
        "WIPRO":      "Wipro",
        "HCLTECH":    "HCL Technologies",
        "TECHM":      "Tech Mahindra",
        # Mid-cap
        "LTIM":       "LTIMindtree",
        "MPHASIS":    "Mphasis",
        "PERSISTENT": "Persistent Systems",
        "COFORGE":    "Coforge",
        "KPITTECH":   "KPIT Technologies",
        "OFSS":       "Oracle Financial Services",
        "TATAELXSI":  "Tata Elxsi",
        "BSOFT":      "Birlasoft",
        "CYIENT":     "Cyient",
        "ZENSAR":     "Zensar Technologies",
        "MASTEK":     "Mastek",
        "TANLA":      "Tanla Platforms",
    },
    "💊 Pharma & Healthcare": {
        # Large-cap
        "SUNPHARMA":   "Sun Pharmaceutical",
        "DRREDDY":     "Dr. Reddy's Laboratories",
        "CIPLA":       "Cipla",
        "DIVISLAB":    "Divi's Laboratories",
        "AUROPHARMA":  "Aurobindo Pharma",
        "LUPIN":       "Lupin",
        "APOLLOHOSP":  "Apollo Hospitals",
        # Mid-cap
        "MANKIND":     "Mankind Pharma",
        "TORNTPHARM":  "Torrent Pharmaceuticals",
        "ALKEM":       "Alkem Laboratories",
        "BIOCON":      "Biocon",
        "NATCO":       "Natco Pharma",
        "ABBOTTINDIA": "Abbott India",
        "GLAXO":       "GSK Pharmaceuticals",
        "PFIZER":      "Pfizer India",
    },
    "🚗 Automobile": {
        # 4-wheelers
        "MARUTI":     "Maruti Suzuki",
        "TATAMOTORS": "Tata Motors",
        "M&M":        "Mahindra & Mahindra",
        "EICHERMOT":  "Eicher Motors",
        "ESCORTS":    "Escorts Kubota",
        # 2-wheelers
        "BAJAJ-AUTO": "Bajaj Auto",
        "HEROMOTOCO": "Hero MotoCorp",
        "TVSMOTOR":   "TVS Motor Company",
        # Ancillaries & tyres
        "BHARATFORG": "Bharat Forge",
        "MOTHERSON":  "Samvardhana Motherson",
        "APOLLOTYRE": "Apollo Tyres",
        "MRF":        "MRF Limited",
        "CEATLTD":    "CEAT Tyres",
        "BALKRISIND": "Balkrishna Industries",
        "ASHOKLEY":   "Ashok Leyland",
    },
    "⚡ Energy & Power": {
        # Oil & Gas
        "RELIANCE":   "Reliance Industries",
        "ONGC":       "ONGC",
        "IOC":        "Indian Oil Corporation",
        "BPCL":       "Bharat Petroleum",
        "HPCL":       "Hindustan Petroleum",
        "GAIL":       "GAIL India",
        "PETRONET":   "Petronet LNG",
        "CHENNPETRO": "Chennai Petroleum Corporation",
        # Power & Renewables
        "POWERGRID":  "Power Grid Corp",
        "NTPC":       "NTPC",
        "COALINDIA":  "Coal India",
        "TATAPOWER":  "Tata Power Company",
        "ADANIGREEN": "Adani Green Energy",
        "TORNTPOWER": "Torrent Power",
        "NHPC":       "NHPC Limited",
        "SJVN":       "SJVN Limited",
    },
    "🏗️ Infrastructure & Metals": {
        # Metals & Mining
        "TATASTEEL":  "Tata Steel",
        "JSWSTEEL":   "JSW Steel",
        "HINDALCO":   "Hindalco Industries",
        "SAIL":       "Steel Authority of India",
        "NMDC":       "NMDC Limited",
        "VEDL":       "Vedanta",
        "HINDZINC":   "Hindustan Zinc",
        # Cement
        "ULTRACEMCO": "UltraTech Cement",
        "GRASIM":     "Grasim Industries",
        "ACC":        "ACC Cement",
        "AMBUJACEM":  "Ambuja Cements",
        "SHREECEM":   "Shree Cement",
        "DALBHARAT":  "Dalmia Bharat Cement",
        # Construction
        "LT":         "Larsen & Toubro",
        "NCC":        "NCC Limited",
        "IRCON":      "IRCON International",
        "JSWINFRA":   "JSW Infrastructure",
        "MAZDOCK":    "Mazagon Dock Shipbuilders",
    },
    "🛒 FMCG & Consumer": {
        "HINDUNILVR": "Hindustan Unilever",
        "ITC":        "ITC Limited",
        "NESTLEIND":  "Nestle India",
        "BRITANNIA":  "Britannia Industries",
        "DABUR":      "Dabur India",
        "MARICO":     "Marico",
        "GODREJCP":   "Godrej Consumer Products",
        "COLPAL":     "Colgate-Palmolive India",
        "EMAMILTD":   "Emami Limited",
        "TATACONSUM": "Tata Consumer Products",
        "VBL":        "Varun Beverages",
        "RADICO":     "Radico Khaitan",
        "UNITDSPR":   "United Spirits",
        "PATANJALI":  "Patanjali Foods",
    },
    "📡 Telecom & Media": {
        "BHARTIARTL": "Bharti Airtel",
        "IDEA":       "Vodafone Idea",
        "TATACOMM":   "Tata Communications",
        "RAILTEL":    "RailTel Corporation",
        "HFCL":       "HFCL Limited",
        "ZEEL":       "Zee Entertainment",
        "SUNTV":      "Sun TV Network",
        "PVRINOX":    "PVR INOX",
        "DEN":        "DEN Networks",
    },
    "🏠 Real Estate": {
        "DLF":        "DLF Limited",
        "GODREJPROP": "Godrej Properties",
        "PRESTIGE":   "Prestige Estates",
        "PHOENIXLTD": "Phoenix Mills",
        "OBEROIRLTY": "Oberoi Realty",
        "BRIGADE":    "Brigade Enterprises",
        "LODHA":      "Macrotech Developers (Lodha)",
        "SOBHA":      "Sobha Limited",
        "SUNTECK":    "Sunteck Realty",
        "KOLTEPATIL": "Kolte-Patil Developers",
    },
    "🛡️ Insurance & Wealth": {
        "SBILIFE":    "SBI Life Insurance",
        "HDFCLIFE":   "HDFC Life Insurance",
        "ICICIGI":    "ICICI Lombard General Insurance",
        "ICICIPRULI": "ICICI Prudential Life Insurance",
        "STARHEALTH": "Star Health Insurance",
        "HDFCAMC":    "HDFC AMC",
        "ANGELONE":   "Angel One",
        "MOTILALOFS": "Motilal Oswal Financial Services",
        "NUVAMA":     "Nuvama Wealth Management",
    },
    "✈️ Aviation & Travel": {
        "INDIGO":     "IndiGo (InterGlobe Aviation)",
        "IRCTC":      "IRCTC",
        "INDHOTEL":   "Indian Hotels (Taj)",
        "MHRIL":      "Mahindra Holidays",
        "LEMONTREE":  "Lemon Tree Hotels",
        "THOMASCOOK": "Thomas Cook India",
        "EASEMYTRIP": "EaseMyTrip",
    },
    "🎨 Paints & Chemicals": {
        # Paints
        "ASIANPAINT":   "Asian Paints",
        "BERGERPAINTS": "Berger Paints India",
        "KANSAINER":    "Kansai Nerolac Paints",
        # Specialty Chemicals
        "PIDILITIND":   "Pidilite Industries",
        "DEEPAKNTR":    "Deepak Nitrite",
        "SRF":          "SRF Limited",
        "AARTIIND":     "Aarti Industries",
        "TATACHEM":     "Tata Chemicals",
        "UPL":          "UPL Limited",
        "GNFC":         "Gujarat Narmada Fertilizers",
        "COROMANDEL":   "Coromandel International",
        "LXCHEM":       "Laxmi Organic Industries",
    },
    "🛡️ Defence & PSU": {
        "HAL":        "Hindustan Aeronautics",
        "BEL":        "Bharat Electronics",
        "BHEL":       "Bharat Heavy Electricals",
        "BEML":       "BEML Limited",
        "COCHINSHIP": "Cochin Shipyard",
        "GRSE":       "Garden Reach Shipbuilders",
        "MIDHANI":    "Mishra Dhatu Nigam",
        "MTAR":       "MTAR Technologies",
        "RVNL":       "Rail Vikas Nigam",
        "IRFC":       "Indian Railway Finance Corp",
        "ADANIPORTS": "Adani Ports & SEZ",
    },
    "💎 Luxury & Retail": {
        "TITAN":      "Titan Company",
        "TRENT":      "Trent Limited",
        "DMART":      "Avenue Supermarts (D-Mart)",
        "NYKAA":      "FSN E-Commerce (Nykaa)",
        "ZOMATO":     "Zomato",
        "POLICYBZR":  "PB Fintech (PolicyBazaar)",
        "PAYTM":      "One 97 Communications (Paytm)",
        "CARTRADE":   "CarTrade Tech",
        "VEDANT":     "Vedant Fashions (Manyavar)",
        "KAYNES":     "Kaynes Technology",
    },
}

# Nifty 50 — used by Dashboard "Nifty 50" picker and Market Home overview
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

# Extended 100-stock universe used by Market Home for broader coverage
MARKET_UNIVERSE: list[str] = NIFTY50 + [
    # Banking extras
    "BANKBARODA", "CANBK", "PNB", "FEDERALBNK", "IDFCFIRSTB", "AUBANK",
    # IT extras
    "PERSISTENT", "COFORGE", "MPHASIS", "KPITTECH", "TATAELXSI",
    # Pharma extras
    "MANKIND", "TORNTPHARM", "ALKEM", "BIOCON",
    # Auto extras
    "TVSMOTOR", "ASHOKLEY", "APOLLOTYRE", "MRF", "BALKRISIND",
    # Energy extras
    "HPCL", "GAIL", "TATAPOWER", "TORNTPOWER",
    # Infra extras
    "SAIL", "NMDC", "VEDL", "AMBUJACEM", "NCC",
    # FMCG extras
    "GODREJCP", "COLPAL", "TATACONSUM", "VBL",
    # New sectors
    "DLF", "GODREJPROP", "OBEROIRLTY",
    "HAL", "BEL", "RVNL", "IRFC",
    "IRCTC", "INDHOTEL",
    "ZOMATO", "NYKAA", "DMART", "TRENT",
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
