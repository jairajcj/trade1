"""
TradeIntel Pro - EDA Engine
Runs Exploratory Data Analysis on stock price data.
Results are used to intelligently SELECT the best ML models.

Checks performed:
  1. Class balance (Target 0/1 ratio)
  2. Feature correlation heatmap
  3. ADF Stationarity test on Close price
  4. Autocorrelation (Ljung-Box)
  5. Return distribution (skew, kurtosis, normality)
  6. Volatility regime (rolling std)
  7. Feature importance ranking via mutual information

Model selection rules derived from EDA:
  - High autocorrelation  -> favour Gradient Boosting (handles sequential patterns)
  - Non-stationary data   -> add lag features, favour tree-based models
  - Class imbalance >60%  -> enable class_weight balanced
  - High kurtosis (fat tails) -> favour Extra Trees (robust to outliers)
  - Low feature count     -> fallback to simpler models
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

try:
    from statsmodels.tsa.stattools import adfuller, acf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


FEATURE_COLUMNS = [
    'RSI', 'Stoch_K', 'Stoch_D', 'MACD', 'MACD_Signal', 'MACD_Hist',
    'ADX', 'ADX_Pos', 'ADX_Neg', 'CCI', 'Williams_R', 'MFI',
    'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
    'BB_Upper', 'BB_Lower', 'ATR', 'OBV',
    'Open', 'High', 'Low', 'Close', 'Volume',
]


# ═══════════════════════════════════════════════════════════════
# MAIN EDA FUNCTION
# ═══════════════════════════════════════════════════════════════
def run_eda(df: pd.DataFrame) -> dict:
    """
    Full EDA pipeline. Returns a dict with findings + model recommendations.
    """
    result = {
        "n_samples": len(df),
        "n_features": 0,
        "class_balance": {},
        "is_balanced": True,
        "is_stationary": True,
        "has_autocorrelation": False,
        "return_stats": {},
        "volatility_regime": "normal",
        "top_features": [],
        "feature_corr": {},
        "recommended_models": [],
        "model_flags": {},
        "warnings": [],
    }

    if df.empty or len(df) < 60:
        result["warnings"].append("Too few samples (<60) for reliable EDA.")
        result["recommended_models"] = ["Random Forest", "Extra Trees"]
        return result

    available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    result["n_features"] = len(available_features)

    df_clean = df[available_features + ['Target']].dropna() if 'Target' in df.columns else df[available_features].dropna()

    # ── 1. Class Balance ──────────────────────────────────────
    if 'Target' in df_clean.columns:
        counts = df_clean['Target'].value_counts()
        total  = len(df_clean)
        balance = {int(k): int(v) for k, v in counts.items()}
        result["class_balance"] = balance
        majority_ratio = max(counts) / total
        result["is_balanced"] = majority_ratio < 0.60
        if not result["is_balanced"]:
            result["warnings"].append(
                f"Class imbalance detected: {majority_ratio*100:.1f}% majority class. "
                "Using class_weight='balanced'."
            )

    # ── 2. Return Distribution ────────────────────────────────
    if 'Close' in df_clean.columns:
        returns = df_clean['Close'].pct_change().dropna()
        if len(returns) > 10:
            skewness  = float(returns.skew())
            kurt      = float(returns.kurtosis())
            _, p_norm = stats.shapiro(returns.tail(100))  # limit to 100 for speed
            result["return_stats"] = {
                "mean_return_pct": round(float(returns.mean() * 100), 4),
                "std_pct":  round(float(returns.std() * 100), 4),
                "skewness": round(skewness, 4),
                "kurtosis": round(kurt, 4),
                "is_normal": bool(p_norm > 0.05),
                "shapiro_p": round(float(p_norm), 4),
            }
            if abs(kurt) > 3:
                result["warnings"].append(
                    f"Fat-tailed returns (kurtosis={kurt:.2f}). Extra Trees handles outliers better."
                )
            if abs(skewness) > 1:
                result["warnings"].append(
                    f"Skewed returns (skew={skewness:.2f}). Gradient Boosting may overfit tails."
                )

        # Volatility regime
        roll_std = returns.rolling(20).std().dropna()
        if len(roll_std) > 5:
            recent_vol = float(roll_std.tail(10).mean())
            full_vol   = float(roll_std.mean())
            if recent_vol > full_vol * 1.5:
                result["volatility_regime"] = "high"
                result["warnings"].append("High volatility regime detected. Reduce position size.")
            elif recent_vol < full_vol * 0.6:
                result["volatility_regime"] = "low"
            else:
                result["volatility_regime"] = "normal"

    # ── 3. Stationarity (ADF Test) ────────────────────────────
    if HAS_STATSMODELS and 'Close' in df_clean.columns and len(df_clean) > 30:
        try:
            adf_result  = adfuller(df_clean['Close'].dropna(), autolag='AIC')
            result["adf_stat"]    = round(float(adf_result[0]), 4)
            result["adf_p"]       = round(float(adf_result[1]), 4)
            result["is_stationary"] = bool(adf_result[1] < 0.05)
            if not result["is_stationary"]:
                result["warnings"].append(
                    f"Price series is non-stationary (ADF p={adf_result[1]:.3f}). "
                    "Tree models are preferred (no stationarity assumption)."
                )
        except Exception:
            pass

    # ── 4. Autocorrelation (Ljung-Box) ────────────────────────
    if HAS_STATSMODELS and 'Close' in df_clean.columns and len(df_clean) > 30:
        try:
            returns_for_lb = df_clean['Close'].pct_change().dropna().tail(200)
            lb_result = acorr_ljungbox(returns_for_lb, lags=[10], return_df=True)
            lb_p = float(lb_result['lb_pvalue'].values[0])
            result["has_autocorrelation"] = bool(lb_p < 0.05)
            result["ljungbox_p"] = round(lb_p, 4)
            if result["has_autocorrelation"]:
                result["warnings"].append(
                    f"Significant autocorrelation detected (Ljung-Box p={lb_p:.3f}). "
                    "Gradient Boosting captures sequential patterns."
                )
        except Exception:
            pass

    # ── 5. Feature Mutual Information ────────────────────────
    if 'Target' in df_clean.columns and len(available_features) >= 3:
        try:
            X = df_clean[available_features].fillna(0).values
            y = df_clean['Target'].values
            mi = mutual_info_classif(X, y, random_state=42)
            feat_mi = sorted(zip(available_features, mi), key=lambda x: x[1], reverse=True)
            result["top_features"] = [(f, round(float(s), 4)) for f, s in feat_mi[:10]]

            # Feature correlation (top features vs each other)
            top_names = [f for f, _ in feat_mi[:8]]
            corr_matrix = df_clean[top_names].corr()
            result["feature_corr"] = corr_matrix.round(3).to_dict()

            # High-redundancy warning
            high_corr_pairs = []
            for i, c1 in enumerate(top_names):
                for c2 in top_names[i+1:]:
                    val = abs(corr_matrix.loc[c1, c2])
                    if val > 0.90:
                        high_corr_pairs.append((c1, c2, round(float(val), 2)))
            if high_corr_pairs:
                result["warnings"].append(
                    f"{len(high_corr_pairs)} highly correlated feature pairs (>0.90). "
                    "Random Forest handles multicollinearity naturally."
                )
        except Exception:
            pass

    # ── 6. MODEL SELECTION LOGIC ─────────────────────────────
    result["recommended_models"], result["model_flags"] = _select_models(result)

    return result


def _select_models(eda: dict) -> tuple:
    """
    Rule-based model selection from EDA findings.
    Returns (ordered list of model names, flags dict).
    """
    scores = {
        "Random Forest":       5,
        "Extra Trees":         4,
        "Gradient Boosting":   3,
        "AdaBoost":            2,
        "XGBoost":             3,
    }
    flags = {
        "class_weight": "balanced" if not eda.get("is_balanced", True) else None,
        "use_lag_features": not eda.get("is_stationary", True),
    }

    # Autocorrelation → GB & XGB handle sequential data better → boost them
    if eda.get("has_autocorrelation"):
        scores["Gradient Boosting"] += 3
        scores["XGBoost"]           += 3

    # Non-stationary → tree ensembles > AdaBoost
    if not eda.get("is_stationary", True):
        scores["Random Forest"]    += 2
        scores["Extra Trees"]      += 2
        scores["AdaBoost"]         -= 1

    # Fat tails (high kurtosis) → Extra Trees (robust to outliers)
    kurt = abs(eda.get("return_stats", {}).get("kurtosis", 0))
    if kurt > 3:
        scores["Extra Trees"]  += 2
        scores["Random Forest"] += 1

    # High volatility → prefer ensemble diversification
    if eda.get("volatility_regime") == "high":
        scores["Random Forest"]    += 1
        scores["Gradient Boosting"] += 1

    # Class imbalance → penalise AdaBoost (sensitive to it)
    if not eda.get("is_balanced", True):
        scores["AdaBoost"] -= 2

    # Low feature count (<5) → simpler models
    if eda.get("n_features", 10) < 5:
        scores["Extra Trees"]      -= 2
        scores["Gradient Boosting"] -= 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # Keep top 4 (or all if XGBoost not available)
    recommended = [name for name, _ in ranked[:4]]
    flags["model_scores"] = {k: v for k, v in ranked}

    return recommended, flags
