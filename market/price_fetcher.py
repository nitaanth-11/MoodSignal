"""
Market Price Fetcher
====================
Downloads DJIA (Dow Jones Industrial Average) OHLCV data using yfinance.
Computes derived features: daily return, direction, volatility, moving averages.

Outputs data/djia_prices.csv
"""

import sys
import logging
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def fetch_prices(days: int = None) -> pd.DataFrame:
    """
    Download DJIA price data and compute technical features.

    Parameters
    ----------
    days : int, optional
        Number of days of history to fetch. Defaults to config.LOOKBACK_DAYS.

    Returns
    -------
    pd.DataFrame with columns:
        date, open, high, low, close, volume,
        daily_return, direction, volatility_5d, ma_5, ma_20
    """
    days = days or config.LOOKBACK_DAYS
    end = datetime.now()
    start = end - timedelta(days=days)

    logger.info(
        f"Fetching {config.DJIA_TICKER} data from {start.date()} to {end.date()}..."
    )

    ticker = yf.Ticker(config.DJIA_TICKER)
    df = ticker.history(start=start, end=end, auto_adjust=True)

    if df.empty:
        logger.error("No price data returned from yfinance")
        return pd.DataFrame()

    # Standardise column names
    df = df.reset_index()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Ensure 'date' column is clean
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    elif "datetime" in df.columns:
        df["date"] = pd.to_datetime(df["datetime"]).dt.date
        df.drop(columns=["datetime"], inplace=True)

    # Keep only OHLCV + date
    keep_cols = ["date", "open", "high", "low", "close", "volume"]
    df = df[[c for c in keep_cols if c in df.columns]]

    # ── Derived features ─────────────────────────────────────────────
    df["daily_return"] = df["close"].pct_change()
    df["direction"] = (df["daily_return"] > 0).astype(int)
    df["volatility_5d"] = df["daily_return"].rolling(5).std()
    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_20"] = df["close"].rolling(20).mean()

    # Drop rows with NaN from rolling calcs
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Convert date to string for consistent CSV handling
    df["date"] = df["date"].astype(str)

    df.to_csv(config.DJIA_PRICES_CSV, index=False)
    logger.info(f"Saved {len(df)} rows to {config.DJIA_PRICES_CSV}")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    fetch_prices()
