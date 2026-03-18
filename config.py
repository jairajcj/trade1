"""
TradeIntel Pro - Configuration
All stock tickers, commodities, indices, and settings.
"""

# ═══════════════════════════════════════════════════════════════
# INDIAN MARKET STOCKS (NSE)
# ═══════════════════════════════════════════════════════════════
INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ITC.NS": "ITC Ltd",
    "ICICIBANK.NS": "ICICI Bank",
    "BHARTIARTL.NS": "Bharti Airtel",
    "SBIN.NS": "State Bank India",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ADANIENT.NS": "Adani Enterprises",
    "TATAMOTORS.NS": "Tata Motors",
    "TATASTEEL.NS": "Tata Steel",
    "TATAPOWER.NS": "Tata Power",
    "ZOMATO.NS": "Zomato",
    "TITAN.NS": "Titan Company",
    "BAJFINANCE.NS": "Bajaj Finance",
    "MARUTI.NS": "Maruti Suzuki",
    "SUNPHARMA.NS": "Sun Pharma",
    "HAL.NS": "Hindustan Aero",
    "BHEL.NS": "BHEL",
    "COALINDIA.NS": "Coal India",
    "BEL.NS": "Bharat Electronics",
    "TRENT.NS": "Trent Ltd",
    "JIOFIN.NS": "Jio Financial",
    "RVNL.NS": "RVNL",
    "IRFC.NS": "IRFC",
    "NHPC.NS": "NHPC",
    "ASIANPAINT.NS": "Asian Paints",
    "WIPRO.NS": "Wipro",
    "LT.NS": "Larsen & Toubro",
    "KOTAKBANK.NS": "Kotak Mahindra",
    "NESTLEIND.NS": "Nestle India",
    "POWERGRID.NS": "Power Grid",
    "NTPC.NS": "NTPC",
    "ONGC.NS": "ONGC",
    "M&M.NS": "Mahindra & Mahindra",
    "DRREDDY.NS": "Dr Reddys Labs",
    "CIPLA.NS": "Cipla",
    "TECHM.NS": "Tech Mahindra",
    "VEDL.NS": "Vedanta",
}

# ═══════════════════════════════════════════════════════════════
# US MARKET STOCKS (Robinhood Popular)
# ═══════════════════════════════════════════════════════════════
US_STOCKS = {
    "MSFT": "Microsoft",
    "AAPL": "Apple",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "HOOD": "Robinhood Markets",
    "AMD": "AMD",
    "NFLX": "Netflix",
    "DIS": "Walt Disney",
    "PYPL": "PayPal",
    "COIN": "Coinbase",
    "SOFI": "SoFi Technologies",
    "PLTR": "Palantir",
    "RIVN": "Rivian",
    "NIO": "NIO Inc",
    "BABA": "Alibaba",
    "JPM": "JPMorgan Chase",
    "BAC": "Bank of America",
    "V": "Visa",
    "MA": "Mastercard",
    "CRM": "Salesforce",
    "UBER": "Uber",
    "SQ": "Block Inc",
    "SNAP": "Snap Inc",
    "RBLX": "Roblox",
    "MARA": "Marathon Digital",
    "RIOT": "Riot Platforms",
    "GME": "GameStop",
}

# ═══════════════════════════════════════════════════════════════
# COMMODITIES
# ═══════════════════════════════════════════════════════════════
COMMODITIES = {
    # Gold
    "GC=F": "🥇 Gold (USD/COMEX)",
    "GOLDBEES.NS": "🥇 Gold India (₹ ETF)",
    "GLD": "🥇 Gold ETF (USD/SPDR)",
    "IAU": "🥇 Gold Trust (USD/iShares)",
    # Silver
    "SI=F": "🥈 Silver (USD/COMEX)",
    "SILVERBEES.NS": "🥈 Silver India (₹ ETF)",
    "SLV": "🥈 Silver ETF (USD/iShares)",
    # Energy
    "CL=F": "🛢️ Crude Oil WTI",
    "BZ=F": "🛢️ Brent Crude",
    "NG=F": "⛽ Natural Gas",
    # Metals
    "PL=F": "Platinum",
    "HG=F": "Copper",
    "PA=F": "Palladium",
    # Agri
    "ZW=F": "Wheat",
    "ZC=F": "Corn",
    "KC=F": "Coffee",
}

# ═══════════════════════════════════════════════════════════════
# INDICES (for market overview)
# ═══════════════════════════════════════════════════════════════
INDICES = {
    "^NSEI": "NIFTY 50",
    "^BSESN": "SENSEX",
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000",
    "^VIX": "VIX (Fear Index)",
}

# ═══════════════════════════════════════════════════════════════
# FOREX (Currency Pairs)
# ═══════════════════════════════════════════════════════════════
FOREX = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD",
    "USDINR=X": "USD/INR",
    "GBPINR=X": "GBP/INR",
    "EURINR=X": "EUR/INR",
    "EURGBP=X": "EUR/GBP",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY",
    "USDCNY=X": "USD/CNY",
    "USDSGD=X": "USD/SGD",
    "USDHKD=X": "USD/HKD",
    "USDTRY=X": "USD/TRY",
    "USDZAR=X": "USD/ZAR",
    "USDBRL=X": "USD/BRL",
    "BTCUSD=X": "BTC/USD",
}

# ═══════════════════════════════════════════════════════════════
# MARKET CATEGORIES
# ═══════════════════════════════════════════════════════════════
MARKETS = {
    "🇮🇳 Indian Stocks": INDIAN_STOCKS,
    "🇺🇸 US / Robinhood": US_STOCKS,
    "🪙 Commodities": COMMODITIES,
    "💱 Forex": FOREX,
}

# ═══════════════════════════════════════════════════════════════
# CURRENCY SYMBOLS (for display)
# ═══════════════════════════════════════════════════════════════
CURRENCY_SYMBOLS = {
    # Indices
    "NIFTY 50": "₹", "SENSEX": "₹",
    "S&P 500": "$", "Dow Jones": "$", "NASDAQ": "$",
    "Russell 2000": "$", "VIX (Fear Index)": "",
}

# ═══════════════════════════════════════════════════════════════
# UI SETTINGS
# ═══════════════════════════════════════════════════════════════
REFRESH_INTERVAL = 60  # seconds
MAX_WORKERS = 10

COLORS = {
    "buy": "#00C896", "sell": "#FF4757", "hold": "#FFA502",
    "neutral": "#747D8C", "bg_card": "#161B22", "bg_dark": "#0D1117",
    "accent": "#6C63FF", "accent2": "#00D2FF", "text": "#E6EDF3",
    "text_dim": "#8B949E", "green": "#00C896", "red": "#FF4757",
    "gold": "#FFD700", "silver": "#C0C0C0",
}
