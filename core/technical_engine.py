"""
TradeIntel Pro - Technical Analysis Engine
Computes 15+ technical indicators and generates TradingView-style ratings.
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochRSIIndicator, WilliamsRIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator


# ═══════════════════════════════════════════════════════════════
# COMPUTE ALL INDICATORS
# ═══════════════════════════════════════════════════════════════
def compute_all_indicators(df):
    """Compute comprehensive technical indicators on OHLCV data."""
    if df.empty or len(df) < 50:
        return df

    df = df.copy()
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # ── Momentum ──
    rsi_ind = RSIIndicator(close=close, window=14)
    df['RSI'] = rsi_ind.rsi()

    stoch = StochRSIIndicator(close=close, window=14, smooth1=3, smooth2=3)
    df['Stoch_K'] = stoch.stochrsi_k() * 100
    df['Stoch_D'] = stoch.stochrsi_d() * 100

    williams = WilliamsRIndicator(high=high, low=low, close=close, lbp=14)
    df['Williams_R'] = williams.williams_r()

    # ── Trend ──
    macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()

    adx = ADXIndicator(high=high, low=low, close=close, window=14)
    df['ADX'] = adx.adx()
    df['ADX_Pos'] = adx.adx_pos()
    df['ADX_Neg'] = adx.adx_neg()

    cci = CCIIndicator(high=high, low=low, close=close, window=20)
    df['CCI'] = cci.cci()

    # ── Moving Averages ──
    df['EMA_12'] = EMAIndicator(close=close, window=12).ema_indicator()
    df['EMA_26'] = EMAIndicator(close=close, window=26).ema_indicator()
    df['SMA_10'] = SMAIndicator(close=close, window=10).sma_indicator()
    df['SMA_20'] = SMAIndicator(close=close, window=20).sma_indicator()
    df['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
    df['SMA_100'] = SMAIndicator(close=close, window=100).sma_indicator()
    df['SMA_200'] = SMAIndicator(close=close, window=200).sma_indicator()

    # ── Volatility ──
    bb = BollingerBands(close=close, window=20, window_dev=2)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Lower'] = bb.bollinger_lband()

    atr = AverageTrueRange(high=high, low=low, close=close, window=14)
    df['ATR'] = atr.average_true_range()

    # ── Volume ──
    obv = OnBalanceVolumeIndicator(close=close, volume=volume)
    df['OBV'] = obv.on_balance_volume()

    try:
        mfi = MFIIndicator(high=high, low=low, close=close, volume=volume, window=14)
        df['MFI'] = mfi.money_flow_index()
    except Exception:
        df['MFI'] = 50.0

    # ── Target (for ML) ──
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    return df


# ═══════════════════════════════════════════════════════════════
# OSCILLATOR SUMMARY (TradingView Style)
# ═══════════════════════════════════════════════════════════════
def get_oscillator_summary(df):
    """
    Returns oscillator buy/neutral/sell counts like TradingView.
    Returns: (buy_count, neutral_count, sell_count, details)
    """
    if df.empty:
        return 0, 0, 0, []

    latest = df.iloc[-1]
    buy, neutral, sell = 0, 0, 0
    details = []

    # RSI (14)
    if 'RSI' in latest and not pd.isna(latest['RSI']):
        rsi = latest['RSI']
        if rsi < 30:
            buy += 1
            details.append(("RSI (14)", round(rsi, 2), "Buy"))
        elif rsi > 70:
            sell += 1
            details.append(("RSI (14)", round(rsi, 2), "Sell"))
        else:
            neutral += 1
            details.append(("RSI (14)", round(rsi, 2), "Neutral"))

    # Stochastic %K
    if 'Stoch_K' in latest and not pd.isna(latest['Stoch_K']):
        stk = latest['Stoch_K']
        if stk < 20:
            buy += 1
            details.append(("Stoch %K", round(stk, 2), "Buy"))
        elif stk > 80:
            sell += 1
            details.append(("Stoch %K", round(stk, 2), "Sell"))
        else:
            neutral += 1
            details.append(("Stoch %K", round(stk, 2), "Neutral"))

    # CCI (20)
    if 'CCI' in latest and not pd.isna(latest['CCI']):
        cci = latest['CCI']
        if cci < -100:
            buy += 1
            details.append(("CCI (20)", round(cci, 2), "Buy"))
        elif cci > 100:
            sell += 1
            details.append(("CCI (20)", round(cci, 2), "Sell"))
        else:
            neutral += 1
            details.append(("CCI (20)", round(cci, 2), "Neutral"))

    # ADX (14)
    if 'ADX' in latest and 'ADX_Pos' in latest and 'ADX_Neg' in latest:
        if not pd.isna(latest['ADX']):
            adx = latest['ADX']
            if latest['ADX_Pos'] > latest['ADX_Neg']:
                buy += 1
                details.append(("ADX (14)", round(adx, 2), "Buy"))
            elif latest['ADX_Neg'] > latest['ADX_Pos']:
                sell += 1
                details.append(("ADX (14)", round(adx, 2), "Sell"))
            else:
                neutral += 1
                details.append(("ADX (14)", round(adx, 2), "Neutral"))

    # Williams %R
    if 'Williams_R' in latest and not pd.isna(latest['Williams_R']):
        wr = latest['Williams_R']
        if wr < -80:
            buy += 1
            details.append(("Williams %R", round(wr, 2), "Buy"))
        elif wr > -20:
            sell += 1
            details.append(("Williams %R", round(wr, 2), "Sell"))
        else:
            neutral += 1
            details.append(("Williams %R", round(wr, 2), "Neutral"))

    # MACD
    if 'MACD' in latest and 'MACD_Signal' in latest:
        if not pd.isna(latest['MACD']):
            if latest['MACD'] > latest['MACD_Signal']:
                buy += 1
                details.append(("MACD", round(latest['MACD'], 4), "Buy"))
            else:
                sell += 1
                details.append(("MACD", round(latest['MACD'], 4), "Sell"))

    # MFI
    if 'MFI' in latest and not pd.isna(latest['MFI']):
        mfi = latest['MFI']
        if mfi < 20:
            buy += 1
            details.append(("MFI", round(mfi, 2), "Buy"))
        elif mfi > 80:
            sell += 1
            details.append(("MFI", round(mfi, 2), "Sell"))
        else:
            neutral += 1
            details.append(("MFI", round(mfi, 2), "Neutral"))

    return buy, neutral, sell, details


# ═══════════════════════════════════════════════════════════════
# MOVING AVERAGES SUMMARY (TradingView Style)
# ═══════════════════════════════════════════════════════════════
def get_ma_summary(df):
    """
    Returns moving average buy/neutral/sell counts.
    Buy = price above MA, Sell = price below MA.
    Returns: (buy_count, neutral_count, sell_count, details)
    """
    if df.empty:
        return 0, 0, 0, []

    latest = df.iloc[-1]
    price = latest['Close']
    buy, neutral, sell = 0, 0, 0
    details = []

    ma_cols = {
        "EMA (12)": "EMA_12",
        "EMA (26)": "EMA_26",
        "SMA (10)": "SMA_10",
        "SMA (20)": "SMA_20",
        "SMA (50)": "SMA_50",
        "SMA (100)": "SMA_100",
        "SMA (200)": "SMA_200",
    }

    for label, col in ma_cols.items():
        if col in latest and not pd.isna(latest[col]):
            ma_val = latest[col]
            if price > ma_val * 1.001:  # Small buffer
                buy += 1
                details.append((label, round(ma_val, 2), "Buy"))
            elif price < ma_val * 0.999:
                sell += 1
                details.append((label, round(ma_val, 2), "Sell"))
            else:
                neutral += 1
                details.append((label, round(ma_val, 2), "Neutral"))

    return buy, neutral, sell, details


# ═══════════════════════════════════════════════════════════════
# OVERALL TECHNICAL RATING
# ═══════════════════════════════════════════════════════════════
def get_overall_rating(osc_summary, ma_summary):
    """
    Combines oscillator and MA summaries into an overall rating.
    Returns: (rating_text, score from -1 to 1)
    """
    osc_buy, osc_neutral, osc_sell, _ = osc_summary
    ma_buy, ma_neutral, ma_sell, _ = ma_summary

    total_buy = osc_buy + ma_buy
    total_sell = osc_sell + ma_sell
    total = total_buy + (osc_neutral + ma_neutral) + total_sell

    if total == 0:
        return "Neutral", 0.0

    # Score: positive = buy, negative = sell
    score = (total_buy - total_sell) / total

    if score > 0.5:
        return "Strong Buy", score
    elif score > 0.15:
        return "Buy", score
    elif score < -0.5:
        return "Strong Sell", score
    elif score < -0.15:
        return "Sell", score
    else:
        return "Neutral", score


def get_support_resistance(df, lookback=50):
    """Calculate support and resistance levels."""
    if df.empty or len(df) < lookback:
        return None, None, None, None

    recent = df.tail(lookback)
    current = float(df['Close'].iloc[-1])

    # Pivot points
    high = float(recent['High'].max())
    low = float(recent['Low'].min())
    close = current

    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    return round(s2, 2), round(s1, 2), round(r1, 2), round(r2, 2)
