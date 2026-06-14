"""
MoodSignal Configuration
========================
Central configuration. Reddit requires PRAW API keys (optional).
StockTwits uses the public API (no keys needed).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Data file paths
RAW_POSTS_CSV = DATA_DIR / "raw_posts.csv"
SCORED_POSTS_CSV = DATA_DIR / "scored_posts.csv"
DAILY_MOOD_CSV = DATA_DIR / "daily_mood.csv"
DJIA_PRICES_CSV = DATA_DIR / "djia_prices.csv"
FEATURES_CSV = DATA_DIR / "features.csv"
MODEL_PATH = MODEL_DIR / "xgb_model.json"

# -- Reddit (PRAW) -- optional, set in .env --------------------------------
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MoodSignal/1.0")

# Subreddits to scrape
SUBREDDITS = ["wallstreetbets", "stocks", "investing"]

# -- StockTwits (public API, no auth) --------------------------------------
STOCKTWITS_BASE_URL = "https://api.stocktwits.com/api/2"
STOCKTWITS_SYMBOLS = [
    "DJI", "SPY", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA",
    "META", "JPM", "BAC", "GS", "V", "BA", "DIS",
]

# ── Market Data ──────────────────────────────────────────────────────────────
DJIA_TICKER = "^DJI"
LOOKBACK_DAYS = 90  # Days of historical price data

# ── Sentiment ────────────────────────────────────────────────────────────────
FINBERT_MODEL = "ProsusAI/finbert"
FINBERT_WEIGHT = 0.6
VADER_WEIGHT = 0.4

# ── Model ────────────────────────────────────────────────────────────────────
TRAIN_TEST_SPLIT = 0.8
XGB_PARAMS = {
    "max_depth": 4,
    "n_estimators": 100,
    "learning_rate": 0.1,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "random_state": 42,
}

# ── Mood Dimensions ─────────────────────────────────────────────────────────
# Keywords that boost specific mood scores
FEAR_KEYWORDS = [
    "crash", "dump", "sell", "bear", "recession", "panic", "collapse",
    "plunge", "tank", "fear", "warning", "crisis", "bubble", "risk",
]
HAPPY_KEYWORDS = [
    "moon", "rocket", "bull", "rally", "gain", "profit", "surge",
    "boom", "breakout", "diamond", "buy", "long", "calls", "tendies",
]
