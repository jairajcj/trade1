"""
TradeIntel Pro - News & Sentiment Engine
Fetches news and analyzes sentiment for stocks, commodities, and markets.
"""

import streamlit as st
from textblob import TextBlob
import numpy as np


# ═══════════════════════════════════════════════════════════════
# NEWS FETCHING
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def fetch_ticker_news(ticker):
    """Fetch news for a specific ticker using yfinance with smarter commodity fallback."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news = stock.news
        
        # Smart Fallback for commodities (Gold/Silver/MCX)
        is_commodity = any(x in ticker.upper() for x in ["GC=F", "GOLD", "IAU", "SI=F", "SILVER"])
        if (not news or len(news) < 3) and is_commodity:
            return fetch_market_news("commodities")

        if not news:
            return []

        articles = []
        for item in news:
            # Handle different yfinance response formats
            content = item.get('content', item)
            title = content.get('title', '')
            summary = content.get('summary', title)
            source = content.get('publisher', content.get('provider', {}))
            if isinstance(source, dict):
                source = source.get('displayName', 'Market News')
            
            if title:
                sentiment = TextBlob(title).sentiment.polarity
                articles.append({
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "date": content.get('pubDate', ''),
                    "sentiment": round(sentiment, 3),
                    "sentiment_label": "Positive" if sentiment > 0.1 else ("Negative" if sentiment < -0.1 else "Neutral"),
                })

        return articles
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_market_news(market_type="us"):
    """Fetch general market news using GoogleNews or fallback."""
    keywords_map = {
        "indian": ["India Stock Market", "Sensex Nifty", "Indian Economy"],
        "us": ["US Stock Market", "Wall Street", "Robinhood Stocks", "S&P 500"],
        "commodities": ["Gold Price", "Silver Price", "Crude Oil", "Commodity Market"],
    }

    keywords = keywords_map.get(market_type, keywords_map["us"])

    try:
        from GoogleNews import GoogleNews
        googlenews = GoogleNews(period='3d')
        all_articles = []

        for key in keywords:
            googlenews.search(key)
            results = googlenews.result()
            if results:
                for res in results[:5]:
                    title = res.get('title', '')
                    if title:
                        sentiment = TextBlob(title).sentiment.polarity
                        all_articles.append({
                            "title": title,
                            "summary": res.get('desc', title),
                            "source": res.get('media', 'Google News'),
                            "date": res.get('date', ''),
                            "sentiment": round(sentiment, 3),
                            "sentiment_label": "Positive" if sentiment > 0.1 else ("Negative" if sentiment < -0.1 else "Neutral"),
                        })
            googlenews.clear()

        # Deduplicate by title
        seen = set()
        unique = []
        for a in all_articles:
            if a['title'] not in seen:
                seen.add(a['title'])
                unique.append(a)

        return unique
    except Exception as e:
        print(f"Error fetching market news: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# SENTIMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════
def compute_sentiment_score(articles):
    """Compute aggregate sentiment from articles."""
    if not articles:
        return 0.0, "Neutral", {"positive": 0, "negative": 0, "neutral": 0}

    sentiments = [a['sentiment'] for a in articles]
    avg = np.mean(sentiments)

    positive = sum(1 for s in sentiments if s > 0.1)
    negative = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - positive - negative

    if avg > 0.15:
        label = "Bullish"
    elif avg > 0.05:
        label = "Slightly Bullish"
    elif avg < -0.15:
        label = "Bearish"
    elif avg < -0.05:
        label = "Slightly Bearish"
    else:
        label = "Neutral"

    return round(avg, 4), label, {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
    }
