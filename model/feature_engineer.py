"""
Feature Engineer
================
Merges daily mood dimensions with DJIA price data to create the feature matrix
for the XGBoost model.

Adapts to available data -- uses shorter lags when history is limited.
Reads: data/daily_mood.csv + data/djia_prices.csv
Outputs: data/features.csv
"""

import sys
import logging

import pandas as pd
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

# Mood dimension column names
MOOD_COLS = ["calm", "fear", "optimism", "anxiety", "happy"]

# Price feature column names (from price_fetcher)
PRICE_COLS = ["daily_return", "volatility_5d", "ma_5", "ma_20"]


def engineer_features() -> pd.DataFrame:
    """
    Merge mood + price data and create the full feature matrix.

    Adapts feature depth to available data:
    - With 10+ overlapping days: full lags (t-1, t-2, t-3), rolling-3, momentum
    - With 3-9 days: short lags (t-1 only), no rolling, momentum
    - With < 3 days: minimal features (raw mood + price only)

    Target: next_day_direction (shifted by -1)

    Returns
    -------
    pd.DataFrame with all features and target, saved to data/features.csv
    """
    # -- Load data ---------------------------------------------------------
    if not config.DAILY_MOOD_CSV.exists():
        logger.error(f"Missing {config.DAILY_MOOD_CSV}")
        return pd.DataFrame()
    if not config.DJIA_PRICES_CSV.exists():
        logger.error(f"Missing {config.DJIA_PRICES_CSV}")
        return pd.DataFrame()

    mood = pd.read_csv(config.DAILY_MOOD_CSV)
    prices = pd.read_csv(config.DJIA_PRICES_CSV)

    mood["date"] = pd.to_datetime(mood["date"]).dt.strftime("%Y-%m-%d")
    prices["date"] = pd.to_datetime(prices["date"]).dt.strftime("%Y-%m-%d")

    logger.info(f"Mood data: {len(mood)} days | Price data: {len(prices)} days")

    # -- Merge on date -----------------------------------------------------
    df = pd.merge(mood, prices, on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"Merged dataset: {len(df)} overlapping days")

    if len(df) < 2:
        logger.error("Not enough overlapping data (need >= 2 days)")
        return pd.DataFrame()

    # -- Adaptive feature engineering --------------------------------------
    n = len(df)

    if n >= 10:
        # Full features: lags 1-3, rolling 3-day, momentum
        logger.info("Using full feature set (lags 1-3, rolling, momentum)")
        for col in MOOD_COLS:
            for lag in [1, 2, 3]:
                df[f"{col}_lag{lag}"] = df[col].shift(lag)
            df[f"{col}_roll3"] = df[col].rolling(3).mean()
            df[f"{col}_mom"] = df[col] - df[col].shift(1)

    elif n >= 4:
        # Medium features: lag 1 only, momentum
        logger.info("Using medium feature set (lag-1, momentum)")
        for col in MOOD_COLS:
            df[f"{col}_lag1"] = df[col].shift(1)
            df[f"{col}_mom"] = df[col] - df[col].shift(1)

    else:
        # Minimal: raw mood + price features only, no lags
        logger.info("Using minimal feature set (raw mood + price only)")

    # -- Target: next day's direction --------------------------------------
    df["next_day_direction"] = df["direction"].shift(-1)

    # -- Clean up ----------------------------------------------------------
    df.dropna(inplace=True)

    if df.empty:
        logger.error("No rows left after dropping NaN. Need more data.")
        return pd.DataFrame()

    df["next_day_direction"] = df["next_day_direction"].astype(int)
    df.reset_index(drop=True, inplace=True)

    # -- Save --------------------------------------------------------------
    df.to_csv(config.FEATURES_CSV, index=False)

    feature_cols = [c for c in df.columns if c not in
                    {"date", "next_day_direction", "direction",
                     "open", "high", "low", "close", "volume"}]
    logger.info(f"Feature matrix: {df.shape[0]} rows x {len(feature_cols)} features")
    logger.info(f"Features: {feature_cols}")
    logger.info(f"Saved to {config.FEATURES_CSV}")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    engineer_features()
