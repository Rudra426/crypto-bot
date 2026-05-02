# strategy/ml_model.py — Random Forest signal predictor (optional, enhances rule-based)

import os
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'rf_model.pkl')

FEATURES = ['rsi','macd','macd_hist','ema_fast','ema_slow','bb_upper','bb_lower','volume','vol_ma']

def _prepare_features(df):
    return df[FEATURES].dropna()

def train_model(df, lookahead=3, profit_threshold=0.01):
    """
    Train Random Forest on historical data.
    Labels: 1=BUY if price rises > threshold in `lookahead` candles, 0=SELL/HOLD
    """
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    X = _prepare_features(df).copy()
    close = df['close'].reindex(X.index)

    future_return = close.shift(-lookahead) / close - 1
    y = (future_return > profit_threshold).astype(int)

    # Align
    mask = ~y.isna()
    X, y = X[mask], y[mask]

    model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"[ML] Model trained on {len(X)} samples. Saved to {MODEL_PATH}")
    return model

def predict_signal(df):
    """Returns 'BUY' or 'HOLD' based on ML model prediction."""
    import joblib
    if not os.path.exists(MODEL_PATH):
        return 'HOLD'  # no model yet

    try:
        model = joblib.load(MODEL_PATH)
        X = _prepare_features(df).iloc[[-1]]
        pred = model.predict(X)[0]
        prob = model.predict_proba(X)[0][pred]
        return 'BUY' if pred == 1 else 'HOLD', round(prob, 4)
    except Exception as e:
        print(f"[ML] Prediction failed: {e}")
        return 'HOLD', 0.5
