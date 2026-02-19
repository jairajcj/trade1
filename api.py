from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from data_loader import fetch_stock_data, fetch_market_news
from feature_engineering import add_technical_indicators, analyze_sentiment
from model import calculate_signal
from screener import get_super_intelligence
import asyncio

app = FastAPI(title="Indian Stock Quant API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Indian Stock Quant API is running"}

@app.get("/analyze/{ticker}")
async def analyze_stock(ticker: str):
    ticker = ticker.upper()
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker += ".NS" # Default to NSE
    
    try:
        # 1. Fetch Data
        df = fetch_stock_data(ticker)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        
        news = fetch_market_news(keywords=['NSE Stock Market India', ticker, 'Global Economy', 'Geopolitics'])
        
        # 2. Process
        df_tech = add_technical_indicators(df)
        if df_tech.empty:
            raise HTTPException(status_code=400, detail="Not enough data for technical analysis")
            
        sentiment_score = analyze_sentiment(news)
        
        # 3. Calculate Signal
        prob, signal, triggers = calculate_signal(df_tech, sentiment_score)
        
        return {
            "ticker": ticker,
            "signal": signal,
            "triggers": triggers,
            "probability": round(prob, 4),
            "sentiment": round(sentiment_score, 4),
            "latest_price": round(float(df['Close'].iloc[-1]), 2),
            "timestamp": pd.Timestamp.now().isoformat(),
            "method": "AI Hybrid"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def dashboard_stats(refresh: bool = False):
    """Returns comprehensive dashboard intelligence."""
    try:
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, get_super_intelligence, refresh)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
