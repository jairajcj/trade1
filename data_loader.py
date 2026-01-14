import pandas as pd
from datetime import datetime, timedelta
import threading

# Global cache to reduce latency
_cache = {
    'stock': {}, # {ticker: (data, timestamp)}
    'news': {}   # {keyword_tuple: (data, timestamp)}
}
_cache_lock = threading.Lock()
CACHE_EXPIRY_STOCK = timedelta(minutes=15)
CACHE_EXPIRY_NEWS = timedelta(hours=1)

def fetch_stock_data(ticker, period="2y"):
    """Fetches historical stock data with caching."""
    global _cache
    now = datetime.now()
    
    with _cache_lock:
        if ticker in _cache['stock']:
            data, ts = _cache['stock'][ticker]
            if now - ts < CACHE_EXPIRY_STOCK:
                return data

    print(f"Fetching live data for {ticker}...")
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if not data.empty:
            with _cache_lock:
                _cache['stock'][ticker] = (data, now)
        return data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()

def fetch_market_news(keywords=['India Economy', 'Stock Market India']):
    """Fetches news headlines with caching."""
    global _cache
    now = datetime.now()
    key_tuple = tuple(sorted(keywords))
    
    with _cache_lock:
        if key_tuple in _cache['news']:
            data, ts = _cache['news'][key_tuple]
            if now - ts < CACHE_EXPIRY_NEWS:
                return data

    print(f"Fetching news for {keywords}...")
    try:
        from GoogleNews import GoogleNews
        googlenews = GoogleNews(period='7d')
        all_news = []
        for key in keywords:
            googlenews.search(key)
            results = googlenews.result()
            if results:
                for res in results:
                    all_news.append(res['title'])
            googlenews.clear()
        
        unique_news = list(set(all_news))
        with _cache_lock:
            _cache['news'][key_tuple] = (unique_news, now)
        return unique_news
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []
