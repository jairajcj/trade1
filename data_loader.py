import pandas as pd
from datetime import datetime, timedelta
import threading

# Global cache to reduce latency
_cache = {
    'stock': {}, # {ticker: (data, timestamp)}
    'news': {}   # {keyword_tuple: (data, timestamp)}
}
_cache_lock = threading.Lock()
CACHE_EXPIRY_STOCK = timedelta(seconds=10)
CACHE_EXPIRY_NEWS = timedelta(hours=1)

def fetch_stock_data(ticker, period="2y", force=False):
    """Fetches historical stock data with caching, but ensures latest price is fresh."""
    global _cache
    now = datetime.now()
    
    # 1. Check if we have history in cache
    history = None
    with _cache_lock:
        if ticker in _cache['stock']:
            history, ts = _cache['stock'][ticker]
            # Refresh history only once an hour to keep it fast
            if now - ts > timedelta(hours=1):
                history = None

    if history is None:
        print(f"Fetching LONG history for {ticker}...")
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            with _cache_lock:
                _cache['stock'][ticker] = (history, now)
        except Exception as e:
            print(f"Error fetching history: {e}")
            return pd.DataFrame()

    # 2. If it's a force/live request, get the absolute latest price (1d, 1m) and patch it
    if force or (now - datetime.fromtimestamp(0) < timedelta(seconds=10)): # placeholder for "too old"
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            # Fetch just the last day's minutes to get the "live" price
            live_data = stock.history(period="1d", interval="1m")
            if not live_data.empty:
                latest_price = live_data['Close'].iloc[-1]
                # Patch the history with the latest price for the calculation
                history.iloc[-1, history.columns.get_loc('Close')] = latest_price
                print(f"Patched {ticker} with LIVE price: {latest_price}")
        except Exception as e:
            print(f"Live patch failed for {ticker}: {e}")

    return history

def fetch_ticker_news(ticker):
    """Fetches real-time news for a specific stock ticker."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news:
            return []
        # Return list of titles
        return [item['title'] for item in news if 'title' in item]
    except Exception as e:
        print(f"Error fetching ticker news for {ticker}: {e}")
        return []

def fetch_market_news(keywords=['India Economy', 'Stock Market India'], force=False):
    """Fetches news headlines with caching. Avoids 429 by strictly respecting cache."""
    global _cache
    now = datetime.now()
    key_tuple = tuple(sorted(keywords))
    
    with _cache_lock:
        if not force and key_tuple in _cache['news']:
            data, ts = _cache['news'][key_tuple]
            if now - ts < CACHE_EXPIRY_NEWS:
                return data

    # If force is True but we just fetched it recently, don't hit the API again to avoid 429
    with _cache_lock:
        if key_tuple in _cache['news']:
            data, ts = _cache['news'][key_tuple]
            if now - ts < timedelta(minutes=5): # Minimum 5 mins between news hits
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
