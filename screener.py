from data_loader import fetch_stock_data, fetch_market_news
from feature_engineering import add_technical_indicators, analyze_sentiment
from model import calculate_signal
import concurrent.futures
from datetime import datetime, time
import pytz

# Constants for Intelligence
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

TOP_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS"
]

def is_market_open():
    """Checks if Indian market is currently open."""
    now_ist = datetime.now(IST)
    if now_ist.weekday() >= 5: # Weekend
        return False, "Closed (Weekend)"
    
    current_time = now_ist.time()
    if MARKET_OPEN <= current_time <= MARKET_CLOSE:
        return True, "Open"
    elif current_time < MARKET_OPEN:
        return False, "Closed (Opens at 9:15 AM)"
    else:
        return False, "Closed (Opens Tomorrow 9:15 AM)"

def analyze_single_stock(ticker, market_news=[]):
    """Deep analysis for Dashboard."""
    try:
        df = fetch_stock_data(ticker)
        if df.empty: return None
        
        df_tech = add_technical_indicators(df)
        if df_tech.empty: return None
        
        # Use provided market news to speed up scan
        sentiment = analyze_sentiment(market_news)
        
        prob, signal = calculate_signal(df_tech, sentiment)
        
        # Superposition Logic: Correlation Factor
        rel_volume = float(df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1])
        superposition_score = (prob * 0.6) + (max(0, sentiment) * 0.2) + (min(1, max(0, rel_volume - 1)) * 0.2)

        return {
            "ticker": ticker,
            "signal": signal,
            "probability": round(float(prob), 4),
            "superposition": round(float(superposition_score), 4),
            "price": round(float(df['Close'].iloc[-1]), 2),
            "trend_past_7d": round(float(((df['Close'].iloc[-1] / df['Close'].iloc[-7]) - 1) * 100), 2),
            "news_sample": market_news[:3] if market_news else ["No major headlines"]
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def get_super_intelligence():
    """Returns top 5 stocks with maximum margin profile."""
    status, status_text = is_market_open()
    
    # Optimization: Fetch news once for the whole scan
    global_news = fetch_market_news(keywords=['Indian Stock Market', 'Indian Economy', 'Geopolitics'])
    
    picks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_stock = {executor.submit(analyze_single_stock, s, global_news): s for s in TOP_STOCKS}
        for future in concurrent.futures.as_completed(future_to_stock):
            res = future.result()
            if res:
                picks.append(res)
    
    # Sort by Superposition Score descending
    picks.sort(key=lambda x: x['superposition'], reverse=True)
    
    return {
        "market_status": status_text,
        "is_open": status,
        "top_5": picks[:5],
        "timestamp": datetime.now(IST).isoformat()
    }
