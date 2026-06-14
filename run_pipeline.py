"""
MoodSignal Pipeline Runner
===========================
End-to-end CLI orchestrator that runs the full data pipeline:

    collect -> analyze -> mood -> prices -> features -> train -> predict

Usage:
    python run_pipeline.py                  # Run everything
    python run_pipeline.py --collect        # Only scrape data
    python run_pipeline.py --analyze        # Only run sentiment analysis
    python run_pipeline.py --train          # Only feature engineering + training
    python run_pipeline.py --predict        # Only make a prediction
    python run_pipeline.py --no-finbert     # Skip FinBERT (faster, VADER only)
"""

import argparse
import logging
import sys
import time
import os
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

logger = logging.getLogger("moodsignal")


def step_collect(args):
    """Step 1: Scrape posts from Reddit + StockTwits."""
    print("\n" + "=" * 60)
    print("  STEP 1/6 -- COLLECTING SOCIAL MEDIA DATA")
    print("=" * 60)

    from collectors import reddit_collector, stocktwits_collector

    # Reddit
    print("\n[*] Scraping Reddit...")
    reddit_df = reddit_collector.collect(
        limit_per_sub=args.reddit_limit,
        include_comments=True,
    )
    reddit_collector.save(reddit_df, append=False)

    # StockTwits
    print("\n[*] Scraping StockTwits...")
    st_df = stocktwits_collector.collect(max_per_symbol=args.stocktwits_limit)
    stocktwits_collector.save(st_df, append=True)

    # Report
    import pandas as pd
    if config.RAW_POSTS_CSV.exists():
        total = len(pd.read_csv(config.RAW_POSTS_CSV))
        print(f"\n[OK] Total posts collected: {total}")
        print(f"     Saved to: {config.RAW_POSTS_CSV}")
    else:
        print("[!!] No posts collected.")
        sys.exit(1)


def step_analyze(args):
    """Step 2: Run sentiment analysis on collected posts."""
    print("\n" + "=" * 60)
    print("  STEP 2/6 -- SENTIMENT ANALYSIS")
    print("=" * 60)

    from sentiment.analyzer import analyze

    use_finbert = not args.no_finbert
    if use_finbert:
        print("\n[*] Running FinBERT + VADER analysis (this may take a few minutes)...")
    else:
        print("\n[*] Running VADER-only analysis...")

    df = analyze(use_finbert=use_finbert)

    if not df.empty:
        avg_score = df["sentiment_score"].mean()
        pos_pct = (df["sentiment_score"] > 0.1).mean() * 100
        neg_pct = (df["sentiment_score"] < -0.1).mean() * 100
        print(f"\n[OK] Scored {len(df)} posts")
        print(f"     Avg sentiment: {avg_score:+.3f}")
        print(f"     Positive: {pos_pct:.1f}% | Negative: {neg_pct:.1f}%")
    else:
        print("[!!] No posts to analyze. Run --collect first.")
        sys.exit(1)


def step_mood(args):
    """Step 3: Compute daily mood dimensions."""
    print("\n" + "=" * 60)
    print("  STEP 3/6 -- COMPUTING MOOD DIMENSIONS")
    print("=" * 60)

    from mood.dimensions import compute_daily_mood

    print("\n[*] Aggregating daily mood...")
    df = compute_daily_mood()

    if not df.empty:
        print(f"\n[OK] Computed mood for {len(df)} days")
        print(f"\n     Latest mood ({df.iloc[-1]['date']}):")
        for dim in ["calm", "fear", "optimism", "anxiety", "happy"]:
            val = df.iloc[-1][dim]
            bar = "#" * int(val * 25) + "." * (25 - int(val * 25))
            print(f"       {dim.capitalize():10s} [{bar}] {val:.2%}")
    else:
        print("[!!] Not enough data for mood computation. Need more posts.")
        sys.exit(1)


def step_prices(args):
    """Step 4: Fetch DJIA price data."""
    print("\n" + "=" * 60)
    print("  STEP 4/6 -- FETCHING DJIA PRICE DATA")
    print("=" * 60)

    from market.price_fetcher import fetch_prices

    print(f"\n[*] Downloading {config.DJIA_TICKER} data ({config.LOOKBACK_DAYS} days)...")
    df = fetch_prices()

    if not df.empty:
        latest = df.iloc[-1]
        print(f"\n[OK] Fetched {len(df)} trading days")
        print(f"     Latest close: ${latest['close']:,.2f}")
        print(f"     Daily return:  {latest['daily_return']:+.2%}")
    else:
        print("[!!] Could not fetch price data.")
        sys.exit(1)


