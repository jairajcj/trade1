import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from textblob import TextBlob

def add_technical_indicators(df):
    """Adds RSI, MACD, and other indicators to the dataframe."""
    df = df.copy()
    if len(df) < 30:
        return df
    
    # RSI
    rsi = RSIIndicator(close=df['Close'], window=14)
    df['RSI'] = rsi.rsi()

    # MACD
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()

    # Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # Target: 1 if Price goes up next day, else 0
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    return df.dropna()

def analyze_sentiment(news_headlines):
    """Calculates average sentiment polarity from a list of headlines."""
    if not news_headlines:
        return 0.0
    
    polarities = [TextBlob(headline).sentiment.polarity for headline in news_headlines]
    return np.mean(polarities)
