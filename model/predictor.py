"""
Predictor
=========
Loads the trained XGBoost model and makes next-day direction predictions
using the latest available features.

Usage:
    python -m model.predictor
"""

import sys
import json
import logging

import pandas as pd
import numpy as np
import xgboost as xgb

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

# Columns to exclude from features (same as trainer)
EXCLUDE_COLS = {"date", "next_day_direction", "direction", "open", "high", "low", "close", "volume"}


def predict() -> dict:
    """
    Predict next-day DJIA direction using the latest feature row.

    Returns
    -------
    dict with keys:
        signal    — 'BULLISH' or 'BEARISH'
        confidence — float 0-1
        direction  — 1 (up) or 0 (down)
        date       — date of the feature row used
        mood       — dict of today's mood dimensions
    """
    if not config.MODEL_PATH.exists():
        logger.error(f"No trained model found at {config.MODEL_PATH}")
        return {"error": "Model not found. Run training first."}

    if not config.FEATURES_CSV.exists():
        logger.error(f"No features found at {config.FEATURES_CSV}")
        return {"error": "Features not found. Run feature engineering first."}

    # Load model
    model = xgb.XGBClassifier()
    model.load_model(str(config.MODEL_PATH))

    # Load latest features
    df = pd.read_csv(config.FEATURES_CSV)
    latest = df.iloc[-1:]

    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
    X = latest[feature_cols].astype(float)

    # Predict
    pred = model.predict(X)[0]
    prob = model.predict_proba(X)[0]

    confidence = float(max(prob))
    direction = int(pred)
    signal = "BULLISH" if direction == 1 else "BEARISH"

    # Get today's mood
    mood = {}
    for dim in ["calm", "fear", "optimism", "anxiety", "happy"]:
        if dim in latest.columns:
            mood[dim] = round(float(latest[dim].iloc[0]), 4)

    result = {
        "signal": signal,
        "confidence": round(confidence, 4),
        "direction": direction,
        "date": str(latest["date"].iloc[0]),
        "mood": mood,
    }

    # Pretty print
    arrow = ">>>" if signal == "BULLISH" else "vvv"
    logger.info("=" * 55)
    logger.info("  M O O D S I G N A L  --  PREDICTION")
    logger.info("=" * 55)
    logger.info(f"  Date:       {result['date']}")
    logger.info(f"  Signal:     {arrow}  {signal}")
    logger.info(f"  Confidence: {confidence:.1%}")
    logger.info(f"")
    logger.info(f"  Mood Dimensions:")
    for dim, val in mood.items():
        bar = "#" * int(val * 20) + "." * (20 - int(val * 20))
        logger.info(f"    {dim.capitalize():10s} [{bar}] {val:.2%}")
    logger.info("=" * 55)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    predict()
