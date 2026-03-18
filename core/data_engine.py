"""
TradeIntel Pro - Data Engine
Unified data fetching for Indian, US, and Commodity markets.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import threading
import streamlit as st

# ═══════════════════════════════════════════════════════════════
# CACHING LAYER
# ═══════════════════════════════════════════════════════════════
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = timedelta(minutes=5)


def _get_cached(key):
    with _cache_lock:
        if key in _cache:
            data, ts = _cache[key]
            if datetime.now() - ts < CACHE_TTL:
                return data
    return None


def _set_cached(key, data):
    with _cache_lock:
        _cache[key] = (data, datetime.now())


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker, period="1y"):
    """Fetch historical OHLCV data for any ticker."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None)
        df = df.reset_index()
        return df
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_price(ticker):
    """Get the latest price info for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None

        # Drop rows with NaN Close
        hist = hist.dropna(subset=['Close'])
        if hist.empty:
            return None

        current = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev != 0 else 0

        def safe_float(series, col, idx=-1):
            try:
                v = float(series[col].iloc[idx])
                return round(v, 2) if not np.isnan(v) else round(current, 2)
            except Exception:
                return round(current, 2)

        return {
            "price": round(current, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns and not np.isnan(hist['Volume'].iloc[-1]) else 0,
            "high": safe_float(hist, 'High'),
            "low": safe_float(hist, 'Low'),
            "open": safe_float(hist, 'Open'),
        }
    except Exception as e:
        print(f"Error fetching live price for {ticker}: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_performance(ticker):
    """Calculate performance over multiple timeframes."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 5:
            return {}

        current = float(hist['Close'].iloc[-1])
        perf = {}

        timeframes = {
            "1W": 5,
            "1M": 21,
            "3M": 63,
            "6M": 126,
            "YTD": None,
            "1Y": 252,
        }

        for label, days in timeframes.items():
            try:
                if label == "YTD":
                    year_start = hist[hist.index >= f"{datetime.now().year}-01-01"]
                    if not year_start.empty:
                        ref = float(year_start['Close'].iloc[0])
                        perf[label] = round(((current / ref) - 1) * 100, 2)
                elif days and len(hist) > days:
                    ref = float(hist['Close'].iloc[-days])
                    perf[label] = round(((current / ref) - 1) * 100, 2)
            except Exception:
                pass

        return perf
    except Exception as e:
        print(f"Error fetching performance for {ticker}: {e}")
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_indices_data(indices_dict):
    """Fetch live data for market indices."""
    results = {}
    for ticker, name in indices_dict.items():
        try:
            data = fetch_live_price(ticker)
            if data:
                results[name] = data
        except Exception:
            pass
    return results


@st.cache_data(ttl=60, show_spinner=False)
def fetch_stock_info(ticker):
    """Get company info and metadata."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "dividend_yield": info.get("dividendYield", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "avg_volume": info.get("averageVolume", 0),
            "description": info.get("longBusinessSummary", ""),
        }
    except Exception:
        return {"name": ticker, "sector": "N/A", "industry": "N/A"}


# ═══════════════════════════════════════════════════════════════
# GOLD/SILVER PRICE CONVERTER (USD/oz → INR & AED per 10g)
# ═══════════════════════════════════════════════════════════════
TROY_OZ_TO_GRAMS = 31.1035
INDIA_IMPORT_DUTY = 0.06     # 6%
INDIA_AIDC = 0.05            # 5%
INDIA_GST = 0.03             # 3%
RETAIL_MARGIN = 0.015        # 1.5%
BASIS_ADJUSTMENT = 0.925     # Calibrated to Landed

@st.cache_data(ttl=300, show_spinner=False)
def get_commodity_in_local_currencies(commodity_ticker="GC=F", is_dubai=False):
    """
    Returns gold rates. 
    If is_dubai=True: Returns pure Dubai market rates (no India Duty/GST).
    If is_dubai=False: Returns India MCX/Retail rates.
    """
    try:
        stock = yf.Ticker(commodity_ticker)
        hist = stock.history(period="5d").dropna(subset=["Close"])
        if hist.empty: return None
        usd_per_oz = float(hist["Close"].iloc[-1])

        usdinr = yf.Ticker("USDINR=X").history(period="5d").dropna(subset=["Close"])
        usdaed = yf.Ticker("USDAED=X").history(period="5d").dropna(subset=["Close"])
        inr_rate = float(usdinr["Close"].iloc[-1]) if not usdinr.empty else 83.5
        aed_rate = float(usdaed["Close"].iloc[-1]) if not usdaed.empty else 3.67

        # Base Conversion
        usd_per_10g = (usd_per_oz / TROY_OZ_TO_GRAMS) * 10 * BASIS_ADJUSTMENT
        
        if is_dubai:
            # DUBAI RATE: Base + 5% VAT (No India Duty/Cess)
            aed_gold = (usd_per_10g * aed_rate) * 1.05
            inr_equivalent = aed_gold * (inr_rate / aed_rate)
            return {
                "usd_per_oz": round(usd_per_oz, 2),
                "aed_24k": round(aed_gold, 0),
                "inr_equivalent": round(inr_equivalent, 0),
                "aed_22k": round(aed_gold * 0.916, 0),
            }
        else:
            # INDIA RATE: Includes Import Duty + AIDC + GST
            inr_landed = usd_per_10g * inr_rate * (1 + INDIA_IMPORT_DUTY + INDIA_AIDC) * (1 + INDIA_GST)
            inr_24k = inr_landed * (1 + RETAIL_MARGIN)
            inr_22k = inr_24k * 0.916
            return {
                "usd_per_oz": round(usd_per_oz, 2),
                "mcx_landed": round(inr_landed, 0),
                "retail_24k": round(inr_24k, 0),
                "retail_22k": round(inr_22k, 0)
            }
    except Exception as e:
        print(f"Conversion error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# DYNAMIC TICKER SEARCH (like TradingView)
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def search_tickers(query, max_results=20):
    """
    Search Yahoo Finance for matching tickers.
    Returns list of dicts: {symbol, name, type, exchange}
    """
    import requests
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "quotesCount": max_results,
            "newsCount": 0,
            "listsCount": 0,
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()

        results = []
        for q in data.get("quotes", []):
            results.append({
                "symbol": q.get("symbol", ""),
                "name": q.get("shortname") or q.get("longname") or q.get("symbol", ""),
                "type": q.get("quoteType", "").capitalize(),
                "exchange": q.get("exchange", ""),
            })
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []
