"""
TradeIntel Pro - Signal Generator
Fuses Technical Analysis + ML Predictions + Sentiment into a final trade signal.
"""

import numpy as np


def generate_master_signal(tech_rating, ml_results, sentiment_score):
    """
    Fuse all signals into a single master signal.
    
    Args:
        tech_rating: (rating_text, score) from technical engine
        ml_results: dict from ML engine
        sentiment_score: float from news engine
    
    Returns:
        dict with signal details
    """
    # Default values
    tech_text, tech_score = tech_rating if tech_rating else ("Neutral", 0.0)
    
    # ML score (0 to 1 scale)
    ml_score = 0.5
    ml_consensus = "NEUTRAL"
    if ml_results and "_ensemble" in ml_results:
        ml_score = ml_results["_ensemble"]["avg_prob_up"]
        ml_consensus = ml_results["_ensemble"]["consensus"]
    
    # Normalize tech_score from (-1, 1) to (0, 1)
    tech_normalized = (tech_score + 1) / 2
    
    # Normalize sentiment from (-1, 1) to (0, 1)
    sentiment_normalized = (sentiment_score + 1) / 2
    
    # ═══════════════════════════════════════════════════════════
    # FUSION FORMULA
    # 40% Technical + 40% ML + 20% Sentiment
    # ═══════════════════════════════════════════════════════════
    master_score = (
        tech_normalized * 0.40 +
        ml_score * 0.40 +
        sentiment_normalized * 0.20
    )
    
    # Clamp to 0-1
    master_score = np.clip(master_score, 0, 1)
    
    # Signal classification
    if master_score > 0.70:
        signal = "STRONG BUY"
        color = "#00C896"
        confidence = "High"
    elif master_score > 0.58:
        signal = "BUY"
        color = "#00C896"
        confidence = "Moderate"
    elif master_score < 0.30:
        signal = "STRONG SELL"
        color = "#FF4757"
        confidence = "High"
    elif master_score < 0.42:
        signal = "SELL"
        color = "#FF4757"
        confidence = "Moderate"
    else:
        signal = "HOLD"
        color = "#FFA502"
        confidence = "Low"
    
    return {
        "signal": signal,
        "score": round(float(master_score), 4),
        "color": color,
        "confidence": confidence,
        "components": {
            "technical": {"text": tech_text, "score": round(tech_score, 4), "weight": "40%"},
            "ml": {"consensus": ml_consensus, "score": round(float(ml_score), 4), "weight": "40%"},
            "sentiment": {"score": round(float(sentiment_score), 4), "weight": "20%"},
        }
    }


def get_trade_plan(signal_data, current_price, atr=None):
    """
    Generate a trade plan with entry, target, and stop-loss.
    
    Args:
        signal_data: dict from generate_master_signal
        current_price: float current stock price
        atr: float Average True Range (optional, for volatility-based levels)
    """
    score = signal_data["score"]
    signal = signal_data["signal"]
    
    if atr is None or atr == 0:
        atr = current_price * 0.02  # Default 2% of price
    
    if "BUY" in signal:
        entry = round(current_price * 1.002, 2)  # Slight premium for momentum entry
        target_1 = round(current_price + (atr * 1.5), 2)
        target_2 = round(current_price + (atr * 3.0), 2)
        stop_loss = round(current_price - (atr * 1.0), 2)
        risk_reward = round((target_1 - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0
    elif "SELL" in signal:
        entry = round(current_price * 0.998, 2)
        target_1 = round(current_price - (atr * 1.5), 2)
        target_2 = round(current_price - (atr * 3.0), 2)
        stop_loss = round(current_price + (atr * 1.0), 2)
        risk_reward = round((entry - target_1) / (stop_loss - entry), 2) if stop_loss > entry else 0
    else:
        entry = round(current_price, 2)
        target_1 = round(current_price + (atr * 1.0), 2)
        target_2 = round(current_price + (atr * 2.0), 2)
        stop_loss = round(current_price - (atr * 1.0), 2)
        risk_reward = 1.0
    
    return {
        "entry": entry,
        "target_1": target_1,
        "target_2": target_2,
        "stop_loss": stop_loss,
        "risk_reward": risk_reward,
        "atr": round(float(atr), 2),
        "position_type": "Long" if "BUY" in signal else ("Short" if "SELL" in signal else "Flat"),
    }
