"""
TradeIntel Pro - ML Engine (EDA-Driven Model Selection)
Trains only the models recommended by EDA, then reports full metrics.

Metrics per model:
  - Accuracy, Precision, Recall, F1 (macro)
  - ROC-AUC
  - Confusion Matrix
  - Cross-validation mean ± std
  - Feature Importance
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    AdaBoostClassifier, ExtraTreesClassifier,
)
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)
import streamlit as st
import warnings
warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from core.eda_engine import FEATURE_COLUMNS, run_eda


# ═══════════════════════════════════════════════════════════════
# MODEL REGISTRY
# ═══════════════════════════════════════════════════════════════
def _build_model(name: str, flags: dict):
    """Instantiate a model with EDA-informed hyper-params."""
    cw = flags.get("class_weight")  # None or "balanced"

    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=300, max_depth=10, min_samples_split=10,
            class_weight=cw, random_state=42, n_jobs=-1,
        )
    if name == "Extra Trees":
        return ExtraTreesClassifier(
            n_estimators=300, max_depth=10, min_samples_split=10,
            class_weight=cw, random_state=42, n_jobs=-1,
        )
    if name == "Gradient Boosting":
        return GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.08,
            subsample=0.8, random_state=42,
        )
    if name == "AdaBoost":
        return AdaBoostClassifier(
            n_estimators=150, learning_rate=0.1,
            random_state=42, algorithm='SAMME',
        )
    if name == "XGBoost" and HAS_XGBOOST:
        scale_pos = flags.get("scale_pos_weight", 1)
        return XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.08,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=scale_pos,
            use_label_encoder=False, eval_metric='logloss',
            random_state=42, verbosity=0,
        )
    # Fallback
    return RandomForestClassifier(n_estimators=100, random_state=42)


# ═══════════════════════════════════════════════════════════════
# FEATURE PREPARATION
# ═══════════════════════════════════════════════════════════════
def _prepare(df: pd.DataFrame, flags: dict):
    """Prepare X, y with optional lag features from EDA findings."""
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    if len(available) < 5:
        return None, None, None, None

    df_w = df[available + ['Target']].dropna().copy()

    # Add lag features if price is non-stationary
    if flags.get("use_lag_features"):
        for col in ['Close', 'RSI', 'MACD']:
            if col in df_w.columns:
                df_w[f'{col}_lag1'] = df_w[col].shift(1)
                df_w[f'{col}_lag2'] = df_w[col].shift(2)
                available += [f'{col}_lag1', f'{col}_lag2']

    df_w.dropna(inplace=True)
    feature_names = [c for c in available if c in df_w.columns]
    if len(df_w) < 100:
        return None, None, None, None

    X = df_w[feature_names].values
    y = df_w['Target'].values

    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    return X_sc, y, feature_names, scaler


# ═══════════════════════════════════════════════════════════════
# TRAINING + FULL METRICS
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def run_ml_analysis(_df_hash, df_values, col_names):
    """
    Full ML pipeline:
      1. Reconstruct DataFrame
      2. Run EDA → get recommended models + flags
      3. Train each recommended model
      4. Return full metrics + EDA report
    """
    df = pd.DataFrame(df_values, columns=col_names)

    # Step 1 — EDA
    eda = run_eda(df)
    recommended = eda["recommended_models"]
    flags = eda["model_flags"]

    # Scale-pos-weight for XGBoost if imbalanced
    cb = eda.get("class_balance", {})
    if cb and not eda.get("is_balanced", True):
        n0 = cb.get(0, 1)
        n1 = cb.get(1, 1)
        flags["scale_pos_weight"] = round(n0 / max(n1, 1), 2)

    # Step 2 — Feature preparation
    X, y, feat_names, scaler = _prepare(df, flags)
    if X is None:
        return {"eda": eda, "models": {}, "error": "Not enough data/features."}

    # Step 3 — Time-series train/test split (no shuffle)
    split = int(len(X) * 0.80)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    cv = StratifiedKFold(n_splits=5, shuffle=False)

    model_results = {}
    for name in recommended:
        if name == "XGBoost" and not HAS_XGBOOST:
            continue
        try:
            model = _build_model(name, flags)

            # Cross-val
            cv_res = cross_validate(
                model, X_train, y_train, cv=cv,
                scoring=['accuracy', 'f1', 'roc_auc'],
                return_train_score=False, n_jobs=-1,
            )

            # Full train
            model.fit(X_train, y_train)
            y_pred  = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred.astype(float)

            # Latest prediction
            latest_x = X[[-1]]
            latest_proba = float(model.predict_proba(latest_x)[0][1]) if hasattr(model, 'predict_proba') else 0.5

            # Metrics
            acc  = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec  = recall_score(y_test, y_pred, zero_division=0)
            f1   = f1_score(y_test, y_pred, zero_division=0)
            try:
                auc = roc_auc_score(y_test, y_proba)
            except Exception:
                auc = 0.5
            cm = confusion_matrix(y_test, y_pred).tolist()

            # Feature importance
            feat_imp = []
            if hasattr(model, 'feature_importances_'):
                imp = model.feature_importances_
                feat_imp = sorted(zip(feat_names, imp), key=lambda x: x[1], reverse=True)[:12]
                feat_imp = [(f, round(float(v), 4)) for f, v in feat_imp]

            model_results[name] = {
                # Live prediction
                "prob_up":    round(latest_proba, 4),
                "prob_down":  round(1 - latest_proba, 4),
                "prediction": "UP" if latest_proba > 0.5 else "DOWN",
                # Test metrics
                "accuracy":   round(acc  * 100, 2),
                "precision":  round(prec * 100, 2),
                "recall":     round(rec  * 100, 2),
                "f1_score":   round(f1   * 100, 2),
                "roc_auc":    round(auc, 4),
                "confusion_matrix": cm,
                # CV metrics
                "cv_accuracy_mean": round(cv_res['test_accuracy'].mean() * 100, 2),
                "cv_accuracy_std":  round(cv_res['test_accuracy'].std()  * 100, 2),
                "cv_f1_mean":       round(cv_res['test_f1'].mean()        * 100, 2),
                "cv_auc_mean":      round(cv_res['test_roc_auc'].mean(), 4),
                # Feature importance
                "feature_importance": feat_imp,
            }

        except Exception as e:
            model_results[name] = {"error": str(e), "prob_up": 0.5, "prediction": "N/A"}

    # Ensemble consensus
    valid = {k: v for k, v in model_results.items() if "error" not in v}
    if valid:
        avg_prob = np.mean([v["prob_up"] for v in valid.values()])
        avg_acc  = np.mean([v["accuracy"] for v in valid.values()])
        best     = max(valid.items(), key=lambda x: x[1]["roc_auc"])
        model_results["_ensemble"] = {
            "avg_prob_up":   round(float(avg_prob), 4),
            "avg_accuracy":  round(float(avg_acc), 2),
            "best_model":    best[0],
            "best_roc_auc":  best[1]["roc_auc"],
            "consensus":     "UP" if avg_prob > 0.55 else ("DOWN" if avg_prob < 0.45 else "NEUTRAL"),
            "n_models":      len(valid),
        }

    return {"eda": eda, "models": model_results}


def get_ml_results(df: pd.DataFrame):
    """Public API: run the full ML pipeline on an indicator-enriched DataFrame."""
    if df.empty or 'Target' not in df.columns:
        return None
    # Build a stable hash
    df_hash = int(pd.util.hash_pandas_object(df['Close'].tail(20)).sum())
    cols = [c for c in df.columns if c != 'Date']
    df_sub = df[[c for c in cols if c in df.columns]].tail(500)
    return run_ml_analysis(df_hash, df_sub.values, list(df_sub.columns))
