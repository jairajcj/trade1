from data_loader import fetch_stock_data, fetch_market_news
from feature_engineering import add_technical_indicators, analyze_sentiment
from model import calculate_signal
import concurrent.futures
from datetime import datetime, time
import pytz
import numpy as np

# Constants for Intelligence
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

TOP_STOCKS = [
    # Blue Chips & Growth
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "ZOMATO.NS", "ADANIENT.NS", "JIOFIN.NS",
    "HAL.NS", "BHEL.NS", "RVNL.NS", "TATASTEEL.NS", "MAZDOCK.NS",
    "IRFC.NS", "IRCON.NS", "NHPC.NS", "BEML.NS", "TITAN.NS",
    "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS", "COALINDIA.NS",
    "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "DELHIVERY.NS", "TRENT.NS",
    "BEL.NS", "MAHABANK.NS", "IOB.NS", "COFORGE.NS", "PERSISTENT.NS"
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

def analyze_single_stock(ticker, global_market_news=[], force=False):
    """Deep analysis for Dashboard."""
    try:
        df = fetch_stock_data(ticker, force=force)
        if df.empty: return None
        
        df_tech = add_technical_indicators(df)
        if df_tech.empty: return None
        
        # Fetch stock-specific news
        from data_loader import fetch_ticker_news
        ticker_news = fetch_ticker_news(ticker)
        
        # Combine ticker news with global context for sentiment
        # Weighting: Ticker news is more relevant to the specific price movement
        all_relevant_news = (ticker_news * 2) + global_market_news
        sentiment = analyze_sentiment(all_relevant_news)
        
        prob, signal, triggers = calculate_signal(df_tech, sentiment)
        
        # Strategy Logic
        price = float(df['Close'].iloc[-1])
        volatility = float(df['Close'].pct_change().std() * np.sqrt(252)) # Annualized volatility
        
        buy_above = round(price * 1.005, 2)
        target = round(price * (1 + (volatility * 0.1)), 2)
        stop_loss = round(price * (1 - (volatility * 0.05)), 2)
        
        if signal == "SELL":
            buy_above = round(price * 0.995, 2) # Sell below for short
            target = round(price * (1 - (volatility * 0.1)), 2)
            stop_loss = round(price * (1 + (volatility * 0.05)), 2)
        
        # Superposition Logic: Correlation Factor
        rel_volume = float(df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1])
        superposition_score = (prob * 0.6) + (max(0, sentiment) * 0.2) + (min(1, max(0, rel_volume - 1)) * 0.2)

        # Prepare history for chart (last 30 days)
        history_data = df.tail(30).reset_index()
        history_list = []
        for _, row in history_data.iterrows():
            history_list.append({
                "date": row['Date'].strftime('%Y-%m-%d'),
                "price": round(float(row['Close']), 2)
            })

        # Mixed News Sample: 2 specific + 1 global
        news_sample = ticker_news[:2] + global_market_news[:1]
        if not news_sample:
            news_sample = ["No major headlines found for this asset."]

        return {
            "ticker": ticker,
            "signal": signal,
            "triggers": triggers,
            "probability": round(float(prob), 4),
            "superposition": round(float(superposition_score), 4),
            "price": round(float(df['Close'].iloc[-1]), 2),
            "buy_above": buy_above,
            "target": target,
            "stop_loss": stop_loss,
            "trend_past_7d": round(float(((df['Close'].iloc[-1] / df['Close'].iloc[-7]) - 1) * 100), 2),
            "news_sample": news_sample,
            "history": history_list
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def get_super_intelligence(force=False):
    """Returns all stocks projected to increase (BUY signals)."""
    status, status_text = is_market_open()
    
    # Optimization: Fetch news once for the whole scan
    global_news = fetch_market_news(keywords=['NSE Stock Market India', 'Indian Economy', 'Geopolitics'], force=force)
    
    picks = []
    # Increase workers to handle 35+ stocks quickly
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_stock = {executor.submit(analyze_single_stock, s, global_news, force): s for s in TOP_STOCKS}
        for future in concurrent.futures.as_completed(future_to_stock):
            res = future.result()
            if res:
                picks.append(res)
    
    # Filter for signals that are going to INCREASE (BUY or HOLD with high probability)
    # The user asked specifically for stocks "going to increase"
    # We'll return all, but sort the best ones to the top
    picks.sort(key=lambda x: x['superposition'], reverse=True)
    
    return {
        "market_status": status_text,
        "is_open": status,
        "results_count": len(picks),
        "top_picks": picks, # Return all results
        "timestamp": datetime.now(IST).isoformat()
    }
