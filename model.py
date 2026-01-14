import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def calculate_signal(df, sentiment_score):
    """
    Calculates a hybrid signal (Rules + AI).
    """
    if df.empty or len(df) < 50:
        return 0.5, "HOLD"

    # --- PART 1: AI Prediction (Random Forest) ---
    features = ['RSI', 'MACD', 'MACD_Signal', 'SMA_20', 'SMA_50', 'Open', 'High', 'Low', 'Close', 'Volume']
    available_features = [f for f in features if f in df.columns]
    
    X = df[available_features]
    y = df['Target']
    
    # Train a quick model on available history
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.1, shuffle=False)
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X_train, y_train)
    
    latest_data = df.iloc[[-1]][available_features]
    ai_prob = float(rf.predict_proba(latest_data)[0][1])

    # --- PART 2: Rule-Based Logic ---
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    rule_score = 0
    total_rule_weight = 0

    if 'RSI' in latest:
        total_rule_weight += 2
        if latest['RSI'] < 30: rule_score += 2
        elif latest['RSI'] > 70: rule_score -= 2
        elif latest['RSI'] < 40: rule_score += 1
        elif latest['RSI'] > 60: rule_score -= 1

    if 'MACD' in latest and 'MACD_Signal' in latest:
        total_rule_weight += 2
        if latest['MACD'] > latest['MACD_Signal']: rule_score += 1
        else: rule_score -= 1

    rule_prob = 0.5 + (rule_score / (total_rule_weight * 2)) if total_rule_weight > 0 else 0.5

    # --- PART 3: Fusion ---
    # 50% AI + 30% Rules + 20% News Sentiment
    combined_prob = (ai_prob * 0.5) + (rule_prob * 0.3) + (sentiment_score * 0.2)
    combined_prob = np.clip(combined_prob, 0, 1)

    signal = "HOLD"
    if combined_prob > 0.65: signal = "BUY"
    elif combined_prob < 0.35: signal = "SELL"

    return float(combined_prob), signal

# Removed AI model functions as per request.
# The calculation is now handled by calculate_signal.