def step_features(args):
    """Step 5: Feature engineering."""
    print("\n" + "=" * 60)
    print("  STEP 5/6 -- FEATURE ENGINEERING")
    print("=" * 60)

    from model.feature_engineer import engineer_features

    print("\n[*] Building feature matrix...")
    df = engineer_features()

    if not df.empty:
        feature_cols = [c for c in df.columns if c not in
                        {"date", "next_day_direction", "direction",
                         "open", "high", "low", "close", "volume"}]
        print(f"\n[OK] Feature matrix: {len(df)} rows x {len(feature_cols)} features")
        print(f"     Target balance: {df['next_day_direction'].value_counts().to_dict()}")
    else:
        print("[!!] Could not build features. Check mood + price data overlap.")
        sys.exit(1)


def step_train(args):
    """Step 6a: Train the XGBoost model."""
    print("\n" + "=" * 60)
    print("  STEP 6/6 -- TRAINING XGBOOST MODEL")
    print("=" * 60)

    from model.trainer import train

    print("\n[*] Training model...")
    meta = train()

    if meta and "accuracy" in meta:
        print(f"\n[OK] Model trained successfully!")
        print(f"     Accuracy:  {meta['accuracy']:.1%}")
        print(f"     F1 Score:  {meta['f1']:.1%}")
        print(f"     Precision: {meta['precision']:.1%}")
        print(f"     Recall:    {meta['recall']:.1%}")
        print(f"     Saved to:  {config.MODEL_PATH}")
    else:
        print("[!!] Training failed.")
        sys.exit(1)


def step_predict(args):
    """Make a prediction using the trained model."""
    print("\n" + "=" * 60)
    print("  PREDICTION")
    print("=" * 60)

    from model.predictor import predict

    result = predict()

    if "error" in result:
        print(f"\n[!!] {result['error']}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="MoodSignal -- Stock Market Prediction via Social Sentiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py                  Full pipeline (collect -> train -> predict)
  python run_pipeline.py --collect        Scrape data only
  python run_pipeline.py --predict        Predict using existing model
  python run_pipeline.py --no-finbert     Use VADER only (faster)
        """,
    )

    # Stage selectors
    parser.add_argument("--collect", action="store_true", help="Run data collection only")
    parser.add_argument("--analyze", action="store_true", help="Run sentiment analysis only")
    parser.add_argument("--mood", action="store_true", help="Compute mood dimensions only")
    parser.add_argument("--prices", action="store_true", help="Fetch price data only")
    parser.add_argument("--features", action="store_true", help="Run feature engineering only")
    parser.add_argument("--train", action="store_true", help="Train model only")
    parser.add_argument("--predict", action="store_true", help="Make prediction only")

    # Options
    parser.add_argument("--no-finbert", action="store_true",
                        help="Skip FinBERT, use VADER only (much faster)")
    parser.add_argument("--reddit-limit", type=int, default=50,
                        help="Posts per subreddit (default: 50)")
    parser.add_argument("--stocktwits-limit", type=int, default=30,
                        help="Messages per symbol (default: 30)")

    args = parser.parse_args()

    # If no specific stage is selected, run everything
    run_all = not any([
        args.collect, args.analyze, args.mood, args.prices,
        args.features, args.train, args.predict,
    ])

    print()
    print("+----------------------------------------------------------+")
    print("|          M O O D S I G N A L   P I P E L I N E           |")
    print("|     Stock Market Prediction via Social Sentiment          |")
    print("+----------------------------------------------------------+")

    start = time.time()

    if run_all or args.collect:
        step_collect(args)
    if run_all or args.analyze:
        step_analyze(args)
    if run_all or args.mood:
        step_mood(args)
    if run_all or args.prices:
        step_prices(args)
    if run_all or args.features:
        step_features(args)
    if run_all or args.train:
        step_train(args)
    if run_all or args.predict:
        step_predict(args)

    elapsed = time.time() - start
    print(f"\n[*] Pipeline completed in {elapsed:.1f}s")
    print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    main()
